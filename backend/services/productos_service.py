from database.connection import get_connection
from decimal import Decimal
from config import Config
from database.db_objects import PRODUCTOS, UNIDADES_MEDIDA
from constants.category import (
    SOPA,
    PROTEINA,
    SECO,
    ENSALADA,
    JUGO,
    CATEGORIAS_ALMUERZO
)


# =============================
# 🔥 ENGINE SAFE (FIX ERROR)
# =============================
def _get_engine():
    try:
        return getattr(Config, "DB_ENGINE")
    except:
        import os
        return os.environ.get("DB_ENGINE", "sqlserver")


DB_ENGINE = _get_engine()


# =============================
# HELPERS
# =============================
def _to_decimal(value, default=0):
    try:
        if value is None or str(value).strip() == "":
            return Decimal(default)
        return Decimal(str(value))
    except Exception:
        return Decimal(default)


def _to_int(value):
    try:
        if value is None or str(value).strip() == "":
            return None
        return int(value)
    except Exception:
        return None


def _placeholder():
    return "%s" if DB_ENGINE == "postgres" else "?"


# =============================
# DB SETTINGS
# =============================
def _get_db_settings():

    is_postgres = DB_ENGINE == "postgres"

    placeholder = "%s" if is_postgres else "?"

    return is_postgres, placeholder


def _normalizar_valor(valor):
    valor = (valor or "").strip()
    return valor or None


def _buscar_producto_duplicado(cursor, campo, valor, excluir_id=None):
    valor = _normalizar_valor(valor)

    if not valor:
        return None

    placeholder = _placeholder()
    campo_expr = (
        f"LOWER(TRIM(COALESCE({campo}, '')))"
        if DB_ENGINE == "postgres"
        else f"LOWER(LTRIM(RTRIM(ISNULL({campo}, ''))))"
    )

    query = f"""
        SELECT id, nombre
        FROM {PRODUCTOS}
        WHERE {campo_expr} = LOWER({placeholder})
    """
    params = [valor]

    if excluir_id is not None:
        query += f" AND id <> {placeholder}"
        params.append(excluir_id)

    cursor.execute(query, tuple(params))
    return cursor.fetchone()


def _validar_producto_unico(cursor, data, excluir_id=None):
    for campo in ["codigo", "nombre"]:
        duplicado = _buscar_producto_duplicado(
            cursor,
            campo,
            data.get(campo),
            excluir_id
        )

        if duplicado:
            return {
                "status": "error",
                "message": f"Ya existe un producto registrado con ese {campo}",
                "status_code": 409
            }

    return None


def _base_query():

    return f"""
        SELECT
            p.*,
            u.nombre AS unidad_nombre,
            u.abreviatura
        FROM {PRODUCTOS} p
        LEFT JOIN {UNIDADES_MEDIDA} u
            ON p.unidad_id = u.id
    """

# =============================
# GET PRODUCTO
# =============================
def _get_producto(cursor, producto_id):

    placeholder = _placeholder()

    query = f"""
        SELECT
            p.id,
            p.nombre,
            p.codigo,
            p.categoria,
            p.tipo,
            p.unidad_id,
            p.precio_venta,
            p.stock,
            p.activo
        FROM {PRODUCTOS} p
        WHERE p.id = {placeholder}
    """

    cursor.execute(query, (producto_id,))

    row = cursor.fetchone()

    if not row:
        return None

    columns = [
        column[0]
        for column in cursor.description
    ]

    producto = dict(zip(columns, row))

    # =============================
    # NORMALIZACIÓN
    # =============================

    producto["id"] = int(
        producto.get("id") or 0
    )

    producto["unidad_id"] = int(
        producto.get("unidad_id") or 0
    )

    producto["precio_venta"] = float(
        producto.get("precio_venta") or 0
    )

    producto["stock"] = float(
        producto.get("stock") or 0
    )

    return producto

# =============================
# GET PRODUCTO POR ID
# =============================
def get_producto_por_id(producto_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        return _get_producto(
            cursor,
            producto_id
        )

    except Exception as e:

        print(
            "❌ ERROR GET PRODUCTO:",
            e
        )

        raise

    finally:

        conn.close()

# =============================
# GET PRODUCTOS POR CATEGORIA
# =============================
def get_productos_por_categoria(categoria):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        placeholder = _placeholder()

        query = _base_query()

        query += f"""
            WHERE
                p.categoria = {placeholder}
                AND p.activo = 1
            ORDER BY
                p.nombre
        """

        cursor.execute(query, (categoria,))

        columns = [
            column[0]
            for column in cursor.description
        ]

        rows = cursor.fetchall()

        data = []

        for row in rows:

            producto = dict(zip(columns, row))

            producto["id"] = int(
                producto.get("id") or 0
            )

            producto["unidad_id"] = int(
                producto.get("unidad_id") or 0
            )

            producto["precio_venta"] = float(
                producto.get("precio_venta") or 0
            )

            producto["stock"] = float(
                producto.get("stock") or 0
            )

            data.append(producto)

        return data

    except Exception as e:

        print(
            "❌ ERROR PRODUCTOS CATEGORIA:",
            e
        )

        return []

    finally:

        conn.close()

# =============================
# COMPONENTES ALMUERZO
# =============================
def get_componentes_almuerzo():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        query = _base_query()

        query += """
            WHERE
                p.tipo = 'RECETA'
                AND p.activo = 1
            ORDER BY
                p.nombre
        """

        cursor.execute(query)

        columns = [

            column[0]

            for column in cursor.description

        ]

        componentes = {

            "sopas": [],

            "proteinas": [],

            "secos": [],

            "ensaladas": [],

            "jugos": []

        }

        for row in cursor.fetchall():

            producto = dict(zip(columns, row))

            producto["id"] = int(
                producto.get("id") or 0
            )

            producto["unidad_id"] = int(
                producto.get("unidad_id") or 0
            )

            producto["precio_venta"] = float(
                producto.get("precio_venta") or 0
            )

            producto["stock"] = float(
                producto.get("stock") or 0
            )

            categoria = (
                producto.get("categoria") or ""
            ).strip().upper()

            nombre = (
                producto.get("nombre") or ""
            ).strip().upper()

            # =============================
            # SOPAS
            # =============================

            if categoria == "SOPA": #or "SOP" in nombre or "CREM" in nombre:

                componentes["sopas"].append(producto)

                continue

            # =============================
            # PROTEINAS
            # =============================

            if categoria == "PROTEINA": #or "PROT" in nombre:

                componentes["proteinas"].append(producto)

                continue

            # =============================
            # ENSALADAS
            # =============================

            if categoria == "ENSALADA": # or "ENSAL" in nombre:

                componentes["ensaladas"].append(producto)

                continue

            # =============================
            # JUGOS
            # =============================

            if categoria == "JUGO": # or "JUGO" in nombre:

                componentes["jugos"].append(producto)

                continue

            # =============================
            # SECOS
            # =============================

            if categoria == "SECO": # or "ARRO" in nombre:

                componentes["secos"].append(producto)

                continue

        return componentes

    except Exception as e:

        print(
            "❌ ERROR COMPONENTES ALMUERZO:",
            e
        )

        return {

            "sopas": [],

            "proteinas": [],

            "secos": [],

            "ensaladas": [],

            "jugos": []

        }

    finally:

        conn.close()

# =============================
# VALIDAR PRODUCTO CATEGORIA
# =============================
def validar_producto_categoria(producto_id,categoria):

    producto=get_producto_por_id(producto_id)

    if not producto:

        return False

    if not producto["activo"]:

        return False

    if str(producto["tipo"]).upper()!="RECETA":

        return False

    categoria = str(categoria).upper()

    if categoria not in CATEGORIAS_ALMUERZO:
        return False

    if str(producto["categoria"]).upper() != categoria:
        return False

    return True

# =============================
# GET PRODUCTOS
# =============================
def get_all_productos(page=1, limit=10, solo_inactivos=False, search=None, sort_by="id", sort_order="desc"):

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:

        estado = 0 if solo_inactivos else 1

        is_postgres, placeholder = _get_db_settings()

        null_fn = "COALESCE" if is_postgres else "ISNULL"

        # =============================
        # QUERY PRINCIPAL
        # =============================

        query = f"""
            SELECT
                p.*,
                u.nombre AS unidad_nombre,
                u.abreviatura
            FROM {PRODUCTOS} p
            LEFT JOIN {UNIDADES_MEDIDA} u
                ON p.unidad_id = u.id
            WHERE p.activo = {placeholder}
        """

        params = [estado]

        # =============================
        # QUERY TOTAL
        # =============================

        count_query = f"""
            SELECT COUNT(*)
            FROM {PRODUCTOS} p
            WHERE p.activo = {placeholder}
        """

        count_params = [estado]

        # =============================
        # BÚSQUEDA
        # =============================

        if search and str(search).strip():

            like = f"%{search.strip().lower()}%"

            filtro = f"""
                AND (
                    LOWER({null_fn}(p.nombre,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(p.codigo,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(p.categoria,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(p.tipo,'')) LIKE {placeholder}
                )
            """

            query += filtro
            count_query += filtro

            params.extend([like, like, like, like])
            count_params.extend([like, like, like, like])

        # =============================
        # COLUMNAS ORDENABLES
        # =============================

        columnas_validas = {
            "id": "p.id",
            "nombre": "p.nombre",
            "codigo": "p.codigo",
            "stock": "p.stock",
            "categoria": "p.categoria",
            "tipo": "p.tipo",
            "precio_venta": "p.precio_venta",
            "fecha_creacion": "p.fecha_creacion",
            "unidad_nombre": "u.nombre"
        }

        sort_by_request = sort_by

        sort_by = columnas_validas.get(
            sort_by,
            "p.id"
        )

        sort_order = (
            "DESC"
            if str(sort_order).lower() == "desc"
            else "ASC"
        )

        # =============================
        # PAGINACIÓN
        # =============================

        if is_postgres:

            query += f"""
                ORDER BY {sort_by} {sort_order}
                LIMIT {placeholder}
                OFFSET {placeholder}
            """

            params.extend([
                limit,
                offset
            ])

        else:

            query += f"""
                ORDER BY {sort_by} {sort_order}
                OFFSET {placeholder}
                ROWS FETCH NEXT {placeholder} ROWS ONLY
            """

            params.extend([
                offset,
                limit
            ])

        # =============================
        # TOTAL
        # =============================

        cursor.execute(
            count_query,
            count_params
        )

        total = cursor.fetchone()[0]

        total_pages = max(
            (total + limit - 1) // limit,
            1
        )

        # =============================
        # CONSULTA
        # =============================

        cursor.execute(
            query,
            params
        )

        columns = [
            c[0]
            for c in cursor.description
        ]

        data = []

        for row in cursor.fetchall():

            producto = dict(zip(columns, row))

            producto["id"] = int(
                producto.get("id") or 0
            )

            producto["unidad_id"] = int(
                producto.get("unidad_id") or 0
            )

            producto["precio_venta"] = float(
                producto.get("precio_venta") or 0
            )

            producto["stock"] = float(
                producto.get("stock") or 0
            )

            data.append(producto)

        return {
            "items": data,
            "page": page,
            "page_size": limit,
            "total": total,
            "total_pages": total_pages,
            "sort_by": sort_by_request,
            "sort_order": sort_order.lower()
        }

    except Exception as e:

        print("❌ ERROR GET PRODUCTOS:", e)

        return {
            "items": [],
            "page": page,
            "page_size": limit,
            "total": 0,
            "total_pages": 1,
            "sort_by": sort_by,
            "sort_order": sort_order.lower()
        }

    finally:

        conn.close()


# =====================================
# AUTOCOMPLETE PRODUCTOS
# =====================================
def get_productos_autocomplete(
    search=None,
    tipos=None,
    activos=True
):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres, placeholder = _get_db_settings()

        null_fn = "COALESCE" if is_postgres else "ISNULL"

        estado = 1 if activos else 0

        query = _base_query()

        query += f"""
            WHERE
                p.activo = {placeholder}
        """

        params = [estado]

        # =====================================
        # FILTRO SEARCH
        # =====================================

        if search and str(search).strip():

            like = f"%{search.strip().lower()}%"

            query += f"""
                AND (
                    LOWER({null_fn}(p.nombre,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(p.codigo,'')) LIKE {placeholder}
                )
            """

            params.extend([
                like,
                like
            ])

        # =====================================
        # FILTRO TIPOS
        # =====================================

        if tipos:

            if isinstance(tipos, str):

                tipos = [
                    t.strip().upper()
                    for t in tipos.split(",")
                    if t.strip()
                ]

            tipos = [
                str(t).strip().upper()
                for t in tipos
                if str(t).strip()
            ]

            if tipos:

                placeholders = ",".join(
                    [placeholder] * len(tipos)
                )

                query += f"""
                    AND UPPER(p.tipo)
                    IN ({placeholders})
                """

                params.extend(tipos)

        # =====================================
        # ORDEN
        # =====================================

        query += """
            ORDER BY
                p.nombre
        """

        cursor.execute(
            query,
            tuple(params)
        )

        columns = [
            column[0]
            for column in cursor.description
        ]

        data = []

        for row in cursor.fetchall():

            producto = dict(zip(columns, row))

            # =====================================
            # NORMALIZACIÓN
            # =====================================

            producto["id"] = int(
                producto.get("id") or 0
            )

            producto["unidad_id"] = int(
                producto.get("unidad_id") or 0
            )

            producto["precio_venta"] = float(
                producto.get("precio_venta") or 0
            )

            producto["stock"] = float(
                producto.get("stock") or 0
            )

            data.append(producto)

        return data

    except Exception as e:

        print(
            "❌ ERROR AUTOCOMPLETE PRODUCTOS:",
            e
        )

        return []

    finally:

        conn.close()


# =============================
# CREATE
# =============================
def create_producto(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        tipo = data.get("tipo") or "INSUMO"
        unidad_id = _to_int(data.get("unidad_id"))
        precio = _to_decimal(data.get("precio_venta"))
        stock = _to_decimal(data.get("stock"))
        data["codigo"] = _normalizar_valor(data.get("codigo"))
        data["nombre"] = _normalizar_valor(data.get("nombre"))

        duplicado = _validar_producto_unico(cursor, data)
        if duplicado:
            return duplicado

        query = f"""
        INSERT INTO {PRODUCTOS} 
        (nombre, codigo, precio_venta, categoria, unidad_id, activo, tipo, stock, fecha_creacion)
        VALUES (%s, %s, %s, %s, %s, 1, %s, %s, CURRENT_TIMESTAMP)
        """ if DB_ENGINE == "postgres" else f"""
        INSERT INTO {PRODUCTOS} 
        (nombre, codigo, precio_venta, categoria, unidad_id, activo, tipo, stock, fecha_creacion)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?, GETDATE())
        """

        cursor.execute(query, (
            data.get("nombre"),
            data.get("codigo"),
            precio,
            data.get("categoria"),
            unidad_id,
            tipo,
            stock
        ))

        conn.commit()

        return {"message": "Producto creado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR CREATE:", e)
        raise e

    finally:
        conn.close()


# =============================
# UPDATE
# =============================
def update_producto(id, data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        tipo = data.get("tipo") or "INSUMO"
        unidad_id = _to_int(data.get("unidad_id"))
        precio = _to_decimal(data.get("precio_venta"))
        data["codigo"] = _normalizar_valor(data.get("codigo"))
        data["nombre"] = _normalizar_valor(data.get("nombre"))

        duplicado = _validar_producto_unico(cursor, data, excluir_id=id)
        if duplicado:
            return duplicado

        query = f"""
        UPDATE {PRODUCTOS}
        SET nombre=%s, codigo=%s, precio_venta=%s, categoria=%s, unidad_id=%s, tipo=%s
        WHERE id=%s AND activo=1
        """ if DB_ENGINE == "postgres" else f"""
        UPDATE {PRODUCTOS}
        SET nombre=?, codigo=?, precio_venta=?, categoria=?, unidad_id=?, tipo=?
        WHERE id=? AND activo=1
        """

        cursor.execute(query, (
            data.get("nombre"),
            data.get("codigo"),
            precio,
            data.get("categoria"),
            unidad_id,
            tipo,
            id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ UPDATE: sin cambios (ID inválido o inactivo)")

        return {"message": "Producto actualizado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR UPDATE:", e)
        raise e

    finally:
        conn.close()


# =============================
# DELETE (SOFT)
# =============================
def delete_producto(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        query = f"UPDATE {PRODUCTOS} SET activo = 0 WHERE id = %s" if DB_ENGINE == "postgres" else f"UPDATE {PRODUCTOS} SET activo = 0 WHERE id = ?"

        cursor.execute(query, (id,))
        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ DELETE: producto no encontrado")

        return {"message": "Producto desactivado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR DELETE:", e)
        raise e

    finally:
        conn.close()


# =============================
# ACTIVATE
# =============================
def activar_producto(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        placeholder = _placeholder()

        cursor.execute(
            f"SELECT codigo, nombre FROM {PRODUCTOS} WHERE id = {placeholder}",
            (id,)
        )
        producto = cursor.fetchone()

        if not producto:
            return {"status": "error", "message": "Producto no encontrado", "status_code": 404}

        duplicado = _validar_producto_unico(
            cursor,
            {"codigo": producto[0], "nombre": producto[1]},
            excluir_id=id
        )
        if duplicado:
            return duplicado

        query = f"UPDATE {PRODUCTOS} SET activo = 1 WHERE id = %s" if DB_ENGINE == "postgres" else f"UPDATE {PRODUCTOS} SET activo = 1 WHERE id = ?"

        cursor.execute(query, (id,))
        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ ACTIVATE: producto no encontrado")

        return {"message": "Producto activado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR ACTIVATE:", e)
        raise e

    finally:
        conn.close()