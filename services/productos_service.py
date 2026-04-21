from database.connection import get_connection
from decimal import Decimal


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


def _base_query():
    return """
        SELECT p.*, u.nombre AS unidad_nombre, u.abreviatura
        FROM productos p
        LEFT JOIN unidades_medida u ON p.unidad_id = u.id
    """


# =============================
# GET PRODUCTOS
# =============================
def get_all_productos(page=1, limit=10, solo_inactivos=False, search=None):

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:
        estado = 0 if solo_inactivos else 1

        query = """
        SELECT p.*, u.nombre AS unidad_nombre, u.abreviatura
        FROM productos p
        LEFT JOIN unidades_medida u ON p.unidad_id = u.id
        WHERE p.activo = ?
        """

        params = [estado]

        # 🔥 FIX REAL: validar correctamente search
        if search and str(search).strip() != "":
            query += """
            AND (
                LOWER(ISNULL(p.nombre, '')) LIKE ? OR
                LOWER(ISNULL(p.codigo, '')) LIKE ? OR
                LOWER(ISNULL(p.categoria, '')) LIKE ? OR
                LOWER(ISNULL(p.tipo, '')) LIKE ?
            )
            """
            like = f"%{search.lower()}%"
            params.extend([like, like, like, like])

        query += """
        ORDER BY p.id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        params.extend([offset, limit])

        cursor.execute(query, params)

        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

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

        query = """
        INSERT INTO productos 
        (nombre, codigo, precio_venta, categoria, unidad_id, activo, tipo, stock)
        VALUES (?, ?, ?, ?, ?, 1, ?, ?)
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

        query = """
        UPDATE productos
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
        cursor.execute(
            "UPDATE productos SET activo = 0 WHERE id = ?",
            (id,)
        )

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
        cursor.execute(
            "UPDATE productos SET activo = 1 WHERE id = ?",
            (id,)
        )

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