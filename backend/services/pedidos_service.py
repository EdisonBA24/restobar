from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from services.ventas_service import crear_venta
from config import Config
from database.db_objects import (
    PEDIDOS,
    DETALLE_PEDIDOS,
    PRODUCTOS,
    USUARIOS,
    DETALLE_PEDIDO_COMPONENTES,
    CLIENTES_DIRECCIONES,

    # Fotografías históricas de pedidos
    DETALLE_PEDIDO_CATALOGO_SNAPSHOT,
    DETALLE_PEDIDO_COMPONENTES_SNAPSHOT,

    # Catálogo comercial
    CATALOGO_ITEMS,
    CATALOGO_LINEAS,
    CATALOGO_PRECIOS,

    # Configuración de menús
    MENU_CONFIGURACIONES,
    MENU_CATEGORIAS,
    MENU_CATEGORIA_PRODUCTOS
)
import math


# =============================
# 🔧 VALIDAR DECIMAL
# =============================
def to_decimal(value, field):
    try:
        if value is None or str(value).strip() == "":
            raise Exception(f"{field} vacío")

        return Decimal(str(value))

    except (InvalidOperation, Exception):
        raise Exception(f"{field} inválido: {value}")



# =====================================================
# SNAPSHOTS Y VALIDACIONES DEL CATALOGO
# =====================================================

LINEAS_POR_TIPO_CONSTRUCTOR = {
    "ALMUERZO": "ALMUERZOS",
    "ADICION": "ALMUERZOS",
    "MENU_EJECUTIVO": "ALMUERZOS",
    "MENU_PREMIUM": "ALMUERZOS",
    "MENU_ESPECIAL": "ALMUERZOS",
    "DESAYUNO": "DESAYUNOS",
    "COMIDA_RAPIDA": "COMIDAS_RAPIDAS",
    "LICOR": "LICORERA",
    "MENU": "ALMUERZOS",
    "COMBO": "COMIDAS_RAPIDAS"
}


NOMBRES_POR_TIPO_CONSTRUCTOR = {
    "ALMUERZO": "Menú del Día",
    "ADICION": "Adición",
    "MENU_EJECUTIVO": "Menú del Día",
    "MENU_PREMIUM": "Especiales",
    "MENU_ESPECIAL": "Cazuela",
    "DESAYUNO": "Desayuno",
    "COMIDA_RAPIDA": "Comida Rápida",
    "LICOR": "Licor",
    "MENU": "Menú",
    "COMBO": "Combo"
}


def _tipo_servicio_snapshot(tipo_servicio):

    tipo = str(
        tipo_servicio or "GENERAL"
    ).strip().upper()

    permitidos = {
        "GENERAL",
        "MESA",
        "LLEVAR",
        "DOMICILIO"
    }

    return tipo if tipo in permitidos else "GENERAL"


def _decimal_snapshot(value):

    return Decimal(
        str(value if value is not None else 0)
    )


def _insertar_snapshot_cabecera(
    cursor,
    detalle_pedido_id,
    snapshot,
    cantidad,
    precio,
    observaciones,
    placeholder
):

    cantidad = _decimal_snapshot(cantidad)
    precio = _decimal_snapshot(precio)

    precio_base = _decimal_snapshot(
        snapshot.get("precio_base", precio)
    )

    precio_adicional = _decimal_snapshot(
        snapshot.get("precio_adicional_unitario", 0)
    )

    subtotal = (
        cantidad * precio
    ).quantize(Decimal("0.01"))

    cursor.execute(
        f"""
        INSERT INTO {DETALLE_PEDIDO_CATALOGO_SNAPSHOT}
        (
            detalle_pedido_id,
            catalogo_item_id,
            linea_codigo,
            item_codigo,
            nombre_item,
            tipo_item_catalogo,
            tipo_servicio,
            precio_base,
            precio_adicional_unitario,
            precio_unitario_final,
            cantidad,
            subtotal_linea,
            observaciones
        )
        VALUES
        (
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder}
        )
        """,
        (
            detalle_pedido_id,
            snapshot.get("catalogo_item_id"),
            snapshot["linea_codigo"],
            snapshot.get("item_codigo"),
            snapshot["nombre_item"],
            snapshot["tipo_item_catalogo"],
            snapshot["tipo_servicio"],
            precio_base,
            precio_adicional,
            precio,
            cantidad,
            subtotal,
            observaciones
        )
    )


def _insertar_snapshot_componente(
    cursor,
    detalle_pedido_id,
    componente,
    placeholder
):

    cursor.execute(
        f"""
        INSERT INTO {DETALLE_PEDIDO_COMPONENTES_SNAPSHOT}
        (
            detalle_pedido_id,
            menu_categoria_id,
            categoria_codigo,
            categoria_nombre,
            producto_id,
            producto_nombre,
            cantidad,
            precio_adicional_unitario,
            subtotal_adicional,
            predeterminado,
            orden_categoria,
            orden_producto
        )
        VALUES
        (
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder},
            {placeholder}
        )
        """,
        (
            detalle_pedido_id,
            componente.get("menu_categoria_id"),
            componente.get("categoria_codigo"),
            componente["categoria_nombre"],
            componente["producto_id"],
            componente["producto_nombre"],
            componente.get("cantidad", 1),
            componente.get("precio_adicional_unitario", 0),
            componente.get("subtotal_adicional", 0),
            bool(componente.get("predeterminado", False)),
            componente.get("orden_categoria", 0),
            componente.get("orden_producto", 0)
        )
    )


def _resolver_precio_catalogo(
    cursor,
    catalogo_item_id,
    tipo_servicio,
    placeholder,
    is_postgres
):

    true_sql = "TRUE" if is_postgres else "1"

    cursor.execute(
        f"""
        SELECT
            tipo_servicio,
            precio

        FROM {CATALOGO_PRECIOS}

        WHERE catalogo_item_id = {placeholder}

          AND activo = {true_sql}

          AND tipo_servicio IN (
                {placeholder},
                'GENERAL'
          )

        ORDER BY CASE
            WHEN tipo_servicio = {placeholder} THEN 0
            ELSE 1
        END
        """,
        (
            catalogo_item_id,
            tipo_servicio,
            tipo_servicio
        )
    )

    row = cursor.fetchone()

    if not row:

        raise ValueError(
            "El artículo comercial no tiene un precio activo "
            f"para la modalidad {tipo_servicio} ni un precio GENERAL."
        )

    return _decimal_snapshot(row[1])


def _preparar_detalle_catalogo(
    cursor,
    item,
    tipo_servicio,
    placeholder,
    is_postgres
):
    """
    Valida artículos comerciales y resuelve sus precios
    directamente desde la base de datos.

    Cuando el detalle no proviene del catálogo, no modifica
    su precio ni su estructura actual.
    """

    catalogo_item_id = item.get("catalogo_item_id")

    if not catalogo_item_id:
        return

    try:

        catalogo_item_id = int(catalogo_item_id)

    except (TypeError, ValueError):

        raise ValueError(
            "El identificador del artículo comercial no es válido."
        )

    true_sql = "TRUE" if is_postgres else "1"

    cursor.execute(
        f"""
        SELECT
            ci.id,
            cl.codigo,
            ci.codigo,
            ci.tipo_item,
            ci.nombre,
            ci.producto_id,
            ci.activo,
            cl.activo,
            mc.activo

        FROM {CATALOGO_ITEMS} ci

        INNER JOIN {CATALOGO_LINEAS} cl
            ON cl.id = ci.linea_id

        LEFT JOIN {MENU_CONFIGURACIONES} mc
            ON mc.catalogo_item_id = ci.id

        WHERE ci.id = {placeholder}
        """,
        (catalogo_item_id,)
    )

    row = cursor.fetchone()

    if not row:

        raise ValueError(
            "El artículo comercial seleccionado no existe."
        )

    if not bool(row[6]) or not bool(row[7]):

        raise ValueError(
            "El artículo comercial o su línea están inactivos."
        )

    tipo_catalogo = str(
        row[3] or ""
    ).strip().upper()

    tipo_servicio = _tipo_servicio_snapshot(
        tipo_servicio
    )

    precio_base = _resolver_precio_catalogo(
        cursor,
        catalogo_item_id,
        tipo_servicio,
        placeholder,
        is_postgres
    )

    snapshot = {
        "catalogo_item_id": catalogo_item_id,
        "linea_codigo": row[1],
        "item_codigo": row[2],
        "nombre_item": row[4],
        "tipo_item_catalogo": tipo_catalogo,
        "tipo_servicio": tipo_servicio,
        "precio_base": precio_base,
        "precio_adicional_unitario": Decimal("0")
    }

    # -------------------------------------------------
    # PRODUCTO NORMAL
    # -------------------------------------------------

    if tipo_catalogo == "PRODUCTO":

        producto_catalogo_id = row[5]

        producto_enviado = item.get("producto_id")

        if producto_enviado is not None:

            if int(producto_enviado) != int(producto_catalogo_id):

                raise ValueError(
                    "El producto enviado no coincide con el "
                    "producto vinculado al artículo comercial."
                )

        producto_id = producto_catalogo_id

        cursor.execute(
            f"""
            SELECT id

            FROM {PRODUCTOS}

            WHERE id = {placeholder}

              AND activo = 1
            """,
            (producto_id,)
        )

        if not cursor.fetchone():

            raise ValueError(
                "El producto vinculado está inactivo o no existe."
            )

        item["producto_id"] = producto_id
        item["tipo_item"] = "PRODUCTO"
        item["nombre"] = row[4]
        item["precio"] = precio_base
        item["_catalogo_snapshot"] = snapshot

        return

    # -------------------------------------------------
    # MENU O COMBO
    # -------------------------------------------------

    if tipo_catalogo not in {"MENU", "COMBO"}:

        raise ValueError(
            f"Tipo de artículo comercial no soportado: {tipo_catalogo}"
        )

    if row[8] is not None and not bool(row[8]):

        raise ValueError(
            "La configuración del menú está inactiva."
        )

    componentes = item.get("componentes") or []

    cursor.execute(
        f"""
        SELECT
            id,
            codigo,
            nombre,
            obligatorio,
            min_selecciones,
            max_selecciones,
            permitir_repetidos,
            orden

        FROM {MENU_CATEGORIAS}

        WHERE menu_item_id = {placeholder}

          AND activo = {true_sql}

        ORDER BY orden, id
        """,
        (catalogo_item_id,)
    )

    categorias_rows = cursor.fetchall()

    if not categorias_rows:

        raise ValueError(
            "El menú no tiene categorías activas configuradas."
        )

    categorias = {}

    for categoria in categorias_rows:

        categorias[categoria[0]] = {
            "id": categoria[0],
            "codigo": categoria[1],
            "nombre": categoria[2],
            "obligatorio": bool(categoria[3]),
            "min": int(categoria[4] or 0),
            "max": int(categoria[5] or 0),
            "permitir_repetidos": bool(categoria[6]),
            "orden": int(categoria[7] or 0),
            "cantidad": 0,
            "productos": set()
        }

    componentes_snapshot = []
    adicional_total = Decimal("0")

    for indice, componente in enumerate(componentes, start=1):

        menu_categoria_id = componente.get(
            "menu_categoria_id"
        )

        producto_id = componente.get(
            "producto_id",
            componente.get("id")
        )

        if not menu_categoria_id or not producto_id:

            raise ValueError(
                "Cada componente del menú debe incluir "
                "menu_categoria_id y producto_id."
            )

        try:

            menu_categoria_id = int(menu_categoria_id)
            producto_id = int(producto_id)

        except (TypeError, ValueError):

            raise ValueError(
                "Los identificadores de los componentes no son válidos."
            )

        categoria = categorias.get(menu_categoria_id)

        if not categoria:

            raise ValueError(
                "Una de las categorías seleccionadas no pertenece "
                "al menú o está inactiva."
            )

        cursor.execute(
            f"""
            SELECT
                p.id,
                p.nombre,
                mcp.precio_adicional,
                mcp.predeterminado,
                mcp.orden

            FROM {MENU_CATEGORIA_PRODUCTOS} mcp

            INNER JOIN {PRODUCTOS} p
                ON p.id = mcp.producto_id

            WHERE mcp.menu_categoria_id = {placeholder}

              AND mcp.producto_id = {placeholder}

              AND mcp.activo = {true_sql}

              AND p.activo = 1
            """,
            (
                menu_categoria_id,
                producto_id
            )
        )

        producto = cursor.fetchone()

        if not producto:

            raise ValueError(
                "Uno de los productos seleccionados no está "
                "asociado activamente a su categoría."
            )

        cantidad_componente = _decimal_snapshot(
            componente.get("cantidad", 1)
        )

        if cantidad_componente <= 0:

            raise ValueError(
                "La cantidad de un componente debe ser mayor que cero."
            )

        precio_adicional = _decimal_snapshot(
            producto[2]
        )

        subtotal_adicional = (
            precio_adicional * cantidad_componente
        ).quantize(Decimal("0.01"))

        adicional_total += subtotal_adicional

        categoria["cantidad"] += int(cantidad_componente)

        if cantidad_componente != cantidad_componente.to_integral_value():

            raise ValueError(
            "La cantidad de selecciones de un componente debe ser un número entero."
        )

        if (
            not categoria["permitir_repetidos"]
            and (
                producto_id in categoria["productos"]
                or cantidad_componente > 1
            )
        ):

            raise ValueError(
                f"No se permite repetir productos en "
                f"la categoría {categoria['nombre']}."
            )

        categoria["productos"].add(producto_id)

        componentes_snapshot.append({

            "menu_categoria_id": menu_categoria_id,

            "categoria_codigo": categoria["codigo"],

            "categoria_nombre": categoria["nombre"],

            "producto_id": producto[0],

            "producto_nombre": producto[1],

            "cantidad": cantidad_componente,

            "precio_adicional_unitario": precio_adicional,

            "subtotal_adicional": subtotal_adicional,

            "predeterminado": bool(producto[3]),

            "orden_categoria": categoria["orden"],

            "orden_producto": int(producto[4] or indice)

        })

        # Normalizar el identificador que se guardará
        # en la tabla actual de componentes.
        componente["producto_id"] = producto_id

    # -------------------------------------------------
    # VALIDAR REGLAS DE TODAS LAS CATEGORÍAS
    # -------------------------------------------------

    for categoria in categorias.values():

        cantidad = categoria["cantidad"]

        # =============================================
        # VALIDAR MINIMO SOLO SI ES OBLIGATORIA
        # =============================================

        if categoria["obligatorio"]:

            minimo = max(
                1,
                categoria["min"]
            )

            if cantidad < minimo:

                raise ValueError(
                    f"La categoría {categoria['nombre']} requiere "
                    f"mínimo {minimo} selección(es)."
                )

        # =============================================
        # EL MAXIMO SIEMPRE SE RESPETA
        # =============================================

        maximo = categoria["max"]

        if maximo > 0 and cantidad > maximo:

            raise ValueError(
                f"La categoría {categoria['nombre']} permite "
                f"máximo {maximo} selección(es)."
            )

    precio_final = (
        precio_base + adicional_total
    ).quantize(Decimal("0.01"))

    snapshot["precio_adicional_unitario"] = adicional_total

    item["tipo_item"] = tipo_catalogo
    item["nombre"] = row[4]
    item["precio"] = precio_final
    item["_catalogo_snapshot"] = snapshot
    item["_componentes_snapshot"] = componentes_snapshot


# =====================================================
# DIRECCION DE ENTREGA
# =====================================================

def _consultar_direccion_entrega(
    cursor,
    cliente_id,
    placeholder,
    direccion_id=None
):

    if not cliente_id:
        return None

    parametros = [cliente_id]

    condicion_direccion = ""

    if direccion_id not in (None, "", 0, "0"):

        condicion_direccion = f"AND id = {placeholder}"

        parametros.append(direccion_id)

    cursor.execute(
        f"""
        SELECT
            nombre,
            direccion,
            barrio,
            referencia

        FROM {CLIENTES_DIRECCIONES}

        WHERE cliente_id = {placeholder}

          AND activo = 1

          {condicion_direccion}

        ORDER BY
            principal DESC,
            id ASC
        """,
        tuple(parametros)
    )

    fila = cursor.fetchone()

    if not fila:
        return None

    nombre, direccion, barrio, referencia = fila

    direccion = str(direccion or "").strip()

    if not direccion:
        return None

    partes = []

    if nombre:
        partes.append(
            f"{str(nombre).strip()}: {direccion}"
        )
    else:
        partes.append(direccion)

    if barrio:
        partes.append(
            f"Barrio: {str(barrio).strip()}"
        )

    if referencia:
        partes.append(
            f"Referencia: {str(referencia).strip()}"
        )

    return " | ".join(partes)[:600]


# =====================================================
# RESOLVER DIRECCION PARA EL PEDIDO
#
# Si existe direccion_id, respeta la seleccion
# del usuario.
#
# Si no existe, utiliza la direccion principal
# activa del cliente.
# =====================================================

def _resolver_direccion_entrega(
    cursor,
    data,
    placeholder
):

    tipo_servicio = str(
        data.get("tipo") or ""
    ).strip().upper()

    if tipo_servicio != "DOMICILIO":
        return None

    direccion_manual = str(
        data.get("direccion_entrega") or ""
    ).strip()

    if direccion_manual:
        return direccion_manual[:600]

    cliente_id = data.get("cliente_id")

    if not cliente_id:

        raise ValueError(
            "Para registrar un pedido a domicilio debe seleccionar un cliente con dirección registrada."
        )

    direccion_id = data.get("direccion_id")

    direccion = _consultar_direccion_entrega(
        cursor=cursor,
        cliente_id=cliente_id,
        placeholder=placeholder,
        direccion_id=direccion_id
    )

    if not direccion:

        raise ValueError(
            "El cliente seleccionado no tiene una dirección de entrega activa. Registre una dirección antes de crear el pedido."
        )

    return direccion



# =============================
# 🔁 CONVERSIÓN UNIDADES
# =============================
#def convertir_cantidad(cantidad, unidad):

#    cantidad = Decimal(cantidad or 0)

#    if not unidad:
#        return cantidad

#    unidad = str(unidad).lower()

#    if unidad in ["g", "gr", "gramos"]:
#        return cantidad / Decimal(1000)

#    if unidad in ["kg", "kilogramo", "kilogramos"]:
#        return cantidad

#    return cantidad


# =============================
# 📦 VALIDAR STOCK (SOLO VALIDAR)
# =============================
#def validar_stock_pedido(data):

#    conn = get_connection()
#    cursor = conn.cursor()

#    try:
#        detalles = data.get("detalles", [])

#        if not detalles:
#            return {"ok": True}  # 🔥 evita error innecesario

#        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
#        placeholder = "%s" if is_postgres else "?"

#        for item in detalles:

#            producto_id = item["producto_id"]
#            cantidad = to_decimal(item["cantidad"], "Cantidad")

#            cursor.execute(f"""
#                SELECT rd.insumo_id, rd.cantidad, rd.unidad
#                FROM restobar.recetas r
#                JOIN restobar.recetas_detalle rd ON r.id = rd.receta_id
#                WHERE r.producto_id = {placeholder}
#            """, (producto_id,))

#            insumos = cursor.fetchall()

#            for insumo_id, cantidad_base, unidad in insumos:

#                cantidad_total = Decimal(cantidad_base or 0) * cantidad
#                cantidad_real = convertir_cantidad(cantidad_total, unidad)

#                cursor.execute(f"""
#                    SELECT stock, nombre 
#                    FROM restobar.productos 
#                    WHERE id = {placeholder}
#                """, (insumo_id,))

#                result = cursor.fetchone()

#                if not result:
#                    continue

#                stock = Decimal(result[0] or 0)
#                nombre = result[1]

#                if stock < cantidad_real:
#                    return {
#                        "ok": False,
#                        "message": f"Stock insuficiente: {nombre}"
#                    }

#        return {"ok": True}

#    finally:
#        conn.close()

# =====================================================
# CALCULAR TOTAL PEDIDO
# =====================================================

def _calcular_total_pedido(detalles):

    """
    Calcula el total del pedido.

    Todos los constructores (Almuerzo, Desayuno,
    Comidas Rápidas, Licores, etc.) utilizarán
    exactamente la misma función.
    """

    total = Decimal("0")

    for item in detalles:

        cantidad = to_decimal(

            item.get("cantidad", 0),

            "Cantidad"

        )

        precio = to_decimal(

            item.get("precio", 0),

            "Precio"

        )

        total += cantidad * precio

    return total


# =====================================================
# INSERTAR CABECERA PEDIDO
# =====================================================

def _insertar_pedido(
    cursor,
    data,
    usuario_id,
    total,
    is_postgres,
    placeholder
):

    if is_postgres:

        cursor.execute(
            f"""
            INSERT INTO {PEDIDOS}
            (
                mesa,
                tipo,
                cliente,
                cliente_id,
                estado,
                usuario_id,
                total,
                categoria,
                direccion_entrega
            )
            VALUES
            (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            RETURNING id
            """,
            (
                data.get("mesa"),
                data.get("tipo"),
                data.get("cliente"),
                data.get("cliente_id"),
                data.get("estado"),
                usuario_id,
                total,
                data.get("categoria"),
                data.get("direccion_entrega")
            )
        )

    else:

        cursor.execute(
            f"""
            INSERT INTO {PEDIDOS}
            (
                mesa,
                tipo,
                cliente,
                cliente_id,
                estado,
                usuario_id,
                total,
                categoria,
                direccion_entrega
            )
            OUTPUT INSERTED.id
            VALUES
            (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            """,
            (
                data.get("mesa"),
                data.get("tipo"),
                data.get("cliente"),
                data.get("cliente_id"),
                data.get("estado"),
                usuario_id,
                total,
                data.get("categoria"),
                data.get("direccion_entrega")
            )
        )

    fila = cursor.fetchone()

    if not fila:

        raise Exception(
            "No fue posible crear el pedido."
        )

    return fila[0]


# =====================================================
# GUARDAR DETALLE PEDIDO
# =====================================================

def _guardar_detalle(

    cursor,
    pedido_id,
    item,
    is_postgres,
    placeholder,
    tipo_servicio="GENERAL"

):

    tipo_item = str(

        item.get("tipo_item", "")

    ).upper()

    print(
        "TIPO ITEM:",
        tipo_item
    )

    #if tipo_item.startswith("MENU") or tipo_item == "ADICION":
    CONSTRUCTORES = {
        "ALMUERZO",
        "ADICION",
        "MENU_EJECUTIVO",
        "MENU_PREMIUM",
        "MENU_ESPECIAL",
        "DESAYUNO",
        "COMIDA_RAPIDA",
        "LICOR",
        "MENU",
        "COMBO"
    }

    if tipo_item in CONSTRUCTORES:

        return _guardar_constructor(

            cursor=cursor,

            pedido_id=pedido_id,

            item=item,

            is_postgres=is_postgres,

            placeholder=placeholder,

            tipo_servicio=tipo_servicio

        )

    return _guardar_producto(

        cursor=cursor,

        pedido_id=pedido_id,

        item=item,

        is_postgres=is_postgres,

        placeholder=placeholder,

        tipo_servicio=tipo_servicio

    )

# =====================================================
# GUARDAR PRODUCTO NORMAL
# =====================================================

def _guardar_producto(
    cursor,
    pedido_id,
    item,
    is_postgres,
    placeholder,
    tipo_servicio="GENERAL"
):

    producto_id = item.get("producto_id")

    if not producto_id:
        raise ValueError("El producto no tiene ID.")

    cantidad = to_decimal(
        item.get("cantidad", 0),
        "Cantidad"
    )

    precio = to_decimal(
        item.get("precio", 0),
        "Precio"
    )

    tipo_item = str(
        item.get("tipo_item", "PRODUCTO")
    ).upper()

    if is_postgres:

        cursor.execute(
            f"""
            INSERT INTO {DETALLE_PEDIDOS}
            (
                pedido_id,
                tipo_item,
                producto_id,
                cantidad,
                precio
            )
            VALUES
            (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            RETURNING id
            """,
            (
                pedido_id,
                tipo_item,
                producto_id,
                cantidad,
                precio
            )
        )

    else:

        cursor.execute(
            f"""
            INSERT INTO {DETALLE_PEDIDOS}
            (
                pedido_id,
                tipo_item,
                producto_id,
                cantidad,
                precio
            )
            OUTPUT INSERTED.id
            VALUES
            (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            """,
            (
                pedido_id,
                tipo_item,
                producto_id,
                cantidad,
                precio
            )
        )

    fila = cursor.fetchone()

    if not fila:
        raise Exception(
            "No fue posible recuperar el detalle del producto."
        )

    detalle_pedido_id = fila[0]

    snapshot = item.get("_catalogo_snapshot")

    # Solo los productos vinculados al catálogo
    # necesitan fotografía comercial en este flujo.
    if snapshot:

        _insertar_snapshot_cabecera(
            cursor=cursor,
            detalle_pedido_id=detalle_pedido_id,
            snapshot=snapshot,
            cantidad=cantidad,
            precio=precio,
            observaciones=item.get("observaciones"),
            placeholder=placeholder
        )

    return detalle_pedido_id


# =====================================================
# GUARDAR CONSTRUCTOR
# =====================================================

def _guardar_constructor(
    cursor,
    pedido_id,
    item,
    is_postgres,
    placeholder,
    tipo_servicio="GENERAL"
):

    cantidad = to_decimal(
        item.get("cantidad", 1),
        "Cantidad"
    )

    precio = to_decimal(
        item.get("precio", 0),
        "Precio"
    )

    tipo_item = str(
        item.get("tipo_item", "ALMUERZO")
    ).upper()

    # =============================================
    # INSERTAR DETALLE DEL PEDIDO
    # =============================================

    if is_postgres:

        cursor.execute(
            f"""
            INSERT INTO {DETALLE_PEDIDOS}
            (
                pedido_id,
                tipo_item,
                producto_id,
                cantidad,
                precio
            )
            VALUES
            (
                {placeholder},
                {placeholder},
                NULL,
                {placeholder},
                {placeholder}
            )
            RETURNING id
            """,
            (
                pedido_id,
                tipo_item,
                cantidad,
                precio
            )
        )

    else:

        cursor.execute(
            f"""
            INSERT INTO {DETALLE_PEDIDOS}
            (
                pedido_id,
                tipo_item,
                producto_id,
                cantidad,
                precio
            )
            OUTPUT INSERTED.id
            VALUES
            (
                {placeholder},
                {placeholder},
                NULL,
                {placeholder},
                {placeholder}
            )
            """,
            (
                pedido_id,
                tipo_item,
                cantidad,
                precio
            )
        )

    fila = cursor.fetchone()

    if not fila:
        raise Exception(
            "No fue posible crear el detalle del constructor."
        )

    detalle_pedido_id = fila[0]

    componentes = item.get("componentes") or []

    if not componentes:
        raise ValueError(
            "El constructor no tiene componentes."
        )

    # =============================================
    # PREPARAR FOTOGRAFÍA COMERCIAL
    # =============================================

    snapshot = item.get("_catalogo_snapshot")

    if not snapshot:

        nombre_item = (
            item.get("nombre")
            or NOMBRES_POR_TIPO_CONSTRUCTOR.get(
                tipo_item,
                tipo_item.replace("_", " ").title()
            )
        )

        snapshot = {

            "catalogo_item_id": None,

            "linea_codigo": (
                item.get("linea_codigo")
                or LINEAS_POR_TIPO_CONSTRUCTOR.get(
                    tipo_item,
                    "ALMUERZOS"
                )
            ),

            "item_codigo": (
                item.get("codigo")
                or tipo_item
            ),

            "nombre_item": nombre_item,

            "tipo_item_catalogo": "MENU",

            "tipo_servicio": _tipo_servicio_snapshot(
                tipo_servicio
            ),

            # En los constructores anteriores,
            # el precio recibido ya representa el
            # valor completo del artículo.
            "precio_base": precio,

            "precio_adicional_unitario": Decimal("0")

        }

    _insertar_snapshot_cabecera(
        cursor=cursor,
        detalle_pedido_id=detalle_pedido_id,
        snapshot=snapshot,
        cantidad=cantidad,
        precio=precio,
        observaciones=item.get("observaciones"),
        placeholder=placeholder
    )

    componentes_snapshot = item.get(
        "_componentes_snapshot"
    )

    # =============================================
    # INSERTAR COMPONENTES
    # =============================================

    for indice, componente in enumerate(
        componentes,
        start=1
    ):

        producto_id = componente.get(
            "producto_id",
            componente.get("id")
        )

        if not producto_id:
            raise ValueError(
                "Un componente no tiene producto_id."
            )

        cursor.execute(
            f"""
            INSERT INTO {DETALLE_PEDIDO_COMPONENTES}
            (
                detalle_pedido_id,
                producto_id
            )
            VALUES
            (
                {placeholder},
                {placeholder}
            )
            """,
            (
                detalle_pedido_id,
                producto_id
            )
        )

        # =========================================
        # SNAPSHOT DE COMPONENTES DEL CATÁLOGO
        # =========================================

        if componentes_snapshot is not None:

            if indice > len(componentes_snapshot):

                raise ValueError(
                    "La cantidad de componentes históricos "
                    "no coincide con los componentes del pedido."
                )

            snapshot_componente = (
                componentes_snapshot[indice - 1]
            )

        else:

            # Compatibilidad con el formulario anterior:
            # los nombres se consultan directamente
            # desde la tabla de productos.

            cursor.execute(
                f"""
                SELECT
                    id,
                    nombre,
                    categoria

                FROM {PRODUCTOS}

                WHERE id = {placeholder}
                """,
                (producto_id,)
            )

            producto = cursor.fetchone()

            if not producto:

                raise ValueError(
                    f"El producto {producto_id} no existe."
                )

            snapshot_componente = {

                "menu_categoria_id": None,

                "categoria_codigo": None,

                "categoria_nombre": (
                    producto[2] or "COMPONENTE"
                ),

                "producto_id": producto[0],

                "producto_nombre": producto[1],

                "cantidad": Decimal("1"),

                "precio_adicional_unitario": Decimal("0"),

                "subtotal_adicional": Decimal("0"),

                "predeterminado": False,

                "orden_categoria": indice,

                "orden_producto": indice

            }

        _insertar_snapshot_componente(
            cursor=cursor,
            detalle_pedido_id=detalle_pedido_id,
            componente=snapshot_componente,
            placeholder=placeholder
        )

    return detalle_pedido_id



# =====================================================
# CREAR PEDIDO
# =====================================================

def crear_pedido(data):

    conn = get_connection()
    cursor = conn.cursor()

    usuario_id = session.get("user_id")

    try:

        detalles = data.get("detalles", [])

        if not detalles:
            raise ValueError(
                "No hay productos en el pedido."
            )

        is_postgres = (
            getattr(Config, "DB_ENGINE", "sqlserver")
            == "postgres"
        )

        placeholder = "%s" if is_postgres else "?"

        # =============================================
        # RESOLVER DIRECCION DE ENTREGA
        # =============================================

        data["direccion_entrega"] = (
            _resolver_direccion_entrega(
                cursor=cursor,
                data=data,
                placeholder=placeholder
            )
        )

        # =============================================
        # VALIDAR Y PREPARAR ARTICULOS DEL CATALOGO
        # =============================================

        tipo_servicio = _tipo_servicio_snapshot(
            data.get("tipo")
        )

        for item in detalles:

            if not isinstance(item, dict):

                raise ValueError(
                    "El detalle del pedido tiene un formato inválido."
                )

            _preparar_detalle_catalogo(
                cursor=cursor,
                item=item,
                tipo_servicio=tipo_servicio,
                placeholder=placeholder,
                is_postgres=is_postgres
            )

        # =============================================
        # CALCULAR TOTAL
        # =============================================

        total = _calcular_total_pedido(detalles)

        # =============================================
        # INSERTAR CABECERA
        # =============================================

        pedido_id = _insertar_pedido(

            cursor=cursor,

            data=data,

            usuario_id=usuario_id,

            total=total,

            is_postgres=is_postgres,

            placeholder=placeholder

        )

        # =============================================
        # GUARDAR DETALLES
        # =============================================

        for item in detalles:

            _guardar_detalle(

                cursor=cursor,

                pedido_id=pedido_id,

                item=item,

                is_postgres=is_postgres,

                placeholder=placeholder,

                tipo_servicio=tipo_servicio

            )

        conn.commit()

        return {

            "message": "Pedido registrado correctamente",

            "total": float(total),

            "pedido_id": pedido_id,

            "direccion_entrega": data.get(
                "direccion_entrega"
            )

        }

    except Exception as e:

        conn.rollback()

        print(
            "ERROR CREAR PEDIDO:",
            e
        )

        raise

    finally:

        conn.close()



# =====================================================
# OBTENER FILTROS PEDIDOS
# =====================================================

def _obtener_parametros_pedidos(args):

    return {

        "page":
            max(
                int(
                    args.get("page")
                    or 1
                ),
                1
            ),

        "page_size":
            max(
                int(
                    args.get("page_size")
                    or 20
                ),
                10
            ),

        "sort_by":
            args.get("sort_by")
            or "id",

        "sort_order":
            (
                args.get("sort_order")
                or "desc"
            ).lower(),

        "buscar":
            (
                args.get("buscar")
                or ""
            ).strip(),

        "estado":
            (
                args.get("estado")
                or ""
            ).strip(),

        "servicio":
            (
                args.get("servicio")
                or ""
            ).strip(),

        "periodo":
            args.get("periodo")
            or "mes_actual",

        "fecha_inicio":
            args.get("fecha_inicio")
            or "",

        "fecha_fin":
            args.get("fecha_fin")
            or ""

    }


# =====================================================
# COLUMNAS ORDENAMIENTO
# =====================================================

COLUMNAS_ORDEN_PEDIDOS = {

    "id": "p.id",

    "fecha": "p.fecha",

    "cliente": "p.cliente",

    "mesa": "p.mesa",

    "estado": "p.estado",

    "total": "p.total",

    "tipo": "p.tipo",

    "usuario": "u.nombre"

}

# =====================================================
# ORDER BY
# =====================================================

def _obtener_order_by(parametros):

    columna = COLUMNAS_ORDEN_PEDIDOS.get(

        parametros["sort_by"],

        "p.id"

    )

    direccion = (

        "ASC"

        if parametros["sort_order"] == "asc"

        else "DESC"

    )

    return f"{columna} {direccion}"

# =====================================================
# PAGINACIÓN
# =====================================================

def _obtener_paginacion(parametros):

    page = parametros["page"]

    page_size = parametros["page_size"]

    offset = (page - 1) * page_size

    return {

        "page": page,

        "page_size": page_size,

        "offset": offset

    }

# =====================================================
# WHERE DINÁMICO
# =====================================================

def _construir_where(parametros, placeholder):

    where = []
    values = []

    # =====================================
    # BUSCADOR
    # =====================================

    if parametros["buscar"]:

        where.append(f"""
        (
            p.cliente LIKE {placeholder}
            OR CAST(p.id AS VARCHAR) LIKE {placeholder}
            OR u.nombre LIKE {placeholder}
        )
        """)

        texto = f"%{parametros['buscar']}%"

        values.extend([
            texto,
            texto,
            texto
        ])

    # =====================================
    # ESTADO
    # =====================================

    if parametros["estado"]:

        where.append(
            f"LOWER(p.estado) = LOWER({placeholder})"
        )

        values.append(
            parametros["estado"]
        )

    # =====================================
    # SERVICIO
    # =====================================

    if parametros["servicio"]:

        where.append(
            f"p.tipo = {placeholder}"
        )

        values.append(
            parametros["servicio"]
        )

    # =====================================
    # FECHA INICIO
    # =====================================

    if parametros["fecha_inicio"]:

        where.append(
            f"CAST(p.fecha AS DATE) >= {placeholder}"
        )

        values.append(
            parametros["fecha_inicio"]
        )

    # =====================================
    # FECHA FIN
    # =====================================

    if parametros["fecha_fin"]:

        where.append(
            f"CAST(p.fecha AS DATE) <= {placeholder}"
        )

        values.append(
            parametros["fecha_fin"]
        )

    sql = ""

    if where:

        sql = " WHERE " + " AND ".join(where)

    return sql, values


# =============================
# 📄 CONSULTAR PEDIDOS
# =============================
def get_pedidos(args):

    parametros = _obtener_parametros_pedidos(args)

    print("PARAMETROS PEDIDOS")

    print(parametros)

    conn = get_connection()
    cursor = conn.cursor()

    is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
    placeholder = "%s" if is_postgres else "?"

    try:
        #cursor.execute(f"""
        #    SELECT p.id, p.mesa, p.tipo, p.cliente, p.total, p.fecha, p.estado, u.nombre AS usuario, p.categoria
        #    FROM {PEDIDOS} p
        #    LEFT JOIN {USUARIOS} u ON p.usuario_id = u.id
        #    ORDER BY p.id DESC
        #""")

        #columns = [c[0] for c in cursor.description]

        #data = []
        #for r in cursor.fetchall():
        #    row = dict(zip(columns, r))
        #    row["total"] = float(row.get("total") or 0)
        #    data.append(row)

        # =====================================
        # PAGINACIÓN
        # =====================================

        paginacion = _obtener_paginacion(

            parametros

        )

        order_by = _obtener_order_by(

            parametros

        )

        where_sql, values = _construir_where(

            parametros, placeholder

        )

        # =====================================
        # TOTAL REGISTROS
        # =====================================

        sql_total = f"""

            SELECT

                COUNT(*)

            FROM {PEDIDOS} p

            LEFT JOIN {USUARIOS} u

            ON u.id = p.usuario_id

            {where_sql}

        """

        cursor.execute(

            sql_total,

            values

        )

        total = cursor.fetchone()[0]

        if not is_postgres:

            sql = f"""

                SELECT

                p.id,

                p.fecha,

                p.cliente,

                p.mesa,

                p.tipo,

                p.estado,

                p.total,

                u.nombre usuario

            FROM {PEDIDOS} p

            LEFT JOIN {USUARIOS} u

                ON u.id=p.usuario_id

            {where_sql}

            ORDER BY {order_by}

            OFFSET ? ROWS

            FETCH NEXT ? ROWS ONLY

            """

            cursor.execute(

                sql,

                values +

                [

                    paginacion["offset"],

                    paginacion["page_size"]

                ]

            )

        else:

            sql = f"""

                SELECT

                    p.id,

                    p.fecha,

                    p.cliente,

                    p.mesa,

                    p.tipo,

                    p.estado,

                    p.total,

                    u.nombre usuario

                FROM {PEDIDOS} p

                LEFT JOIN {USUARIOS} u

                    ON u.id=p.usuario_id

                {where_sql}

                ORDER BY {order_by}

                LIMIT %s

                OFFSET %s

                """

            cursor.execute(

                sql,

                values +

                [

                    paginacion["page_size"],

                    paginacion["offset"]

                ]

            )

        columns = [

            c[0]

            for c in cursor.description

        ]

        items = []

        for r in cursor.fetchall():

            items.append(

                dict(

                    zip(

                        columns,

                        r

                    )

                )

            )
            
        #return data
        return {

            "items": items,

            "pagination": {

                "page":

                    paginacion["page"],

                "page_size":

                    paginacion["page_size"],

                "total": total,

                "total_pages":

                    math.ceil(

                        total /

                        paginacion["page_size"]

                    )

                if total else 1

            }

        }

    finally:
        conn.close()


# =====================================================
# EXPORTAR PEDIDOS A EXCEL
# =====================================================

def exportar_pedidos(filtros=None):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if filtros is None:
            filtros = {}

        # ==========================================
        # CONFIGURACIÓN BD
        # ==========================================

        is_postgres = (
            getattr(
                Config,
                "DB_ENGINE",
                "sqlserver"
            ) == "postgres"
        )

        placeholder = (
            "%s"
            if is_postgres
            else "?"
        )

        # ==========================================
        # NORMALIZAR FILTROS
        # ==========================================

        parametros = _obtener_parametros_pedidos(
            filtros
        )

        # ==========================================
        # WHERE
        #
        # IMPORTANTE:
        # reutilizamos exactamente el mismo WHERE
        # utilizado por el historial.
        #
        # NO utilizamos paginación.
        # ==========================================

        where_sql, values = _construir_where(
            parametros,
            placeholder
        )

        # ==========================================
        # HOJA 1
        # CABECERA DE PEDIDOS
        # ==========================================

        sql_pedidos = f"""
            SELECT
                p.id,
                p.fecha,
                p.cliente,
                p.tipo,
                p.mesa,
                p.estado,
                u.nombre AS usuario,
                p.total
            FROM {PEDIDOS} p

            LEFT JOIN {USUARIOS} u
                ON u.id = p.usuario_id

            {where_sql}

            ORDER BY
                p.id DESC
        """

        cursor.execute(
            sql_pedidos,
            values
        )

        columnas = [
            c[0]
            for c in cursor.description
        ]

        pedidos = []

        for row in cursor.fetchall():

            pedido = dict(
                zip(
                    columnas,
                    row
                )
            )

            # ======================================
            # NORMALIZAR DATOS
            # ======================================

            pedido["id"] = int(
                pedido.get("id") or 0
            )

            if pedido.get("fecha"):

                pedido["fecha"] = (
                    pedido["fecha"]
                    .strftime("%Y-%m-%d %H:%M:%S")
                )

            else:

                pedido["fecha"] = ""

            pedido["cliente"] = (
                pedido.get("cliente")
                or "Consumidor final"
            )

            pedido["tipo"] = (
                pedido.get("tipo")
                or ""
            )

            pedido["mesa"] = (
                pedido.get("mesa")
                or ""
            )

            pedido["estado"] = (
                pedido.get("estado")
                or ""
            )

            pedido["usuario"] = (
                pedido.get("usuario")
                or ""
            )

            pedido["total"] = float(
                pedido.get("total")
                or 0
            )

            pedidos.append(
                pedido
            )

        # ==========================================
        # HOJA 2
        # DETALLE DE PEDIDOS
        # ==========================================

        sql_detalles = f"""
            SELECT
                p.id AS pedido_id,
                p.fecha,
                p.cliente,
                p.tipo AS servicio,
                p.mesa,
                p.estado,
                u.nombre AS usuario,

                dp.id AS detalle_id,
                dp.tipo_item,
                dp.producto_id,
                dp.cantidad,
                dp.precio,

                COALESCE(
                    NULLIF(s.nombre_item, ''),
                    NULLIF(pr.nombre, '')
                ) AS producto,

                pr.categoria AS categoria

            FROM {DETALLE_PEDIDOS} dp

            INNER JOIN {PEDIDOS} p
                ON p.id = dp.pedido_id

            LEFT JOIN {USUARIOS} u
                ON u.id = p.usuario_id

            LEFT JOIN {PRODUCTOS} pr
                ON pr.id = dp.producto_id

            LEFT JOIN {DETALLE_PEDIDO_CATALOGO_SNAPSHOT} s
                ON s.detalle_pedido_id = dp.id

            {where_sql}

            ORDER BY
                p.id DESC,
                dp.id ASC
        """

        cursor.execute(
            sql_detalles,
            values
        )

        columnas_detalle = [
            c[0]
            for c in cursor.description
        ]

        detalles_base = []

        for row in cursor.fetchall():

            detalle = dict(
                zip(
                    columnas_detalle,
                    row
                )
            )

            detalle["pedido_id"] = int(
                detalle.get("pedido_id")
                or 0
            )

            detalle["detalle_id"] = int(
                detalle.get("detalle_id")
                or 0
            )

            if detalle.get("fecha"):

                detalle["fecha"] = (
                    detalle["fecha"]
                    .strftime("%Y-%m-%d %H:%M:%S")
                )

            else:

                detalle["fecha"] = ""

            detalle["cliente"] = (
                detalle.get("cliente")
                or "Consumidor final"
            )

            detalle["servicio"] = (
                detalle.get("servicio")
                or ""
            )

            detalle["mesa"] = (
                detalle.get("mesa")
                or ""
            )

            detalle["estado"] = (
                detalle.get("estado")
                or ""
            )

            detalle["usuario"] = (
                detalle.get("usuario")
                or ""
            )

            detalle["tipo_item"] = (
                str(
                    detalle.get("tipo_item")
                    or ""
                ).upper()
            )

            detalle["cantidad"] = float(
                detalle.get("cantidad")
                or 0
            )

            detalle["precio"] = float(
                detalle.get("precio")
                or 0
            )

            detalle["producto"] = (
                detalle.get("producto")
                or ""
            )

            detalle["categoria"] = (
                detalle.get("categoria")
                or ""
            )

            detalles_base.append(
                detalle
            )

        # ==========================================
        # OBTENER COMPONENTES
        #
        # Los constructores como:
        #
        # ALMUERZO
        # ADICION
        # MENU_EJECUTIVO
        # MENU_PREMIUM
        # MENU_ESPECIAL
        #
        # tienen producto_id NULL y sus productos
        # están en DETALLE_PEDIDO_COMPONENTES.
        # ==========================================

        componentes_por_detalle = {}

        for detalle in detalles_base:

            if detalle.get("producto_id") is None:

                componentes = (
                    obtener_componentes_detalle(
                        cursor,
                        detalle["detalle_id"],
                        placeholder
                    )
                )

                componentes_por_detalle[
                    detalle["detalle_id"]
                ] = componentes

            else:

                componentes_por_detalle[
                    detalle["detalle_id"]
                ] = []

        # ==========================================
        # TRANSFORMAR DETALLE PARA EXCEL
        # ==========================================

        detalles = []

        for detalle in detalles_base:

            tipo_item = (
                detalle.get("tipo_item")
                or ""
            )

            # ======================================
            # NOMBRE AMIGABLE DEL TIPO
            # ======================================

            nombres_tipo = {

                "ALMUERZO":
                    "Almuerzo",

                "ADICION":
                    "Adición",

                "MENU_EJECUTIVO":
                    #"Menú Ejecutivo",
                    "Menú del Día",

                "MENU_PREMIUM":
                    #"Menú Premium",
                    "Especiales",

                "MENU_ESPECIAL":
                    #"Menú Especial",
                    "Cazuela",

                "MENU": "Menú",

                "COMBO": "Combo",

                "DESAYUNO":
                    "Desayuno",

                "COMIDA_RAPIDA":
                    "Comida Rápida",

                "LICOR":
                    #"Licor"
                    "Licor/Bebidas"

            }

            tipo_nombre = nombres_tipo.get(
                tipo_item,
                tipo_item.replace(
                    "_",
                    " "
                ).title()
            )

            # ======================================
            # COMPONENTES
            # ======================================

            componentes = (
                componentes_por_detalle.get(
                    detalle["detalle_id"],
                    []
                )
            )

            nombres_componentes = []

            for componente in componentes:

                nombre = (
                    componente.get("nombre")
                    or ""
                )

                if nombre:

                    nombres_componentes.append(
                        nombre
                    )

            componentes_texto = (
                " | ".join(
                    nombres_componentes
                )
                if nombres_componentes
                else ""
            )

            # ======================================
            # SUBTOTAL
            # ======================================

            subtotal = (
                detalle["cantidad"]
                *
                detalle["precio"]
            )

            # ======================================
            # REGISTRO FINAL
            # ======================================

            detalles.append({

                "pedido_id":
                    detalle["pedido_id"],

                "fecha":
                    detalle["fecha"],

                "cliente":
                    detalle["cliente"],

                "servicio":
                    detalle["servicio"],

                "mesa":
                    detalle["mesa"],

                "estado":
                    detalle["estado"],

                "usuario":
                    detalle["usuario"],

                "tipo_item":
                    tipo_nombre,

                "producto":
                    detalle["producto"]
                    if detalle["producto"]
                    else tipo_nombre,

                "cantidad":
                    detalle["cantidad"],

                "precio":
                    detalle["precio"],

                "subtotal":
                    subtotal,

                "componentes":
                    componentes_texto

            })

        # ==========================================
        # RESULTADO
        # ==========================================

        return {

            "pedidos":
                pedidos,

            "detalles":
                detalles

        }

    except Exception as e:

        print(
            "❌ ERROR EXPORTAR PEDIDOS:",
            e
        )

        return {

            "pedidos": [],

            "detalles": []

        }

    finally:

        conn.close()


# =====================================================
# KPIs PEDIDOS
# =====================================================

def get_pedidos_kpis(args):

    parametros = _obtener_parametros_pedidos(args)

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        where_sql, values = _construir_where(
            parametros,
            placeholder
        )

        total_sql = (
            "COALESCE(SUM(p.total),0)"
            if is_postgres
            else
            "ISNULL(SUM(p.total),0)"
        )

        sql = f"""
            SELECT

                COUNT(*) total_pedidos,

                SUM(
                    CASE
                        WHEN LOWER(p.estado)='pendiente'
                        THEN 1
                        ELSE 0
                    END
                ) pendientes,

                SUM(
                    CASE
                        WHEN LOWER(p.estado)='facturado'
                        THEN 1
                        ELSE 0
                    END
                ) facturados,

                {total_sql} valor_total

            FROM {PEDIDOS} p

            LEFT JOIN {USUARIOS} u
                ON u.id = p.usuario_id

            {where_sql}
        """

        cursor.execute(sql, values)

        row = cursor.fetchone()

        total_pedidos = row[0] or 0
        pendientes = row[1] or 0
        facturados = row[2] or 0
        valor_total = float(row[3] or 0)

        ticket_promedio = (
            valor_total / total_pedidos
            if total_pedidos
            else 0
        )

        return {

            "total_pedidos": total_pedidos,

            "pendientes": pendientes,

            "facturados": facturados,

            # frontend
            "ventas_dia": valor_total,

            "ticket_promedio": ticket_promedio

        }

    finally:
        conn.close()

# =====================================================
# TRANSFORMACIÓN DETALLE
# =====================================================

def transformar_detalle_pedido(detalle):

    resultado = []

    CONSTRUCTORES = {

        "ALMUERZO",
        "ADICION",
        "MENU_EJECUTIVO",
        "MENU_PREMIUM",
        "MENU_ESPECIAL",
        "DESAYUNO",
        "COMIDA_RAPIDA",
        "LICOR",
        "MENU",
        "COMBO"

    }

    for item in detalle:

        tipo = str(
            item.get("tipo_item") or ""
        ).upper()

        if tipo in CONSTRUCTORES:

            resultado.append(

                transformar_constructor(item)

            )

        else:

            resultado.append(

                transformar_producto(item)

            )

    return resultado

# =====================================================
# MODELO BASE
# =====================================================

def crear_item_detalle():

    """
    Modelo estándar utilizado por todo el ERP.

    Todas las transformaciones deben devolver esta
    estructura para mantener el frontend desacoplado.
    """

    return {

        "id": None,

        "tipo": "",

        "nombre": "",

        "cantidad": 0,

        "precio": 0,

        "subtotal": 0,

        "componentes": [],

        "observaciones": "",

        "metadata": {}

    }

# ==========================================================
# OBTENER DETALLES DEL PEDIDO
# ==========================================================

def obtener_detalles_pedido(
    cursor,
    pedido_id,
    placeholder
):

    cursor.execute(
        f"""
        SELECT
            dp.id AS detalle_id,
            dp.pedido_id,
            dp.producto_id,
            dp.tipo_item,
            dp.cantidad,
            dp.precio,

            p.nombre AS producto_nombre,
            p.categoria AS categoria,

            s.nombre_item AS snapshot_nombre_item,
            s.catalogo_item_id,
            s.linea_codigo,
            s.item_codigo,
            s.tipo_item_catalogo,
            s.tipo_servicio AS tipo_servicio_snapshot,
            s.precio_base,
            s.precio_adicional_unitario,
            s.precio_unitario_final,
            s.observaciones AS snapshot_observaciones

        FROM {DETALLE_PEDIDOS} dp

        LEFT JOIN {PRODUCTOS} p
            ON p.id = dp.producto_id

        LEFT JOIN {DETALLE_PEDIDO_CATALOGO_SNAPSHOT} s
            ON s.detalle_pedido_id = dp.id

        WHERE dp.pedido_id = {placeholder}

        ORDER BY dp.id
        """,
        (pedido_id,)
    )

    columns = [
        column[0]
        for column in cursor.description
    ]

    data = []

    for row in cursor.fetchall():

        item = dict(zip(columns, row))

        item["cantidad"] = float(
            item.get("cantidad") or 0
        )

        item["precio"] = float(
            item.get("precio") or 0
        )

        item["observaciones"] = (
            item.get("snapshot_observaciones") or ""
        )

        data.append(item)

    return data

# ==========================================================
# OBTENER COMPONENTES DEL DETALLE
# ==========================================================

def obtener_componentes_detalle(
    cursor,
    detalle_id,
    placeholder
):

    # =============================================
    # PRIMERO: SNAPSHOT HISTORICO
    # =============================================

    cursor.execute(
        f"""
        SELECT
            producto_id AS id,
            producto_nombre AS nombre,
            categoria_nombre AS categoria,
            menu_categoria_id,
            categoria_codigo,
            precio_adicional_unitario,
            subtotal_adicional,
            predeterminado,
            orden_categoria,
            orden_producto

        FROM {DETALLE_PEDIDO_COMPONENTES_SNAPSHOT}

        WHERE detalle_pedido_id = {placeholder}

        ORDER BY
            orden_categoria,
            orden_producto,
            id
        """,
        (detalle_id,)
    )

    columns = [
        column[0]
        for column in cursor.description
    ]

    componentes = [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

    if componentes:
        return componentes

    # =============================================
    # SEGUNDO: COMPATIBILIDAD HISTORICA
    # =============================================

    cursor.execute(
        f"""
        SELECT
            p.id,
            p.nombre,
            p.categoria

        FROM {DETALLE_PEDIDO_COMPONENTES} dpc

        INNER JOIN {PRODUCTOS} p
            ON p.id = dpc.producto_id

        WHERE dpc.detalle_pedido_id = {placeholder}

        ORDER BY
            p.categoria,
            p.nombre
        """,
        (detalle_id,)
    )

    columns = [
        column[0]
        for column in cursor.description
    ]

    return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]

# ==========================================================
# ENRIQUECER DETALLES DEL PEDIDO
# ==========================================================

def enriquecer_detalles_pedido(

    cursor,
    detalle,
    placeholder

):

    for item in detalle:

        if item.get("producto_id") is None:

            item["componentes"] = obtener_componentes_detalle(

                cursor,

                item["detalle_id"],

                placeholder

            )

        else:

            item["componentes"] = []

    return detalle

#def transformar_almuerzo(item):

#    detalle = crear_item_detalle()

#    detalle["id"] = item.get("id")

#    detalle["tipo"] = "ALMUERZO"

#    detalle["nombre"] = item.get("nombre")

#    detalle["cantidad"] = item.get("cantidad")

#    detalle["precio"] = float(item.get("precio") or 0)

#    detalle["subtotal"] = round(

#        detalle["cantidad"] *

#        detalle["precio"],

#        2

#    )

#    detalle["observaciones"] = item.get(

#        "observaciones",

#        ""

#    )

#    detalle["componentes"] = []

#    return detalle

# =====================================================
# TRANSFORMAR CONSTRUCTOR
# =====================================================

# =====================================================
# TRANSFORMAR CONSTRUCTOR
# =====================================================

def transformar_constructor(item):

    detalle = crear_item_detalle()

    detalle["id"] = item.get(
        "detalle_id"
    )

    tipo_item = str(
        item.get(
            "tipo_item",
            ""
        )
        or ""
    ).upper()

    detalle["tipo"] = tipo_item

    # =====================================================
    # NOMBRES COMERCIALES
    # =====================================================

    nombres_constructores = {

        "ALMUERZO":
            "Menú del Día",

        "MENU_EJECUTIVO":
            "Menú del Día",

        "MENU_PREMIUM":
            "Especiales",

        "MENU_ESPECIAL":
            "Cazuela",

        "ADICION":
            "Adición",

        "DESAYUNO":
            "Desayuno",

        "COMIDA_RAPIDA":
            "Comida Rápida",

        "LICOR":
            "Licor"

    }

    detalle["nombre"] = (
        item.get("snapshot_nombre_item")

        or item.get("nombre_item")

        or nombres_constructores.get(
            tipo_item
        )

        or tipo_item.replace(
            "_",
            " "
        ).title()
    )

    # =====================================================
    # CANTIDAD
    # =====================================================

    detalle["cantidad"] = float(
        item.get(
            "cantidad"
        )
        or 0
    )

    # =====================================================
    # PRECIO
    # =====================================================

    detalle["precio"] = float(
        item.get(
            "precio"
        )
        or 0
    )

    # =====================================================
    # SUBTOTAL
    # =====================================================

    detalle["subtotal"] = round(

        detalle["cantidad"]
        *
        detalle["precio"],

        2

    )

    # =====================================================
    # OBSERVACIONES
    # =====================================================

    detalle["observaciones"] = (
        item.get(
            "observaciones",
            ""
        )
        or ""
    )

    # =====================================================
    # COMPONENTES
    # =====================================================

    detalle["componentes"] = []

    for componente in item.get("componentes", []):

        detalle["componentes"].append({

            "producto_id": (
                componente.get("id")
                or componente.get("producto_id")
            ),

            "categoria": (
                componente.get("categoria")
                or componente.get("categoria_nombre")
            ),

            "nombre": (
                componente.get("nombre")
                or componente.get("producto_nombre")
            ),

            "menu_categoria_id": componente.get(
                "menu_categoria_id"
            ),

            "precio_adicional_unitario": float(
                componente.get("precio_adicional_unitario") or 0
            )

        })

    # =====================================================
    # METADATA
    # =====================================================

    detalle["metadata"] = {

        "constructor": True,

        "tipo_item": tipo_item,

        "catalogo_item_id": item.get(
            "catalogo_item_id"
        ),

        "linea_codigo": item.get(
            "linea_codigo"
        ),

        "item_codigo": item.get(
            "item_codigo"
        ),

        "tipo_servicio": item.get(
            "tipo_servicio_snapshot"
        ),

        "precio_base": float(
            item.get("precio_base") or 0
        ),

        "precio_adicional_unitario": float(
            item.get("precio_adicional_unitario") or 0
        ),

        "precio_unitario_final": float(
            item.get("precio_unitario_final") or 0
        )

    }

    print(
        "CONSTRUCTOR TRANSFORMADO"
    )

    print(
        detalle
    )

    return detalle

# =====================================================
# COMPONENTES
# =====================================================

def agregar_componente(

    detalle,

    categoria,

    nombre

):

    detalle["componentes"].append({

        "categoria": categoria,

        "nombre": nombre

    })


# =====================================================
# PRODUCTO NORMAL
# =====================================================
def transformar_producto(item):

    detalle = crear_item_detalle()

    detalle["id"] = (
        item.get("detalle_id")
        or item.get("id")
    )

    detalle["tipo"] = "PRODUCTO"

    detalle["nombre"] = (
        item.get("snapshot_nombre_item")
        or item.get("producto_nombre")
        or item.get("nombre")
    )

    detalle["cantidad"] = item.get("cantidad")

    detalle["precio"] = float(item.get("precio") or 0)

    detalle["subtotal"] = round(

        detalle["cantidad"] *

        detalle["precio"],

        2

    )

    detalle["observaciones"] = (
        item.get("snapshot_observaciones") or ""
    )

    return detalle


# =====================================================
# AGRUPAR DETALLE PEDIDO
# =====================================================

def agrupar_detalle_pedido(rows):

    detalle = []

    #almuerzos = {}
    constructores = {}

    CONSTRUCTORES = {

        "ALMUERZO",
        "ADICION",
        "MENU_EJECUTIVO",
        "MENU_PREMIUM",
        "MENU_ESPECIAL",
        "DESAYUNO",
        "COMIDA_RAPIDA",
        "LICOR",
        "MENU",
        "COMBO"

    }

    for row in rows:

        tipo = (row.get("tipo_item") or "").upper()

        # =====================================
        # ALMUERZO
        # =====================================

        #if tipo == "ALMUERZO":
        if tipo in CONSTRUCTORES:

            detalle_id = row["detalle_id"]

            #if detalle_id not in almuerzos:
            if detalle_id not in constructores:

                #almuerzos[detalle_id] = {
                #constructores[detalle_id] = {

                #    "detalle_id": detalle_id,

                    #"tipo_item": "ALMUERZO",
                #    "tipo_item": tipo,

                #    "cantidad": float(row.get("cantidad") or 0),

                #    "precio": float(row.get("precio") or 0),

                #    "componentes": []

                #}
                constructores[detalle_id] = {

                    "detalle_id": detalle_id,

                    "tipo_item": tipo,

                    "nombre": None,

                    "cantidad": float(row.get("cantidad") or 0),

                    "precio": float(row.get("precio") or 0),

                    "subtotal": round(

                        float(row.get("cantidad") or 0)

                        *

                        float(row.get("precio") or 0),

                        2

                    ),

                    "observaciones": row.get(

                        "observaciones",

                        ""

                    ),

                    "componentes": []

                }

                detalle.append(

                    #almuerzos[detalle_id]
                    constructores[detalle_id]

                )

            if row.get("componente_nombre"):

                #almuerzos[detalle_id]["componentes"].append({
                constructores[detalle_id]["componentes"].append({

                    "producto_id":

                        row.get("componente_id"),

                    "categoria":

                        row.get("categoria"),

                    "nombre":

                        row.get("componente_nombre")

                })

        # =====================================
        # PRODUCTOS
        # =====================================

        else:

            detalle.append({

                "detalle_id":

                    row["detalle_id"],

                "tipo_item":

                    tipo,

                "producto_id":

                    row.get("producto_id"),

                "nombre":

                    row.get("producto_nombre"),

                "cantidad":

                    float(row.get("cantidad") or 0),

                "precio":

                    float(row.get("precio") or 0)

            })

    # =====================================
    # ASIGNAR NOMBRE DEL CONSTRUCTOR
    # =====================================

    for constructor in constructores.values():

        tipo = (

            constructor["tipo_item"]

            .replace("_", " ")

            .title()

        )

        constructor["nombre"] = tipo

    return detalle



# =====================================================
# DETALLE PEDIDO
# =====================================================

def get_pedido_detalle(pedido_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres = (
            getattr(Config, "DB_ENGINE", "sqlserver")
            == "postgres"
        )

        placeholder = "%s" if is_postgres else "?"

        # =============================================
        # CABECERA DEL PEDIDO
        # =============================================

        cursor.execute(
            f"""
            SELECT
                id,
                mesa,
                tipo,
                cliente,
                categoria,
                estado,
                fecha,
                cliente_id,
                direccion_entrega

            FROM {PEDIDOS}

            WHERE id = {placeholder}
            """,
            (pedido_id,)
        )

        pedido_row = cursor.fetchone()

        if not pedido_row:
            return None

        direccion_entrega = pedido_row[8]

        tipo_servicio = str(
            pedido_row[2] or ""
        ).strip().upper()

        # =============================================
        # RECUPERAR DIRECCION PARA PEDIDOS HISTORICOS
        #
        # Si el pedido se creó antes de implementar
        # direccion_entrega, se consulta la principal.
        # =============================================

        if (
            tipo_servicio == "DOMICILIO"
            and not direccion_entrega
        ):

            direccion_entrega = (
                _consultar_direccion_entrega(
                    cursor=cursor,
                    cliente_id=pedido_row[7],
                    placeholder=placeholder
                )
            )

        pedido = {

            "id": pedido_row[0],

            "mesa": pedido_row[1],

            "tipo": pedido_row[2],

            "cliente": pedido_row[3],

            "categoria": pedido_row[4],

            "estado": pedido_row[5],

            "fecha": (
                str(pedido_row[6])
                if pedido_row[6]
                else ""
            ),

            "cliente_id": pedido_row[7],

            "direccion_entrega": direccion_entrega

        }

        # =============================================
        # OBTENER DETALLES
        # =============================================

        detalle = obtener_detalles_pedido(
            cursor,
            pedido_id,
            placeholder
        )

        # =============================================
        # ENRIQUECER DETALLES
        # =============================================

        detalle = enriquecer_detalles_pedido(
            cursor,
            detalle,
            placeholder
        )

        # =============================================
        # TRANSFORMAR PARA FRONTEND
        # =============================================

        detalle = transformar_detalle_pedido(
            detalle
        )

        return {

            "pedido": pedido,

            "detalle": detalle

        }

    finally:

        conn.close()




# =====================================================
# FACTURAR PEDIDO → VENTA
# CONSERVAR DIRECCION DE ENTREGA
# =====================================================

def facturar_pedido(
    pedido_id,
    metodo_pago="Efectivo",
    usuario_id=None,
    *args,
    **kwargs
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        usuario_id = (
            usuario_id
            or session.get("user_id")
            or 1
        )

        is_postgres = (
            getattr(Config, "DB_ENGINE", "sqlserver")
            == "postgres"
        )

        placeholder = "%s" if is_postgres else "?"

        # =============================================
        # CONSULTAR PEDIDO
        # =============================================

        cursor.execute(
            f"""
            SELECT
                id,
                estado,
                mesa,
                cliente,
                cliente_id,
                categoria,
                tipo,
                direccion_entrega

            FROM {PEDIDOS}

            WHERE id = {placeholder}
            """,
            (pedido_id,)
        )

        pedido = cursor.fetchone()

        if not pedido:
            raise Exception("Pedido no existe.")

        if str(pedido[1]).strip().lower() == "facturado":
            raise Exception("El pedido ya fue facturado.")

        # =============================================
        # RECUPERAR DIRECCION SI ES UN DOMICILIO
        # =============================================

        tipo_servicio = str(
            pedido[6] or ""
        ).strip().upper()

        direccion_entrega = pedido[7]

        if (
            tipo_servicio == "DOMICILIO"
            and not direccion_entrega
        ):

            direccion_entrega = (
                _consultar_direccion_entrega(
                    cursor=cursor,
                    cliente_id=pedido[4],
                    placeholder=placeholder
                )
            )

            # Actualizar la fotografía de dirección
            # para conservarla en el historial.

            if direccion_entrega:

                cursor.execute(
                    f"""
                    UPDATE {PEDIDOS}

                    SET direccion_entrega = {placeholder}

                    WHERE id = {placeholder}
                    """,
                    (
                        direccion_entrega,
                        pedido_id
                    )
                )

        # =============================================
        # CONSULTAR PRODUCTOS DEL PEDIDO
        # =============================================

        cursor.execute(
            f"""
            SELECT
                dp.producto_id,
                dp.tipo_item,
                dp.cantidad,
                dp.precio,
                s.nombre_item

            FROM {DETALLE_PEDIDOS} dp

            LEFT JOIN {DETALLE_PEDIDO_CATALOGO_SNAPSHOT} s
                ON s.detalle_pedido_id = dp.id

            WHERE dp.pedido_id = {placeholder}

            ORDER BY dp.id
            """,
            (pedido_id,)
        )

        detalles_db = cursor.fetchall()

        if not detalles_db:
            raise Exception("Pedido sin productos.")

        # =============================================
        # CONSTRUIR VENTA
        # =============================================

        data_venta = {

            "cliente": (
                pedido[3]
                or f"Mesa {pedido[2]}"
            ),

            "cliente_id": pedido[4],

            "mesa": pedido[2],

            "categoria": pedido[5],

            "tipo_servicio": tipo_servicio,

            "direccion_entrega": direccion_entrega,

            "metodo_pago": metodo_pago,

            "usuario": (
                session.get("nombreUsuario")
                or f"user_{usuario_id}"
            ),

            "usuario_id": usuario_id,

            "detalles": []

        }

        # =============================================
        # CONSTRUIR DETALLE DE VENTA
        # =============================================

        for (
            producto_id,
            tipo_item,
            cantidad,
            precio,
            nombre_item
        ) in detalles_db:

            tipo_item = str(
                tipo_item or "PRODUCTO"
            ).upper()

            data_venta["detalles"].append({

                "producto_id": producto_id,

                "tipo_item": tipo_item,

                "cantidad": float(cantidad or 0),

                "precio": float(precio or 0),

                "nombre_item": nombre_item

            })

        # =============================================
        # REGISTRAR VENTA
        # =============================================

        resultado = crear_venta(
            data_venta
        )

        # =============================================
        # ACTUALIZAR ESTADO PEDIDO
        # =============================================

        cursor.execute(
            f"""
            UPDATE {PEDIDOS}

            SET estado = 'facturado'

            WHERE id = {placeholder}
            """,
            (pedido_id,)
        )

        conn.commit()

        return {

            "message": "Pedido facturado correctamente",

            "venta": resultado

        }

    except Exception as e:

        conn.rollback()

        print(
            "ERROR FACTURAR PEDIDO:",
            e
        )

        raise

    finally:

        conn.close()
