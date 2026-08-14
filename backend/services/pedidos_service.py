from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from services.ventas_service import crear_venta
from config import Config
from database.db_objects import PEDIDOS, DETALLE_PEDIDOS, PRODUCTOS, USUARIOS, DETALLE_PEDIDO_COMPONENTES
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

        cursor.execute(f"""
            INSERT INTO {PEDIDOS}
            (
                mesa,
                tipo,
                cliente,
                cliente_id,
                estado,
                usuario_id,
                total,
                categoria
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
                {placeholder}
            )
            RETURNING id
        """, (

            data.get("mesa"),

            data.get("tipo"),

            data.get("cliente"),

            data.get("cliente_id"),

            data.get("estado"),

            usuario_id,

            total,

            data.get("categoria")

        ))

    else:

        cursor.execute(f"""
            INSERT INTO {PEDIDOS}
            (
                mesa,
                tipo,
                cliente,
                cliente_id,
                estado,
                usuario_id,
                total,
                categoria
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
                {placeholder}
            )
        """, (

            data.get("mesa"),

            data.get("tipo"),

            data.get("cliente"),

            data.get("cliente_id"),

            data.get("estado"),

            usuario_id,

            total,

            data.get("categoria")

        ))

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
    placeholder

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
        "LICOR"

    }

    if tipo_item in CONSTRUCTORES:

        return _guardar_constructor(

            cursor=cursor,

            pedido_id=pedido_id,

            item=item,

            is_postgres=is_postgres,

            placeholder=placeholder

        )

    return _guardar_producto(

        cursor=cursor,

        pedido_id=pedido_id,

        item=item,

        is_postgres=is_postgres,

        placeholder=placeholder

    )

# =====================================================
# GUARDAR PRODUCTO NORMAL
# =====================================================

def _guardar_producto(

    cursor,
    pedido_id,
    item,
    is_postgres,
    placeholder

):

    producto_id = item.get("producto_id")

    if not producto_id:

        raise Exception(

            "El producto no tiene ID."

        )

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
        """,

        (

            pedido_id,

            tipo_item,

            producto_id,

            cantidad,

            precio

        )

    )

    return True


# =====================================================
# GUARDAR CONSTRUCTOR
# =====================================================

def _guardar_constructor(

    cursor,
    pedido_id,
    item,
    is_postgres,
    placeholder

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

    print(
        "CONSTRUCTOR:",
        tipo_item
    )

    # ============================================
    # INSERT DETALLE
    # ============================================

    if is_postgres:

        cursor.execute(f"""
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
        """, (

            pedido_id,

            tipo_item,

            cantidad,

            precio

        ))

    else:

        cursor.execute(f"""
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
        """, (

            pedido_id,

            tipo_item,

            cantidad,

            precio

        ))

    fila = cursor.fetchone()

    if not fila:

        raise Exception(

            "No fue posible crear el detalle del constructor."

        )

    detalle_pedido_id = fila[0]

    componentes = item.get(

        "componentes",

        []

    )

    if not componentes:

        raise Exception(

            "El constructor no tiene componentes."

        )

    for componente in componentes:

        cursor.execute(f"""
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
        """, (

            detalle_pedido_id,

            componente["producto_id"]

        ))

    return detalle_pedido_id


# =============================
# 🧾 CREAR PEDIDO
# =============================
def crear_pedido(data):

    conn = get_connection()
    cursor = conn.cursor()
    usuario_id = session.get("user_id")

    try:
        detalles = data.get("detalles", [])

        if not detalles:
            raise Exception("No hay productos en el pedido")

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        total = _calcular_total_pedido(detalles)

        # =============================
        # INSERT PEDIDO
        # =============================
        pedido_id = _insertar_pedido(

            cursor=cursor,

            data=data,

            usuario_id=usuario_id,

            total=total,

            is_postgres=is_postgres,

            placeholder=placeholder

        )

        # =============================
        # DETALLE PEDIDO
        # =============================
        for item in detalles:

            _guardar_detalle(

                cursor=cursor,

                pedido_id=pedido_id,

                item=item,

                is_postgres=is_postgres,

                placeholder=placeholder

            )

        conn.commit()

        return {
            "message": "Pedido registrado correctamente",
            "total": float(total),
            "pedido_id": pedido_id
        }

    except Exception as e:
        conn.rollback()
        print("❌ ERROR PEDIDO:", e)
        raise e

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

                pr.nombre AS producto,
                pr.categoria AS categoria

            FROM {DETALLE_PEDIDOS} dp

            INNER JOIN {PEDIDOS} p
                ON p.id = dp.pedido_id

            LEFT JOIN {USUARIOS} u
                ON u.id = p.usuario_id

            LEFT JOIN {PRODUCTOS} pr
                ON pr.id = dp.producto_id

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
                    "Menú Ejecutivo",

                "MENU_PREMIUM":
                    "Menú Premium",

                "MENU_ESPECIAL":
                    "Menú Especial",

                "DESAYUNO":
                    "Desayuno",

                "COMIDA_RAPIDA":
                    "Comida Rápida",

                "LICOR":
                    "Licor"

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
        "LICOR"

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

    cursor.execute(f"""

        SELECT

            dp.id                AS detalle_id,
            dp.pedido_id,
            dp.producto_id,
            dp.tipo_item,
            dp.cantidad,
            dp.precio,

            p.nombre            AS producto_nombre,
            p.categoria         AS categoria

        FROM {DETALLE_PEDIDOS} dp

        LEFT JOIN {PRODUCTOS} p
               ON p.id = dp.producto_id

        WHERE dp.pedido_id = {placeholder}

        ORDER BY dp.id

    """, (pedido_id,))

    columns = [c[0] for c in cursor.description]

    data = []

    for r in cursor.fetchall():

        row = dict(zip(columns, r))

        row["cantidad"] = float(row.get("cantidad") or 0)

        row["precio"] = float(row.get("precio") or 0)

        data.append(row)

    return data

# ==========================================================
# OBTENER COMPONENTES DEL DETALLE
# ==========================================================

def obtener_componentes_detalle(
    cursor,
    detalle_id,
    placeholder
):

    cursor.execute(f"""

        SELECT

            p.id,
            p.nombre,
            p.categoria

        FROM {DETALLE_PEDIDO_COMPONENTES} dpc

        INNER JOIN {PRODUCTOS} p

            ON p.id = dpc.producto_id

        WHERE dpc.detalle_pedido_id = {placeholder}

        ORDER BY p.categoria,
                 p.nombre

    """, (detalle_id,))

    columns = [c[0] for c in cursor.description]

    data = []

    for r in cursor.fetchall():

        data.append(

            dict(zip(columns, r))

        )

    return data

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

def transformar_constructor(item):

    detalle = crear_item_detalle()

    detalle["id"] = item.get("detalle_id")

    detalle["tipo"] = str(

        item.get("tipo_item", "")

    ).upper()

    detalle["nombre"] = (

        item.get("nombre")

        or item.get("tipo_item", "")

            .replace("_", " ")

            .title()

    )

    detalle["cantidad"] = float(

        item.get("cantidad") or 0

    )

    detalle["precio"] = float(

        item.get("precio") or 0

    )

    detalle["subtotal"] = round(

        detalle["cantidad"]

        *

        detalle["precio"],

        2

    )

    detalle["observaciones"] = item.get(

        "observaciones",

        ""

    )

    detalle["componentes"] = []

    for componente in item.get(

        "componentes",

        []

    ):

        detalle["componentes"].append({

            "producto_id":

                componente.get("id"),

            "categoria":

                componente.get("categoria"),

            "nombre":

                componente.get("nombre")

        })

    detalle["metadata"] = {

        "constructor": True

    }

    print("CONSTRUCTOR TRANSFORMADO")

    print(detalle)

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

    detalle["id"] = item.get("id")

    detalle["tipo"] = "PRODUCTO"

    detalle["nombre"] = item.get("nombre")

    detalle["cantidad"] = item.get("cantidad")

    detalle["precio"] = float(item.get("precio") or 0)

    detalle["subtotal"] = round(

        detalle["cantidad"] *

        detalle["precio"],

        2

    )

    detalle["observaciones"] = item.get(

        "observaciones",

        ""

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
        "LICOR"

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


# =============================
# 📄 DETALLE PEDIDO
# =============================
def get_pedido_detalle(pedido_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        # =============================
        # CABECERA PEDIDO
        # =============================
        cursor.execute(f"""
            SELECT
                id,
                mesa,
                tipo,
                cliente,
                categoria,
                estado,
                fecha
            FROM {PEDIDOS}
            WHERE id = {placeholder}
        """, (pedido_id,))

        pedido_row = cursor.fetchone()

        if not pedido_row:
            return None

        pedido = {
            "id": pedido_row[0],
            "mesa": pedido_row[1],
            "tipo": pedido_row[2],
            "cliente": pedido_row[3],
            "categoria": pedido_row[4],
            "estado": pedido_row[5],
            "fecha": str(pedido_row[6]) if pedido_row[6] else ""
        }

        # =============================
        # DETALLE CONSULTA ANTIGUA
        # =============================
        #cursor.execute(f"""
        #    SELECT
        #        dp.producto_id,
        #        p.nombre,
        #        dp.cantidad,
        #        dp.precio
        #    FROM {DETALLE_PEDIDOS} dp
        #    JOIN {PRODUCTOS} p
        #        ON dp.producto_id = p.id
        #    WHERE dp.pedido_id = {placeholder}
        #""", (pedido_id,))

        #columns = [c[0] for c in cursor.description]

        #detalle = []

        #for r in cursor.fetchall():

        #    row = dict(zip(columns, r))

        #    row["cantidad"] = float(row.get("cantidad") or 0)
        #    row["precio"] = float(row.get("precio") or 0)

        #    detalle.append(row)
        detalle = obtener_detalles_pedido(

            cursor,

            pedido_id,

            placeholder

        )

        detalle = enriquecer_detalles_pedido(

            cursor,

            detalle,

            placeholder

        )

        print("DETALLE BD")

        for d in detalle:

            print(d)

        detalle = transformar_detalle_pedido(detalle)

        print("DETALLE FRONT")

        for d in detalle:

            print(d)

        return {

            "pedido": pedido,

            "detalle": detalle

            #    transformar_detalle_pedido(

            #        detalle

            #    )

        }

    finally:
        conn.close()


# =============================
# 🧾 FACTURAR PEDIDO → VENTA
# =============================
def facturar_pedido(pedido_id, metodo_pago="Efectivo", usuario_id=None, *args, **kwargs):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        usuario_id = usuario_id or session.get("user_id") or 1

        #print(f"🧾 FACTURAR PEDIDO | id={pedido_id} | metodo={metodo_pago} | usuario_id={usuario_id}")

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        cursor.execute(f"""
            SELECT id, estado, mesa, cliente, cliente_id, categoria
            FROM {PEDIDOS}
            WHERE id = {placeholder}
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if not pedido:
            raise Exception("Pedido no existe")

        if str(pedido[1]).lower() == "facturado":
            raise Exception("El pedido ya fue facturado")

        cursor.execute(f"""
            SELECT
                producto_id,
                tipo_item,
                cantidad,
                precio
            FROM {DETALLE_PEDIDOS}
            WHERE pedido_id = {placeholder}
            ORDER BY id
        """, (pedido_id,))

        detalles_db = cursor.fetchall()

        if not detalles_db:
            raise Exception("Pedido sin productos")

        data_venta = {
            "cliente": pedido[3] or f"Mesa {pedido[2]}",
            "cliente_id": pedido[4],
            "mesa": pedido[2],
            "categoria": pedido[5],
            "metodo_pago": metodo_pago,
            "usuario": session.get("nombreUsuario") or f"user_{usuario_id}",
            "usuario_id": usuario_id,  # 🔥 clave
            "detalles": []
        }

        for producto_id, tipo_item, cantidad, precio in detalles_db:

            tipo_item = str(
                tipo_item or "PRODUCTO"
            ).upper()

            data_venta["detalles"].append({
                "producto_id": producto_id,
                "tipo_item": tipo_item,
                "cantidad": float(cantidad or 0),
                "precio": float(precio or 0)
            })

        resultado = crear_venta(data_venta)

        cursor.execute(f"""
            UPDATE {PEDIDOS}
            SET estado = 'facturado'
            WHERE id = {placeholder}
        """, (pedido_id,))

        conn.commit()

        return {
            "message": "Pedido facturado correctamente",
            "venta": resultado
        }

    except Exception as e:
        conn.rollback()
        print("❌ ERROR FACTURAR PEDIDO:", e)
        raise e

    finally:
        conn.close()