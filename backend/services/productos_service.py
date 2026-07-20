from database.connection import get_connection
from decimal import Decimal
from config import Config
from database.db_objects import PRODUCTOS, UNIDADES_MEDIDA


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
        SELECT p.*, u.nombre AS unidad_nombre, u.abreviatura
        FROM {PRODUCTOS} p
        LEFT JOIN {UNIDADES_MEDIDA} u ON p.unidad_id = u.id
    """


# =============================
# GET PRODUCTOS
# =============================
def get_all_productos(page=1, limit=10, solo_inactivos=False, search=None):

    # 🔥 HARDENING
    page = max(int(page), 1)
    limit = max(int(limit), 1)
    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:
        estado = 0 if solo_inactivos else 1

        # 🔥 BASE SEGÚN MOTOR
        if DB_ENGINE == "postgres":
            query = f"""
            SELECT p.*, u.nombre AS unidad_nombre, u.abreviatura
            FROM {PRODUCTOS} p
            LEFT JOIN {UNIDADES_MEDIDA} u ON p.unidad_id = u.id
            WHERE p.activo = %s
            """
        else:
            query = f"""
            SELECT p.*, u.nombre AS unidad_nombre, u.abreviatura
            FROM {PRODUCTOS} p
            LEFT JOIN {UNIDADES_MEDIDA} u ON p.unidad_id = u.id
            WHERE p.activo = ?
            """

        params = [estado]

        # =============================
        # 🔍 SEARCH
        # =============================
        if search and str(search).strip() != "":
            search = str(search).strip().lower()

            if DB_ENGINE == "postgres":
                query += """
                AND (
                    LOWER(COALESCE(p.nombre, '')) LIKE %s OR
                    LOWER(COALESCE(p.codigo, '')) LIKE %s OR
                    LOWER(COALESCE(p.categoria, '')) LIKE %s OR
                    LOWER(COALESCE(p.tipo, '')) LIKE %s
                )
                """
            else:
                query += """
                AND (
                    LOWER(ISNULL(p.nombre, '')) LIKE ? OR
                    LOWER(ISNULL(p.codigo, '')) LIKE ? OR
                    LOWER(ISNULL(p.categoria, '')) LIKE ? OR
                    LOWER(ISNULL(p.tipo, '')) LIKE ?
                )
                """

            like = f"%{search}%"
            params.extend([like, like, like, like])

        # =============================
        # 📄 PAGINACIÓN
        # =============================
        if DB_ENGINE == "postgres":
            query += " ORDER BY p.id DESC LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        else:
            query += " ORDER BY p.id DESC OFFSET ? ROWS FETCH NEXT ? ROWS ONLY"
            params.extend([offset, limit])

        cursor.execute(query, tuple(params))

        columns = [column[0] for column in cursor.description]

        data = []
        for row in cursor.fetchall():
            r = dict(zip(columns, row))

            # 🔥 NORMALIZACIÓN SEGURA
            r["precio_venta"] = float(r.get("precio_venta") or 0)
            r["stock"] = float(r.get("stock") or 0)

            data.append(r)

        return data

    except Exception as e:
        print("❌ ERROR GET PRODUCTOS:", e)
        raise e

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
