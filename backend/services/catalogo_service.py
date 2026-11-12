
from datetime import date, datetime
from decimal import Decimal, InvalidOperation

from config import Config
from database.connection import get_connection
from database.db_objects import (
    PRODUCTOS,
    USUARIOS,
    CATALOGO_LINEAS,
    CATALOGO_CATEGORIAS,
    CATALOGO_ITEMS,
    CATALOGO_PRECIOS,
    CATALOGO_PRECIOS_HISTORIAL,
    MENU_CONFIGURACIONES,
)


class CatalogoValidationError(ValueError):
    """Error controlado de validación del catálogo comercial."""


TIPOS_ITEM = {"PRODUCTO", "MENU", "COMBO"}
TIPOS_SERVICIO = {"GENERAL", "MESA", "LLEVAR", "DOMICILIO"}


# =====================================================
# CONFIGURACION DE BASE DE DATOS
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


# =====================================================
# VALIDACIONES GENERALES
# =====================================================

def _int(value, field, required=False, minimum=1):

    if value is None or str(value).strip() == "":

        if required:
            raise CatalogoValidationError(
                f"El campo '{field}' es obligatorio."
            )

        return None

    try:

        result = int(value)

    except (TypeError, ValueError):

        raise CatalogoValidationError(
            f"El campo '{field}' debe ser un entero válido."
        )

    if result < minimum:

        raise CatalogoValidationError(
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

    value = str(value or "").strip()

    if required and not value:

        raise CatalogoValidationError(
            f"El campo '{field}' es obligatorio."
        )

    if len(value) > max_len:

        raise CatalogoValidationError(
            f"El campo '{field}' supera los {max_len} caracteres."
        )

    return value or None


def _price(value):

    try:

        value = Decimal(str(value))

    except (InvalidOperation, TypeError, ValueError):

        raise CatalogoValidationError(
            "El precio debe ser un número válido."
        )

    if (
        not value.is_finite()
        or value < 0
        or value >= Decimal("1000000000000")
    ):

        raise CatalogoValidationError(
            "El precio debe ser un número finito entre 0 y 999.999.999.999,99."
        )

    rounded = value.quantize(Decimal("0.01"))

    if rounded != value:

        raise CatalogoValidationError(
            "El precio admite máximo dos decimales."
        )

    return rounded


# =====================================================
# CONVERSION DE RESULTADOS SQL
# =====================================================

def _row_dict(cursor, row=None):

    row = cursor.fetchone() if row is None else row

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


def _normalize(data):

    result = {}

    for key, value in data.items():

        if isinstance(value, Decimal):

            result[key] = float(value)

        elif isinstance(value, (datetime, date)):

            result[key] = value.isoformat()

        elif key in {
            "activo",
            "destacado",
            "obligatorio",
            "permite_personalizar"
        } and value is not None:

            result[key] = bool(value)

        else:

            result[key] = value

    return result


# =====================================================
# VALIDAR RELACIONES
# =====================================================

def _assert_line_and_category(
    cursor,
    line_id,
    category_id,
    ph
):

    cursor.execute(
        f"""
        SELECT id
        FROM {CATALOGO_LINEAS}
        WHERE id = {ph}
          AND activo = {_true_sql()}
        """,
        (line_id,)
    )

    if not cursor.fetchone():

        raise CatalogoValidationError(
            "La línea comercial no existe o está inactiva."
        )

    if category_id is not None:

        cursor.execute(
            f"""
            SELECT id
            FROM {CATALOGO_CATEGORIAS}
            WHERE id = {ph}
              AND linea_id = {ph}
              AND activo = {_true_sql()}
            """,
            (category_id, line_id)
        )

        if not cursor.fetchone():

            raise CatalogoValidationError(
                "La categoría no pertenece a la línea seleccionada o está inactiva."
            )


def _assert_unique_code(
    cursor,
    table,
    line_id,
    code,
    ph,
    exclude_id=None
):

    query = f"""
        SELECT id
        FROM {table}
        WHERE linea_id = {ph}
          AND UPPER(codigo) = UPPER({ph})
    """

    params = [line_id, code]

    if exclude_id is not None:

        query += f" AND id <> {ph}"

        params.append(exclude_id)

    cursor.execute(query, tuple(params))

    if cursor.fetchone():

        raise CatalogoValidationError(
            "Ya existe un registro con ese código en la línea seleccionada."
        )


def _get_product(cursor, product_id, ph):

    cursor.execute(
        f"""
        SELECT id, nombre, imagen_url, activo
        FROM {PRODUCTOS}
        WHERE id = {ph}
        """,
        (product_id,)
    )

    row = cursor.fetchone()

    if not row:

        raise CatalogoValidationError(
            "El producto relacionado no existe."
        )

    if not _bool(row[3]):

        raise CatalogoValidationError(
            "No se puede vincular un producto inactivo al catálogo."
        )

    return {

        "id": row[0],

        "nombre": row[1],

        "imagen_url": row[2]

    }


# =====================================================
# LINEAS COMERCIALES
# =====================================================

def listar_lineas_catalogo(incluir_inactivas=False):

    conn = get_connection()

    try:

        cursor = conn.cursor()

        where = (
            ""
            if incluir_inactivas
            else f"WHERE activo = {_true_sql()}"
        )

        cursor.execute(
            f"""
            SELECT
                id,
                codigo,
                nombre,
                descripcion,
                imagen_url,
                activo,
                orden

            FROM {CATALOGO_LINEAS}

            {where}

            ORDER BY orden, nombre
            """
        )

        return _rows_dict(cursor)

    finally:

        conn.close()


# =====================================================
# CATEGORIAS COMERCIALES
# =====================================================

def listar_categorias_catalogo(
    linea_id=None,
    incluir_inactivas=False
):

    is_postgres, ph = _settings()

    conditions = []
    params = []

    if linea_id not in (None, ""):

        conditions.append(
            f"cc.linea_id = {ph}"
        )

        params.append(
            _int(linea_id, "linea_id", required=True)
        )

    if not incluir_inactivas:

        conditions.extend([

            f"cc.activo = {_true_sql()}",

            f"cl.activo = {_true_sql()}"

        ])

    where = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT

                cc.id,

                cc.linea_id,

                cl.codigo AS linea_codigo,

                cl.nombre AS linea_nombre,

                cc.codigo,

                cc.nombre,

                cc.descripcion,

                cc.imagen_url,

                cc.activo,

                cc.orden

            FROM {CATALOGO_CATEGORIAS} cc

            INNER JOIN {CATALOGO_LINEAS} cl
                ON cl.id = cc.linea_id

            {where}

            ORDER BY
                cl.orden,
                cc.orden,
                cc.nombre
            """,
            tuple(params)
        )

        return _rows_dict(cursor)

    finally:

        conn.close()


def crear_categoria_catalogo(data):

    if not isinstance(data, dict):

        raise CatalogoValidationError(
            "Los datos de la categoría no son válidos."
        )

    line_id = _int(
        data.get("linea_id"),
        "linea_id",
        required=True
    )

    code = _text(
        data.get("codigo"),
        "codigo",
        50,
        True
    ).upper().replace(" ", "_")

    name = _text(
        data.get("nombre"),
        "nombre",
        120,
        True
    )

    description = _text(
        data.get("descripcion"),
        "descripcion",
        300
    )

    image_url = _text(
        data.get("imagen_url"),
        "imagen_url",
        1000
    )

    order = _int(
        data.get("orden", 0),
        "orden",
        minimum=0
    )

    is_postgres, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        _assert_line_and_category(
            cursor,
            line_id,
            None,
            ph
        )

        _assert_unique_code(
            cursor,
            CATALOGO_CATEGORIAS,
            line_id,
            code,
            ph
        )

        columns = """
            linea_id,
            codigo,
            nombre,
            descripcion,
            imagen_url,
            activo,
            orden
        """

        values = ", ".join([ph] * 5)

        values += (
            ", TRUE, "
            if is_postgres
            else ", 1, "
        )

        values += ph

        params = (
            line_id,
            code,
            name,
            description,
            image_url,
            order
        )

        if is_postgres:

            cursor.execute(
                f"""
                INSERT INTO {CATALOGO_CATEGORIAS}
                    ({columns})
                VALUES ({values})
                RETURNING id
                """,
                params
            )

        else:

            cursor.execute(
                f"""
                INSERT INTO {CATALOGO_CATEGORIAS}
                    ({columns})
                OUTPUT INSERTED.id
                VALUES ({values})
                """,
                params
            )

        new_id = int(cursor.fetchone()[0])

        conn.commit()

        return {

            "id": new_id,

            "message": "Categoría comercial creada correctamente."

        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def actualizar_categoria_catalogo(category_id, data):

    category_id = _int(
        category_id,
        "categoria_id",
        required=True
    )

    if not isinstance(data, dict) or not data:

        raise CatalogoValidationError(
            "No se enviaron datos para actualizar la categoría."
        )

    _, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT
                id,
                linea_id,
                codigo,
                nombre,
                descripcion,
                imagen_url,
                orden

            FROM {CATALOGO_CATEGORIAS}

            WHERE id = {ph}
            """,
            (category_id,)
        )

        current = _row_dict(cursor)

        if not current:

            raise CatalogoValidationError(
                "La categoría no existe."
            )

        line_id = _int(
            data.get("linea_id", current["linea_id"]),
            "linea_id",
            required=True
        )

        code = _text(
            data.get("codigo", current["codigo"]),
            "codigo",
            50,
            True
        ).upper().replace(" ", "_")

        name = _text(
            data.get("nombre", current["nombre"]),
            "nombre",
            120,
            True
        )

        description = _text(
            data.get("descripcion", current["descripcion"]),
            "descripcion",
            300
        )

        image_url = _text(
            data.get("imagen_url", current["imagen_url"]),
            "imagen_url",
            1000
        )

        order = _int(
            data.get("orden", current["orden"]),
            "orden",
            minimum=0
        )

        _assert_line_and_category(
            cursor,
            line_id,
            None,
            ph
        )

        _assert_unique_code(
            cursor,
            CATALOGO_CATEGORIAS,
            line_id,
            code,
            ph,
            category_id
        )

        cursor.execute(
            f"""
            UPDATE {CATALOGO_CATEGORIAS}

            SET
                linea_id = {ph},
                codigo = {ph},
                nombre = {ph},
                descripcion = {ph},
                imagen_url = {ph},
                orden = {ph},
                actualizado_en = CURRENT_TIMESTAMP

            WHERE id = {ph}
            """,
            (
                line_id,
                code,
                name,
                description,
                image_url,
                order,
                category_id
            )
        )

        conn.commit()

        return {
            "message": "Categoría comercial actualizada correctamente."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def cambiar_estado_categoria_catalogo(category_id, activo):

    category_id = _int(
        category_id,
        "categoria_id",
        required=True
    )

    _, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT id
            FROM {CATALOGO_CATEGORIAS}
            WHERE id = {ph}
            """,
            (category_id,)
        )

        if not cursor.fetchone():

            raise CatalogoValidationError(
                "La categoría no existe."
            )

        cursor.execute(
            f"""
            UPDATE {CATALOGO_CATEGORIAS}

            SET
                activo = {ph},
                actualizado_en = CURRENT_TIMESTAMP

            WHERE id = {ph}
            """,
            (
                _bool(activo),
                category_id
            )
        )

        conn.commit()

        return {
            "message": "Estado de categoría actualizado correctamente."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# =====================================================
# ARTICULOS COMERCIALES
# =====================================================

def listar_items_catalogo(filtros=None):

    filtros = filtros or {}

    is_postgres, ph = _settings()

    page = _int(
        filtros.get("page") or 1,
        "page",
        minimum=1
    )

    page_size = min(
        _int(
            filtros.get("page_size") or 20,
            "page_size",
            minimum=1
        ),
        100
    )

    line_id = _int(
        filtros.get("linea_id"),
        "linea_id"
    )

    category_id = _int(
        filtros.get("categoria_id"),
        "categoria_id"
    )

    item_type = str(
        filtros.get("tipo_item") or ""
    ).strip().upper()

    search = str(
        filtros.get("search") or ""
    ).strip()[:100]

    include_inactive = _bool(
        filtros.get("incluir_inactivos"),
        False
    )

    if item_type and item_type not in TIPOS_ITEM:

        raise CatalogoValidationError(
            "El tipo de artículo debe ser PRODUCTO, MENU o COMBO."
        )

    conditions = []
    params = []

    if line_id:

        conditions.append(
            f"ci.linea_id = {ph}"
        )

        params.append(line_id)

    if category_id:

        conditions.append(
            f"ci.categoria_id = {ph}"
        )

        params.append(category_id)

    if item_type:

        conditions.append(
            f"ci.tipo_item = {ph}"
        )

        params.append(item_type)

    if search:

        conditions.append(
            f"""
            (
                LOWER(ci.nombre) LIKE {ph}
                OR LOWER(ci.codigo) LIKE {ph}
                OR LOWER(COALESCE(ci.descripcion, '')) LIKE {ph}
            )
            """
        )

        like = f"%{search.lower()}%"

        params.extend([
            like,
            like,
            like
        ])

    if not include_inactive:

        conditions.extend([

            f"ci.activo = {_true_sql()}",

            f"cl.activo = {_true_sql()}",

            f"(cc.id IS NULL OR cc.activo = {_true_sql()})",

            f"(ci.producto_id IS NULL OR p.activo = 1)"

        ])

    where = (
        "WHERE " + " AND ".join(conditions)
        if conditions
        else ""
    )

    offset = (page - 1) * page_size

    conn = get_connection()

    try:

        cursor = conn.cursor()

        joins = f"""
            FROM {CATALOGO_ITEMS} ci

            INNER JOIN {CATALOGO_LINEAS} cl
                ON cl.id = ci.linea_id

            LEFT JOIN {CATALOGO_CATEGORIAS} cc
                ON cc.id = ci.categoria_id

            LEFT JOIN {PRODUCTOS} p
                ON p.id = ci.producto_id
        """

        cursor.execute(
            f"""
            SELECT COUNT(*)

            {joins}

            {where}
            """,
            tuple(params)
        )

        total = int(
            cursor.fetchone()[0] or 0
        )

        query = f"""
            SELECT

                ci.id,

                ci.linea_id,

                cl.codigo AS linea_codigo,

                cl.nombre AS linea_nombre,

                ci.categoria_id,

                cc.nombre AS categoria_nombre,

                ci.producto_id,

                ci.codigo,

                ci.tipo_item,

                ci.nombre,

                ci.descripcion,

                COALESCE(
                    NULLIF(ci.imagen_url, ''),
                    p.imagen_url
                ) AS imagen_url,

                ci.activo,

                ci.destacado,

                ci.orden,

                cp.precio AS precio_general

            {joins}

            LEFT JOIN {CATALOGO_PRECIOS} cp
                ON cp.catalogo_item_id = ci.id
                AND cp.tipo_servicio = 'GENERAL'
                AND cp.activo = {_true_sql()}

            {where}

            ORDER BY
                cl.orden,
                ci.orden,
                ci.nombre
        """

        if is_postgres:

            query += f"""
                LIMIT {ph}
                OFFSET {ph}
            """

            query_params = params + [
                page_size,
                offset
            ]

        else:

            query += f"""
                OFFSET {ph} ROWS
                FETCH NEXT {ph} ROWS ONLY
            """

            query_params = params + [
                offset,
                page_size
            ]

        cursor.execute(
            query,
            tuple(query_params)
        )

        items = _rows_dict(cursor)

        total_pages = max(
            (total + page_size - 1) // page_size,
            1
        )

        return {

            "items": items,

            "pagination": {

                "page": page,

                "page_size": page_size,

                "total": total,

                "total_pages": total_pages

            }

        }

    finally:

        conn.close()


def _get_item(cursor, item_id, ph):

    cursor.execute(
        f"""
        SELECT
            id,
            linea_id,
            categoria_id,
            producto_id,
            codigo,
            tipo_item,
            nombre,
            descripcion,
            imagen_url,
            activo,
            destacado,
            orden

        FROM {CATALOGO_ITEMS}

        WHERE id = {ph}
        """,
        (item_id,)
    )

    return _row_dict(cursor)


def obtener_item_catalogo(
    item_id,
    incluir_precios_inactivos=False
):

    item_id = _int(
        item_id,
        "item_id",
        required=True
    )

    _, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT

                ci.id,

                ci.linea_id,

                cl.codigo AS linea_codigo,

                cl.nombre AS linea_nombre,

                ci.categoria_id,

                cc.nombre AS categoria_nombre,

                ci.producto_id,

                ci.codigo,

                ci.tipo_item,

                ci.nombre,

                ci.descripcion,

                COALESCE(
                    NULLIF(ci.imagen_url, ''),
                    p.imagen_url
                ) AS imagen_url,

                ci.activo,

                ci.destacado,

                ci.orden,

                mc.permite_personalizar

            FROM {CATALOGO_ITEMS} ci

            INNER JOIN {CATALOGO_LINEAS} cl
                ON cl.id = ci.linea_id

            LEFT JOIN {CATALOGO_CATEGORIAS} cc
                ON cc.id = ci.categoria_id

            LEFT JOIN {PRODUCTOS} p
                ON p.id = ci.producto_id

            LEFT JOIN {MENU_CONFIGURACIONES} mc
                ON mc.catalogo_item_id = ci.id

            WHERE ci.id = {ph}
            """,
            (item_id,)
        )

        item = _row_dict(cursor)

        if not item:
            return None

        active_filter = (
            ""
            if incluir_precios_inactivos
            else f"AND activo = {_true_sql()}"
        )

        cursor.execute(
            f"""
            SELECT
                id,
                tipo_servicio,
                precio,
                activo,
                fecha_modificacion

            FROM {CATALOGO_PRECIOS}

            WHERE catalogo_item_id = {ph}

            {active_filter}

            ORDER BY CASE tipo_servicio

                WHEN 'GENERAL' THEN 1

                WHEN 'MESA' THEN 2

                WHEN 'LLEVAR' THEN 3

                WHEN 'DOMICILIO' THEN 4

                ELSE 5

            END
            """,
            (item_id,)
        )

        item["precios"] = _rows_dict(cursor)

        return item

    finally:

        conn.close()


def _normalizar_item(data, current=None):

    current = current or {}

    line_id = _int(
        data.get("linea_id", current.get("linea_id")),
        "linea_id",
        required=True
    )

    category_id = _int(
        data.get("categoria_id", current.get("categoria_id")),
        "categoria_id"
    )

    product_id = _int(
        data.get("producto_id", current.get("producto_id")),
        "producto_id"
    )

    item_type = str(
        data.get(
            "tipo_item",
            current.get("tipo_item", "PRODUCTO")
        ) or ""
    ).strip().upper()

    if item_type not in TIPOS_ITEM:

        raise CatalogoValidationError(
            "tipo_item debe ser PRODUCTO, MENU o COMBO."
        )

    code = _text(
        data.get("codigo", current.get("codigo")),
        "codigo",
        80,
        True
    ).upper()

    name = _text(
        data.get("nombre", current.get("nombre")),
        "nombre",
        150,
        item_type != "PRODUCTO"
    )

    description = _text(
        data.get("descripcion", current.get("descripcion")),
        "descripcion",
        500
    )

    image_url = _text(
        data.get("imagen_url", current.get("imagen_url")),
        "imagen_url",
        1000
    )

    active = _bool(
        data.get("activo", current.get("activo")),
        True
    )

    featured = _bool(
        data.get("destacado", current.get("destacado")),
        False
    )

    order = _int(
        data.get("orden", current.get("orden", 0)),
        "orden",
        minimum=0
    )

    return {

        "linea_id": line_id,

        "categoria_id": category_id,

        "producto_id": product_id,

        "tipo_item": item_type,

        "codigo": code,

        "nombre": name,

        "descripcion": description,

        "imagen_url": image_url,

        "activo": active,

        "destacado": featured,

        "orden": order

    }


def _validar_vinculo_producto(cursor, item, ph):

    if item["tipo_item"] == "PRODUCTO":

        if not item["producto_id"]:

            raise CatalogoValidationError(
                "Los artículos tipo PRODUCTO deben vincularse con un producto existente."
            )

        product = _get_product(
            cursor,
            item["producto_id"],
            ph
        )

        if not item["nombre"]:
            item["nombre"] = product["nombre"]

        if not item["imagen_url"]:
            item["imagen_url"] = product["imagen_url"]

    elif item["producto_id"] is not None:

        raise CatalogoValidationError(
            "Los artículos tipo MENU o COMBO no deben vincularse directamente a un producto."
        )

    elif not item["nombre"]:

        raise CatalogoValidationError(
            "El nombre del menú o combo es obligatorio."
        )

    return item


def crear_item_catalogo(data):

    if not isinstance(data, dict):

        raise CatalogoValidationError(
            "Los datos del artículo no son válidos."
        )

    is_postgres, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        item = _normalizar_item(data)

        _assert_line_and_category(
            cursor,
            item["linea_id"],
            item["categoria_id"],
            ph
        )

        _assert_unique_code(
            cursor,
            CATALOGO_ITEMS,
            item["linea_id"],
            item["codigo"],
            ph
        )

        _validar_vinculo_producto(
            cursor,
            item,
            ph
        )

        columns = """
            linea_id,
            categoria_id,
            producto_id,
            codigo,
            tipo_item,
            nombre,
            descripcion,
            imagen_url,
            activo,
            destacado,
            orden
        """

        values = ", ".join([ph] * 11)

        params = tuple(
            item[key]
            for key in (
                "linea_id",
                "categoria_id",
                "producto_id",
                "codigo",
                "tipo_item",
                "nombre",
                "descripcion",
                "imagen_url",
                "activo",
                "destacado",
                "orden"
            )
        )

        if is_postgres:

            cursor.execute(
                f"""
                INSERT INTO {CATALOGO_ITEMS}
                    ({columns})

                VALUES ({values})

                RETURNING id
                """,
                params
            )

        else:

            cursor.execute(
                f"""
                INSERT INTO {CATALOGO_ITEMS}
                    ({columns})

                OUTPUT INSERTED.id

                VALUES ({values})
                """,
                params
            )

        item_id = int(cursor.fetchone()[0])

        if item["tipo_item"] in {"MENU", "COMBO"}:

            cursor.execute(
                f"""
                INSERT INTO {MENU_CONFIGURACIONES}
                    (
                        catalogo_item_id,
                        permite_personalizar,
                        activo
                    )

                VALUES ({ph}, {ph}, {ph})
                """,
                (
                    item_id,
                    _bool(data.get("permite_personalizar"), True),
                    item["activo"]
                )
            )

        conn.commit()

        return {

            "id": item_id,

            "message": "Artículo comercial creado correctamente."

        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def actualizar_item_catalogo(item_id, data):

    item_id = _int(
        item_id,
        "item_id",
        required=True
    )

    if not isinstance(data, dict) or not data:

        raise CatalogoValidationError(
            "No se enviaron datos para actualizar el artículo."
        )

    _, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        current = _get_item(
            cursor,
            item_id,
            ph
        )

        if not current:

            raise CatalogoValidationError(
                "El artículo comercial no existe."
            )

        item = _normalizar_item(
            data,
            current
        )

        _assert_line_and_category(
            cursor,
            item["linea_id"],
            item["categoria_id"],
            ph
        )

        _assert_unique_code(
            cursor,
            CATALOGO_ITEMS,
            item["linea_id"],
            item["codigo"],
            ph,
            item_id
        )

        _validar_vinculo_producto(
            cursor,
            item,
            ph
        )

        cursor.execute(
            f"""
            UPDATE {CATALOGO_ITEMS}

            SET
                linea_id = {ph},
                categoria_id = {ph},
                producto_id = {ph},
                codigo = {ph},
                tipo_item = {ph},
                nombre = {ph},
                descripcion = {ph},
                imagen_url = {ph},
                activo = {ph},
                destacado = {ph},
                orden = {ph},
                actualizado_en = CURRENT_TIMESTAMP

            WHERE id = {ph}
            """,
            tuple(
                item[key]
                for key in (
                    "linea_id",
                    "categoria_id",
                    "producto_id",
                    "codigo",
                    "tipo_item",
                    "nombre",
                    "descripcion",
                    "imagen_url",
                    "activo",
                    "destacado",
                    "orden"
                )
            ) + (item_id,)
        )

        if item["tipo_item"] in {"MENU", "COMBO"}:

            cursor.execute(
                f"""
                SELECT catalogo_item_id
                FROM {MENU_CONFIGURACIONES}
                WHERE catalogo_item_id = {ph}
                """,
                (item_id,)
            )

            if cursor.fetchone():

                cursor.execute(
                    f"""
                    UPDATE {MENU_CONFIGURACIONES}

                    SET
                        permite_personalizar = {ph},
                        activo = {ph},
                        actualizado_en = CURRENT_TIMESTAMP

                    WHERE catalogo_item_id = {ph}
                    """,
                    (
                        _bool(data.get("permite_personalizar"), True),
                        item["activo"],
                        item_id
                    )
                )

            else:

                cursor.execute(
                    f"""
                    INSERT INTO {MENU_CONFIGURACIONES}
                        (
                            catalogo_item_id,
                            permite_personalizar,
                            activo
                        )

                    VALUES ({ph}, {ph}, {ph})
                    """,
                    (
                        item_id,
                        _bool(data.get("permite_personalizar"), True),
                        item["activo"]
                    )
                )

        else:

            cursor.execute(
                f"""
                UPDATE {MENU_CONFIGURACIONES}

                SET
                    activo = {ph},
                    actualizado_en = CURRENT_TIMESTAMP

                WHERE catalogo_item_id = {ph}
                """,
                (False, item_id)
            )

        conn.commit()

        return {
            "message": "Artículo comercial actualizado correctamente."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def cambiar_estado_item_catalogo(item_id, activo):

    item_id = _int(
        item_id,
        "item_id",
        required=True
    )

    _, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT id
            FROM {CATALOGO_ITEMS}
            WHERE id = {ph}
            """,
            (item_id,)
        )

        if not cursor.fetchone():

            raise CatalogoValidationError(
                "El artículo comercial no existe."
            )

        active = _bool(activo)

        cursor.execute(
            f"""
            UPDATE {CATALOGO_ITEMS}

            SET
                activo = {ph},
                actualizado_en = CURRENT_TIMESTAMP

            WHERE id = {ph}
            """,
            (active, item_id)
        )

        cursor.execute(
            f"""
            UPDATE {MENU_CONFIGURACIONES}

            SET
                activo = {ph},
                actualizado_en = CURRENT_TIMESTAMP

            WHERE catalogo_item_id = {ph}
            """,
            (active, item_id)
        )

        conn.commit()

        return {
            "message": "Estado del artículo actualizado correctamente."
        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


# =====================================================
# PRECIOS Y AUDITORIA
# =====================================================

def obtener_precios_catalogo(
    item_id,
    incluir_inactivos=False
):

    item_id = _int(
        item_id,
        "item_id",
        required=True
    )

    _, ph = _settings()

    active_filter = (
        ""
        if incluir_inactivos
        else f"AND activo = {_true_sql()}"
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT id
            FROM {CATALOGO_ITEMS}
            WHERE id = {ph}
            """,
            (item_id,)
        )

        if not cursor.fetchone():

            raise CatalogoValidationError(
                "El artículo comercial no existe."
            )

        cursor.execute(
            f"""
            SELECT

                id,

                catalogo_item_id,

                tipo_servicio,

                precio,

                activo,

                modificado_por,

                fecha_modificacion

            FROM {CATALOGO_PRECIOS}

            WHERE catalogo_item_id = {ph}

            {active_filter}

            ORDER BY CASE tipo_servicio

                WHEN 'GENERAL' THEN 1

                WHEN 'MESA' THEN 2

                WHEN 'LLEVAR' THEN 3

                WHEN 'DOMICILIO' THEN 4

                ELSE 5

            END
            """,
            (item_id,)
        )

        return _rows_dict(cursor)

    finally:

        conn.close()


def guardar_precios_catalogo(
    item_id,
    precios,
    usuario_id
):

    item_id = _int(
        item_id,
        "item_id",
        required=True
    )

    usuario_id = _int(
        usuario_id,
        "usuario_id",
        required=True
    )

    if not isinstance(precios, list) or not precios:

        raise CatalogoValidationError(
            "Debes enviar al menos un precio para guardar."
        )

    prepared = []
    seen = set()

    for entry in precios:

        if not isinstance(entry, dict):

            raise CatalogoValidationError(
                "Cada precio debe ser un objeto válido."
            )

        service_type = str(
            entry.get("tipo_servicio") or ""
        ).strip().upper()

        if service_type not in TIPOS_SERVICIO:

            raise CatalogoValidationError(
                "La modalidad debe ser GENERAL, MESA, LLEVAR o DOMICILIO."
            )

        if service_type in seen:

            raise CatalogoValidationError(
                f"La modalidad {service_type} está repetida."
            )

        seen.add(service_type)

        prepared.append((

            service_type,

            _price(entry.get("precio")),

            _bool(entry.get("activo"), True),

            _text(entry.get("motivo"), "motivo", 300)

        ))

    is_postgres, ph = _settings()

    conn = get_connection()

    changes = 0

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT id
            FROM {CATALOGO_ITEMS}
            WHERE id = {ph}
            """,
            (item_id,)
        )

        if not cursor.fetchone():

            raise CatalogoValidationError(
                "El artículo comercial no existe."
            )

        for (
            service_type,
            new_price,
            active,
            reason
        ) in prepared:

            # =====================================
            # BLOQUEAR REGISTRO EXISTENTE
            # =====================================

            if is_postgres:

                query = f"""
                    SELECT id, precio, activo
                    FROM {CATALOGO_PRECIOS}
                    WHERE catalogo_item_id = {ph}
                      AND tipo_servicio = {ph}
                    FOR UPDATE
                """

            else:

                query = f"""
                    SELECT id, precio, activo
                    FROM {CATALOGO_PRECIOS} WITH (UPDLOCK, HOLDLOCK)
                    WHERE catalogo_item_id = {ph}
                      AND tipo_servicio = {ph}
                """

            cursor.execute(
                query,
                (item_id, service_type)
            )

            existing = cursor.fetchone()

            if existing:

                price_id = int(existing[0])

                old_price = Decimal(
                    str(existing[1])
                )

                cursor.execute(
                    f"""
                    UPDATE {CATALOGO_PRECIOS}

                    SET
                        precio = {ph},
                        activo = {ph},
                        modificado_por = {ph},
                        fecha_modificacion = CURRENT_TIMESTAMP

                    WHERE id = {ph}
                    """,
                    (
                        new_price,
                        active,
                        usuario_id,
                        price_id
                    )
                )

            else:

                old_price = None

                columns = """
                    catalogo_item_id,
                    tipo_servicio,
                    precio,
                    activo,
                    modificado_por
                """

                values = ", ".join([ph] * 5)

                params = (
                    item_id,
                    service_type,
                    new_price,
                    active,
                    usuario_id
                )

                if is_postgres:

                    cursor.execute(
                        f"""
                        INSERT INTO {CATALOGO_PRECIOS}
                            ({columns})

                        VALUES ({values})

                        RETURNING id
                        """,
                        params
                    )

                else:

                    cursor.execute(
                        f"""
                        INSERT INTO {CATALOGO_PRECIOS}
                            ({columns})

                        OUTPUT INSERTED.id

                        VALUES ({values})
                        """,
                        params
                    )

                price_id = int(
                    cursor.fetchone()[0]
                )

            # =====================================
            # REGISTRAR HISTORIAL
            # =====================================

            if old_price is None or old_price != new_price:

                cursor.execute(
                    f"""
                    INSERT INTO {CATALOGO_PRECIOS_HISTORIAL}
                    (
                        catalogo_precio_id,
                        catalogo_item_id,
                        tipo_servicio,
                        precio_anterior,
                        precio_nuevo,
                        motivo,
                        usuario_id
                    )

                    VALUES (
                        {ph},
                        {ph},
                        {ph},
                        {ph},
                        {ph},
                        {ph},
                        {ph}
                    )
                    """,
                    (
                        price_id,
                        item_id,
                        service_type,
                        old_price,
                        new_price,
                        reason,
                        usuario_id
                    )
                )

                changes += 1

        conn.commit()

        return {

            "message": "Precios guardados correctamente.",

            "precios_modificados": changes

        }

    except Exception:

        conn.rollback()

        raise

    finally:

        conn.close()


def obtener_historial_precios(item_id, limit=100):

    item_id = _int(
        item_id,
        "item_id",
        required=True
    )

    limit = min(
        _int(limit or 100, "limit", minimum=1),
        500
    )

    is_postgres, ph = _settings()

    query = f"""
        SELECT

            h.id,

            h.catalogo_precio_id,

            h.catalogo_item_id,

            ci.nombre AS articulo,

            h.tipo_servicio,

            h.precio_anterior,

            h.precio_nuevo,

            h.motivo,

            h.usuario_id,

            u.nombre AS usuario,

            h.fecha_cambio

        FROM {CATALOGO_PRECIOS_HISTORIAL} h

        INNER JOIN {CATALOGO_ITEMS} ci
            ON ci.id = h.catalogo_item_id

        INNER JOIN {USUARIOS} u
            ON u.id = h.usuario_id

        WHERE h.catalogo_item_id = {ph}

        ORDER BY
            h.fecha_cambio DESC,
            h.id DESC
    """

    query += (
        f" LIMIT {ph}"
        if is_postgres
        else f" OFFSET 0 ROWS FETCH NEXT {ph} ROWS ONLY"
    )

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            query,
            (item_id, limit)
        )

        return _rows_dict(cursor)

    finally:

        conn.close()


# =====================================================
# RESOLVER PRECIO VIGENTE
# =====================================================

def resolver_precio_catalogo(
    item_id,
    tipo_servicio="GENERAL"
):

    item_id = _int(
        item_id,
        "item_id",
        required=True
    )

    service_type = str(
        tipo_servicio or "GENERAL"
    ).strip().upper()

    if service_type not in TIPOS_SERVICIO:

        raise CatalogoValidationError(
            "La modalidad de servicio no es válida."
        )

    _, ph = _settings()

    conn = get_connection()

    try:

        cursor = conn.cursor()

        cursor.execute(
            f"""
            SELECT

                cp.tipo_servicio,

                cp.precio

            FROM {CATALOGO_PRECIOS} cp

            INNER JOIN {CATALOGO_ITEMS} ci
                ON ci.id = cp.catalogo_item_id

            INNER JOIN {CATALOGO_LINEAS} cl
                ON cl.id = ci.linea_id

            LEFT JOIN {PRODUCTOS} p
                ON p.id = ci.producto_id

            WHERE cp.catalogo_item_id = {ph}

              AND ci.activo = {_true_sql()}

              AND cl.activo = {_true_sql()}

              AND (
                    ci.producto_id IS NULL
                    OR p.activo = 1
              )

              AND cp.activo = {_true_sql()}

              AND cp.tipo_servicio IN (
                    {ph},
                    'GENERAL'
              )

            ORDER BY CASE
                WHEN cp.tipo_servicio = {ph} THEN 0
                ELSE 1
            END
            """,
            (
                item_id,
                service_type,
                service_type
            )
        )

        row = cursor.fetchone()

        if not row:
            return None

        return {

            "catalogo_item_id": item_id,

            "tipo_servicio": row[0],

            "precio": float(row[1])

        }

    finally:

        conn.close()
