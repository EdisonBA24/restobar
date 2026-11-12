
from decimal import Decimal, InvalidOperation

from config import Config
from database.connection import get_connection
from database.db_objects import (
    PRODUCTOS,
    CATALOGO_ITEMS,
    CATALOGO_LINEAS,
    MENU_CONFIGURACIONES,
    MENU_CATEGORIAS,
    MENU_CATEGORIA_PRODUCTOS,
)


class CatalogoMenuValidationError(ValueError):
    """Error de validación de la configuración de menús."""


# =====================================================
# CONFIGURACION Y HELPERS
# =====================================================

def _settings():

    is_postgres = (
        str(
            getattr(Config, "DB_ENGINE", "sqlserver") or "sqlserver"
        ).strip().lower() == "postgres"
    )

    return is_postgres, "%s" if is_postgres else "?"


def _true_sql():

    return "TRUE" if _settings()[0] else "1"


def _int(value, field, required=False, minimum=0):

    if value is None or str(value).strip() == "":

        if required:
            raise CatalogoMenuValidationError(
                f"El campo '{field}' es obligatorio."
            )

        return None

    try:

        result = int(value)

    except (TypeError, ValueError):

        raise CatalogoMenuValidationError(
            f"El campo '{field}' debe ser un entero válido."
        )

    if result < minimum:

        raise CatalogoMenuValidationError(
            f"El campo '{field}' debe ser mayor o igual a {minimum}."
        )

    return result


def _bool(value, default=False):

    if value is None:
        return default

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return value != 0

    return str(value).strip().lower() in {
        "1", "true", "yes", "si", "sí", "activo"
    }


def _text(value, field, max_len, required=False):

    result = str(value or "").strip()

    if required and not result:

        raise CatalogoMenuValidationError(
            f"El campo '{field}' es obligatorio."
        )

    if len(result) > max_len:

        raise CatalogoMenuValidationError(
            f"El campo '{field}' supera los {max_len} caracteres."
        )

    return result or None


def _money(value, field="precio_adicional"):

    try:

        result = Decimal(
            str(value if value is not None else 0)
        )

    except (InvalidOperation, TypeError, ValueError):

        raise CatalogoMenuValidationError(
            f"El campo '{field}' debe ser numérico."
        )

    if (
        not result.is_finite()
        or result < 0
        or result >= Decimal("1000000000000")
    ):

        raise CatalogoMenuValidationError(
            f"El campo '{field}' tiene un valor inválido."
        )

    rounded = result.quantize(
        Decimal("0.01")
    )

    if rounded != result:

        raise CatalogoMenuValidationError(
            f"El campo '{field}' admite máximo dos decimales."
        )

    return rounded


def _row_dict(cursor, row=None):

    row = (
        cursor.fetchone()
        if row is None
        else row
    )

    if row is None:
        return None

    return _normalize(
        dict(zip(
            [column[0] for column in cursor.description],
            row
        ))
    )


def _rows_dict(cursor):

    columns = [
        column[0]
        for column in cursor.description
    ]

    return [
        _normalize(dict(zip(columns, row)))
        for row in cursor.fetchall()
    ]


def _normalize(record):

    result = {}

    bool_fields = {
        "activo",
        "obligatorio",
        "permitir_repetidos",
        "predeterminado",
        "permite_personalizar",
        "asignado"
    }

    decimal_fields = {
        "precio_venta",
        "precio_adicional",
        "stock"
    }

    for key, value in record.items():

        if key in bool_fields and value is not None:

            result[key] = bool(value)

        elif key in decimal_fields and value is not None:

            result[key] = float(value)

        else:

            result[key] = value

    return result


# =====================================================
# VALIDAR MENU O COMBO
# =====================================================

def _validar_menu(
    cursor,
    menu_item_id,
    placeholder,
    incluir_inactivos=False
):

    cursor.execute(
        f"""
        SELECT

            ci.id,

            ci.tipo_item,

            ci.nombre,

            ci.activo,

            cl.activo AS linea_activa,

            mc.permite_personalizar,

            mc.instrucciones,

            mc.activo AS configuracion_activa

        FROM {CATALOGO_ITEMS} ci

        INNER JOIN {CATALOGO_LINEAS} cl
            ON cl.id = ci.linea_id

        LEFT JOIN {MENU_CONFIGURACIONES} mc
            ON mc.catalogo_item_id = ci.id

        WHERE ci.id = {placeholder}
        """,
        (menu_item_id,)
    )

    menu = _row_dict(cursor)

    if not menu:

        raise CatalogoMenuValidationError(
            "El menú o combo comercial no existe."
        )

    if menu["tipo_item"] not in {"MENU", "COMBO"}:

        raise CatalogoMenuValidationError(
            "La configuración de categorías solo aplica a artículos tipo MENU o COMBO."
        )

    if not incluir_inactivos:

        if (
            not menu.get("activo")
            or not menu.get("linea_activa")
        ):

            raise CatalogoMenuValidationError(
                "El menú o su línea comercial están inactivos."
            )

        if (
            menu.get("configuracion_activa") is not None
            and not _bool(menu.get("configuracion_activa"))
        ):

            raise CatalogoMenuValidationError(
                "La configuración del menú está inactiva."
            )

    return menu


# =====================================================
# OBTENER CATEGORIA DE MENU
# =====================================================

def _obtener_categoria(
    cursor,
    menu_categoria_id,
    placeholder,
    menu_item_id=None
):

    query = f"""
        SELECT

            id,

            menu_item_id,

            codigo,

            nombre,

            descripcion,

            obligatorio,

            min_selecciones,

            max_selecciones,

            permitir_repetidos,

            activo,

            orden

        FROM {MENU_CATEGORIAS}

        WHERE id = {placeholder}
    """

    params = [
        menu_categoria_id
    ]

    if menu_item_id is not None:

        query += f" AND menu_item_id = {placeholder}"

        params.append(
            menu_item_id
        )

    cursor.execute(
        query,
        tuple(params)
    )

    return _row_dict(cursor)


# =====================================================
# NORMALIZAR CATEGORIA DE MENU
# =====================================================

def _normalizar_categoria(data, current=None):

    current = current or {}

    codigo = _text(
        data.get("codigo", current.get("codigo")),
        "codigo",
        50,
        required=True
    ).upper().replace(" ", "_")

    nombre = _text(
        data.get("nombre", current.get("nombre")),
        "nombre",
        120,
        required=True
    )

    descripcion = _text(
        data.get("descripcion", current.get("descripcion")),
        "descripcion",
        300
    )

    obligatorio = _bool(
        data.get("obligatorio", current.get("obligatorio")),
        False
    )

    default_min = current.get("min_selecciones")

    if default_min is None:

        default_min = 1 if obligatorio else 0

    min_value = (
        data["min_selecciones"]
        if "min_selecciones" in data
        else default_min
    )

    minimo = _int(
        min_value,
        "min_selecciones",
        minimum=0
    )

    max_value = data.get(
        "max_selecciones",
        current.get("max_selecciones", 1)
    )

    maximo = _int(
        max_value,
        "max_selecciones",
        required=True,
        minimum=1
    )

    # Una categoría obligatoria siempre debe exigir
    # al menos una selección.
    if obligatorio and minimo == 0:

        raise CatalogoMenuValidationError(
            "Una categoría obligatoria debe tener al menos una selección mínima."
        )

    # Una categoría opcional puede omitirse completamente.
    # Por tanto, su mínimo debe ser cero.
    if not obligatorio:
        minimo = 0

    if minimo > maximo:

        raise CatalogoMenuValidationError(
            "La selección mínima no puede superar la selección máxima."
        )

    permitir_repetidos = _bool(
        data.get(
            "permitir_repetidos",
            current.get("permitir_repetidos")
        ),
        False
    )

    activo = _bool(
        data.get("activo", current.get("activo")),
        True
    )

    orden = _int(
        data.get("orden", current.get("orden", 0)),
        "orden",
        minimum=0
    )

    return {

        "codigo": codigo,

        "nombre": nombre,

        "descripcion": descripcion,

        "obligatorio": obligatorio,

        "min_selecciones": minimo,

        "max_selecciones": maximo,

        "permitir_repetidos": permitir_repetidos,

        "activo": activo,

        "orden": orden

    }


# =====================================================
# VALIDAR CODIGO UNICO POR MENU
# =====================================================

def _validar_codigo_categoria(
    cursor,
    menu_item_id,
    codigo,
    placeholder,
    exclude_id=None
):

    query = f"""
        SELECT id

        FROM {MENU_CATEGORIAS}

        WHERE menu_item_id = {placeholder}

          AND UPPER(codigo) = UPPER({placeholder})
    """

    params = [
        menu_item_id,
        codigo
    ]

    if exclude_id is not None:

        query += f" AND id <> {placeholder}"

        params.append(exclude_id)

    cursor.execute(
        query,
        tuple(params)
    )

    if cursor.fetchone():

        raise CatalogoMenuValidationError(
            "Ya existe una categoría con ese código dentro del menú."
        )



# =====================================================
# CONSULTAR CONFIGURACION COMPLETA DE UN MENU
# COMPATIBLE SQL SERVER Y POSTGRESQL
# =====================================================

def obtener_configuracion_menu(
    menu_item_id,
    incluir_inactivos=False
):

    menu_item_id = _int(
        menu_item_id,
        "menu_item_id",
        required=True,
        minimum=1
    )

    _, placeholder = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        # =============================================
        # VALIDAR MENU
        # =============================================

        menu = _validar_menu(
            cursor,
            menu_item_id,
            placeholder,
            incluir_inactivos=incluir_inactivos
        )

        # =============================================
        # FILTRO DE CATEGORIAS
        #
        # Esta consulta solamente utiliza
        # menu_categorias.
        #
        # NO debe utilizar p.activo.
        # =============================================

        filtro_categorias = (

            ""

            if incluir_inactivos

            else f"AND activo = {_true_sql()}"

        )

        cursor.execute(
            f"""
            SELECT

                id,

                menu_item_id,

                codigo,

                nombre,

                descripcion,

                obligatorio,

                min_selecciones,

                max_selecciones,

                permitir_repetidos,

                activo,

                orden

            FROM {MENU_CATEGORIAS}

            WHERE menu_item_id = {placeholder}

            {filtro_categorias}

            ORDER BY orden, nombre
            """,
            (menu_item_id,)
        )

        categorias = _rows_dict(cursor)

        # =============================================
        # RECORRER CATEGORIAS
        # =============================================

        for categoria in categorias:

            # =========================================
            # FILTRO DE PRODUCTOS
            #
            # Aqui SI existe el alias p.
            #
            # mcp.activo:
            #   Campo booleano del catalogo.
            #
            # p.activo:
            #   Campo numerico del modulo Productos.
            # =========================================

            filtro_productos = (

                ""

                if incluir_inactivos

                else f"""
                    AND mcp.activo = {_true_sql()}
                    AND p.activo = 1
                """

            )

            cursor.execute(
                f"""
                SELECT

                    mcp.id AS relacion_id,

                    mcp.menu_categoria_id,

                    mcp.producto_id,

                    p.codigo AS producto_codigo,

                    p.nombre AS producto_nombre,

                    p.tipo AS producto_tipo,

                    p.categoria AS producto_categoria,

                    p.imagen_url,

                    p.precio_venta,

                    mcp.precio_adicional,

                    mcp.predeterminado,

                    mcp.activo,

                    mcp.orden

                FROM {MENU_CATEGORIA_PRODUCTOS} mcp

                INNER JOIN {PRODUCTOS} p

                    ON p.id = mcp.producto_id

                WHERE mcp.menu_categoria_id = {placeholder}

                {filtro_productos}

                ORDER BY
                    mcp.orden,
                    p.nombre
                """,
                (categoria["id"],)
            )

            categoria["productos"] = _rows_dict(cursor)

        # =============================================
        # RESPUESTA FINAL
        # =============================================

        return {

            "id": menu["id"],

            "tipo_item": menu["tipo_item"],

            "nombre": menu["nombre"],

            "activo": bool(menu["activo"]),

            "configuracion": {

                "permite_personalizar": (

                    True

                    if menu.get("permite_personalizar") is None

                    else bool(menu["permite_personalizar"])

                ),

                "instrucciones": menu.get("instrucciones"),

                "activo": (

                    True

                    if menu.get("configuracion_activa") is None

                    else _bool(menu["configuracion_activa"])

                )

            },

            "categorias": categorias

        }

    finally:

        conn.close()



# =====================================================
# CREAR CATEGORIA DENTRO DEL MENU
# =====================================================

def crear_categoria_menu(menu_item_id, data):

    menu_item_id = _int(
        menu_item_id,
        "menu_item_id",
        required=True,
        minimum=1
    )

    if not isinstance(data, dict):

        raise CatalogoMenuValidationError(
            "Los datos de la categoría no son válidos."
        )

    category = _normalizar_categoria(data)

    is_postgres, placeholder = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        _validar_menu(
            cursor,
            menu_item_id,
            placeholder
        )

        _validar_codigo_categoria(
            cursor,
            menu_item_id,
            category["codigo"],
            placeholder
        )

        columnas = """
            menu_item_id,
            codigo,
            nombre,
            descripcion,
            obligatorio,
            min_selecciones,
            max_selecciones,
            permitir_repetidos,
            activo,
            orden
        """

        values = ", ".join([placeholder] * 10)

        params = (

            menu_item_id,

            category["codigo"],

            category["nombre"],

            category["descripcion"],

            category["obligatorio"],

            category["min_selecciones"],

            category["max_selecciones"],

            category["permitir_repetidos"],

            category["activo"],

            category["orden"]

        )

        if is_postgres:

            cursor.execute(
                f"""
                INSERT INTO {MENU_CATEGORIAS}
                    ({columnas})

                VALUES ({values})

                RETURNING id
                """,
                params
            )

        else:

            cursor.execute(
                f"""
                INSERT INTO {MENU_CATEGORIAS}
                    ({columnas})

                OUTPUT INSERTED.id

                VALUES ({values})
                """,
                params
            )

        new_id = int(
            cursor.fetchone()[0]
        )

        conn.commit()

        return {

            "id": new_id,

            "message": "Categoría del menú creada correctamente."

        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# =====================================================
# ACTUALIZAR CATEGORIA DE MENU
# =====================================================

def actualizar_categoria_menu(
    menu_item_id,
    menu_categoria_id,
    data
):

    menu_item_id = _int(
        menu_item_id,
        "menu_item_id",
        required=True,
        minimum=1
    )

    menu_categoria_id = _int(
        menu_categoria_id,
        "menu_categoria_id",
        required=True,
        minimum=1
    )

    if not isinstance(data, dict) or not data:

        raise CatalogoMenuValidationError(
            "No se enviaron datos para actualizar la categoría."
        )

    _, placeholder = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        _validar_menu(
            cursor,
            menu_item_id,
            placeholder,
            incluir_inactivos=True
        )

        current = _obtener_categoria(
            cursor,
            menu_categoria_id,
            placeholder,
            menu_item_id
        )

        if not current:

            raise CatalogoMenuValidationError(
                "La categoría no existe dentro del menú indicado."
            )

        category = _normalizar_categoria(
            data,
            current
        )

        _validar_codigo_categoria(
            cursor,
            menu_item_id,
            category["codigo"],
            placeholder,
            exclude_id=menu_categoria_id
        )

        cursor.execute(
            f"""
            UPDATE {MENU_CATEGORIAS}

            SET
                codigo = {placeholder},
                nombre = {placeholder},
                descripcion = {placeholder},
                obligatorio = {placeholder},
                min_selecciones = {placeholder},
                max_selecciones = {placeholder},
                permitir_repetidos = {placeholder},
                activo = {placeholder},
                orden = {placeholder}

            WHERE id = {placeholder}

              AND menu_item_id = {placeholder}
            """,
            (

                category["codigo"],

                category["nombre"],

                category["descripcion"],

                category["obligatorio"],

                category["min_selecciones"],

                category["max_selecciones"],

                category["permitir_repetidos"],

                category["activo"],

                category["orden"],

                menu_categoria_id,

                menu_item_id

            )
        )

        conn.commit()

        return {
            "message": "Categoría del menú actualizada correctamente."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# =====================================================
# ACTIVAR / DESACTIVAR CATEGORIA DE MENU
# =====================================================

def cambiar_estado_categoria_menu(
    menu_item_id,
    menu_categoria_id,
    activo
):

    menu_item_id = _int(
        menu_item_id,
        "menu_item_id",
        required=True,
        minimum=1
    )

    menu_categoria_id = _int(
        menu_categoria_id,
        "menu_categoria_id",
        required=True,
        minimum=1
    )

    active = _bool(activo)

    _, placeholder = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        _validar_menu(
            cursor,
            menu_item_id,
            placeholder,
            incluir_inactivos=True
        )

        current = _obtener_categoria(
            cursor,
            menu_categoria_id,
            placeholder,
            menu_item_id
        )

        if not current:

            raise CatalogoMenuValidationError(
                "La categoría no existe dentro del menú indicado."
            )

        cursor.execute(
            f"""
            UPDATE {MENU_CATEGORIAS}

            SET activo = {placeholder}

            WHERE id = {placeholder}

              AND menu_item_id = {placeholder}
            """,
            (
                active,
                menu_categoria_id,
                menu_item_id
            )
        )

        conn.commit()

        return {
            "message": "Estado de la categoría actualizado correctamente."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# =====================================================
# CONSULTAR PRODUCTOS ASOCIADOS A UNA CATEGORIA
# =====================================================

def listar_productos_categoria_menu(
    menu_categoria_id,
    incluir_inactivos=False
):

    menu_categoria_id = _int(
        menu_categoria_id,
        "menu_categoria_id",
        required=True,
        minimum=1
    )

    _, placeholder = _settings()

    filtro = (
        ""
        if incluir_inactivos
        else f"""
            AND mcp.activo = {_true_sql()}
            AND p.activo = 1
        """
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        categoria = _obtener_categoria(
            cursor,
            menu_categoria_id,
            placeholder
        )

        if not categoria:

            raise CatalogoMenuValidationError(
                "La categoría del menú no existe."
            )

        cursor.execute(
            f"""
            SELECT

                mcp.id AS relacion_id,

                mcp.menu_categoria_id,

                mcp.producto_id,

                p.codigo AS producto_codigo,

                p.nombre AS producto_nombre,

                p.tipo AS producto_tipo,

                p.categoria AS producto_categoria,

                p.imagen_url,

                p.precio_venta,

                p.stock,

                mcp.precio_adicional,

                mcp.predeterminado,

                mcp.activo,

                mcp.orden

            FROM {MENU_CATEGORIA_PRODUCTOS} mcp

            INNER JOIN {PRODUCTOS} p
                ON p.id = mcp.producto_id

            WHERE mcp.menu_categoria_id = {placeholder}

            {filtro}

            ORDER BY mcp.orden, p.nombre
            """,
            (menu_categoria_id,)
        )

        return {

            "categoria": categoria,

            "productos": _rows_dict(cursor)

        }

    finally:

        conn.close()


# =====================================================
# LISTAR PRODUCTOS DISPONIBLES PARA CONFIGURAR
# =====================================================

def listar_productos_disponibles_menu_categoria(
    menu_categoria_id,
    search=None,
    incluir_inactivos=False
):

    menu_categoria_id = _int(
        menu_categoria_id,
        "menu_categoria_id",
        required=True,
        minimum=1
    )

    is_postgres, placeholder = _settings()

    search = str(
        search or ""
    ).strip()[:100]

    false_literal = (
        "FALSE"
        if is_postgres
        else "0"
    )

    conditions = [
        "UPPER(p.tipo) = 'RECETA'"
    ]

    params = []

    if not incluir_inactivos:

        conditions.append(
            f"p.activo = {_true_sql()}"
        )

    if search:

        conditions.append(
            f"""
            (
                LOWER(p.nombre) LIKE {placeholder}

                OR LOWER(COALESCE(p.codigo, '')) LIKE {placeholder}
            )
            """
        )

        like = f"%{search.lower()}%"

        params.extend([
            like,
            like
        ])

    where = " AND ".join(conditions)

    conn = get_connection()

    try:

        cursor = conn.cursor()

        categoria = _obtener_categoria(
            cursor,
            menu_categoria_id,
            placeholder
        )

        if not categoria:

            raise CatalogoMenuValidationError(
                "La categoría del menú no existe."
            )

        cursor.execute(
            f"""
            SELECT

                p.id,

                p.codigo,

                p.nombre,

                p.tipo,

                p.categoria,

                p.precio_venta,

                p.stock,

                p.imagen_url,

                CASE
                    WHEN mcp.id IS NULL THEN 0
                    ELSE 1
                END AS asignado,

                COALESCE(
                    mcp.precio_adicional,
                    0
                ) AS precio_adicional,

                COALESCE(
                    mcp.predeterminado,
                    {false_literal}
                ) AS predeterminado,

                COALESCE(
                    mcp.activo,
                    {false_literal}
                ) AS relacion_activa,

                COALESCE(
                    mcp.orden,
                    0
                ) AS orden

            FROM {PRODUCTOS} p

            LEFT JOIN {MENU_CATEGORIA_PRODUCTOS} mcp

                ON mcp.producto_id = p.id

                AND mcp.menu_categoria_id = {placeholder}

            WHERE {where}

            ORDER BY p.nombre
            """,
            tuple([menu_categoria_id] + params)
        )

        return _rows_dict(cursor)

    finally:

        conn.close()


# =====================================================
# ASOCIAR / ACTUALIZAR PRODUCTOS DE UNA CATEGORIA
#
# La lista recibida representa el conjunto completo
# que debe quedar asociado.
#
# Los elementos retirados se desactivan lógicamente.
# No se eliminan registros físicamente.
# =====================================================

def guardar_productos_categoria_menu(
    menu_categoria_id,
    productos
):

    menu_categoria_id = _int(
        menu_categoria_id,
        "menu_categoria_id",
        required=True,
        minimum=1
    )

    if not isinstance(productos, list):

        raise CatalogoMenuValidationError(
            "El campo 'productos' debe ser una lista."
        )

    if len(productos) > 500:

        raise CatalogoMenuValidationError(
            "No se pueden asociar más de 500 productos a una categoría."
        )

    _, placeholder = _settings()

    prepared = []

    seen = set()

    for index, item in enumerate(productos, start=1):

        if not isinstance(item, dict):

            raise CatalogoMenuValidationError(
                f"El producto de la posición {index} no es válido."
            )

        product_id = _int(
            item.get("producto_id"),
            "producto_id",
            required=True,
            minimum=1
        )

        if product_id in seen:

            raise CatalogoMenuValidationError(
                f"El producto {product_id} está repetido en la solicitud."
            )

        seen.add(product_id)

        active = _bool(
            item.get("activo"),
            True
        )

        prepared.append({

            "producto_id": product_id,

            "precio_adicional": _money(
                item.get("precio_adicional", 0)
            ),

            "predeterminado": (
                _bool(item.get("predeterminado"), False)
                if active
                else False
            ),

            "activo": active,

            "orden": _int(
                item.get("orden", index),
                "orden",
                minimum=0
            )

        })

    conn = get_connection()

    try:

        cursor = conn.cursor()

        categoria = _obtener_categoria(
            cursor,
            menu_categoria_id,
            placeholder
        )

        if not categoria:

            raise CatalogoMenuValidationError(
                "La categoría del menú no existe."
            )

        # =============================================
        # VALIDAR CANTIDAD DE PREDETERMINADOS
        # =============================================

        defaults_count = sum(

            1
            for item in prepared

            if item["activo"] and item["predeterminado"]

        )

        if defaults_count > categoria["max_selecciones"]:

            raise CatalogoMenuValidationError(
                "La cantidad de productos predeterminados supera el máximo de selecciones de la categoría."
            )

        # =============================================
        # VALIDAR TODOS LOS PRODUCTOS
        # =============================================

        for item in prepared:

            cursor.execute(
                f"""
                SELECT

                    id,

                    nombre,

                    tipo,

                    activo

                FROM {PRODUCTOS}

                WHERE id = {placeholder}
                """,
                (item["producto_id"],)
            )

            product = cursor.fetchone()

            if not product:

                raise CatalogoMenuValidationError(
                    f"El producto {item['producto_id']} no existe."
                )

            if not _bool(product[3]):

                raise CatalogoMenuValidationError(
                    f"El producto '{product[1]}' está inactivo."
                )

            if (
                str(product[2] or "").strip().upper()
                != "RECETA"
            ):

                raise CatalogoMenuValidationError(
                    f"El producto '{product[1]}' no es vendible. Solo se permiten productos tipo RECETA como componentes de menús."
                )

        # =============================================
        # CONSULTAR ASOCIACIONES EXISTENTES
        # =============================================

        cursor.execute(
            f"""
            SELECT

                id,

                producto_id

            FROM {MENU_CATEGORIA_PRODUCTOS}

            WHERE menu_categoria_id = {placeholder}
            """,
            (menu_categoria_id,)
        )

        existing = {

            int(row[1]): int(row[0])

            for row in cursor.fetchall()

        }

        incoming_ids = set(seen)

        # =============================================
        # DESACTIVAR PRODUCTOS RETIRADOS
        # =============================================

        for product_id, relation_id in existing.items():

            if product_id not in incoming_ids:

                cursor.execute(
                    f"""
                    UPDATE {MENU_CATEGORIA_PRODUCTOS}

                    SET

                        activo = {placeholder},

                        predeterminado = {placeholder}

                    WHERE id = {placeholder}
                    """,
                    (
                        False,
                        False,
                        relation_id
                    )
                )

        # =============================================
        # INSERTAR O ACTUALIZAR ASOCIACIONES
        # =============================================

        is_postgres, _ = _settings()

        for item in prepared:

            relation_id = existing.get(
                item["producto_id"]
            )

            values = (

                item["precio_adicional"],

                item["predeterminado"],

                item["activo"],

                item["orden"]

            )

            if relation_id is not None:

                cursor.execute(
                    f"""
                    UPDATE {MENU_CATEGORIA_PRODUCTOS}

                    SET

                        precio_adicional = {placeholder},

                        predeterminado = {placeholder},

                        activo = {placeholder},

                        orden = {placeholder}

                    WHERE id = {placeholder}
                    """,
                    values + (relation_id,)
                )

            else:

                cursor.execute(
                    f"""
                    INSERT INTO {MENU_CATEGORIA_PRODUCTOS}
                    (
                        menu_categoria_id,
                        producto_id,
                        precio_adicional,
                        predeterminado,
                        activo,
                        orden
                    )

                    VALUES (
                        {placeholder},
                        {placeholder},
                        {placeholder},
                        {placeholder},
                        {placeholder},
                        {placeholder}
                    )
                    """,
                    (
                        menu_categoria_id,
                        item["producto_id"],
                        item["precio_adicional"],
                        item["predeterminado"],
                        item["activo"],
                        item["orden"]
                    )
                )

        conn.commit()

        return {

            "message": "Productos de la categoría actualizados correctamente.",

            "productos_asociados": sum(
                1 for item in prepared if item["activo"]
            )

        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()
