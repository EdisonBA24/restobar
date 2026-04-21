from database.connection import get_connection


def get_all_clientes(page=1, limit=10, solo_inactivos=False, search=None):

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:
        estado = 0 if solo_inactivos else 1

        query = """
        SELECT *
        FROM clientes
        WHERE activo = ?
        """

        params = [estado]

        if search and str(search).strip() != "":
            query += """
            AND (
                LOWER(ISNULL(nombre, '')) LIKE ? OR
                LOWER(ISNULL(documento, '')) LIKE ? OR
                LOWER(ISNULL(telefono, '')) LIKE ? OR
                LOWER(ISNULL(direccion, '')) LIKE ?
            )
            """
            like = f"%{search.lower()}%"
            params.extend([like, like, like, like])

        query += """
        ORDER BY id DESC
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """

        params.extend([offset, limit])

        cursor.execute(query, params)

        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return data

    finally:
        conn.close()


# =============================
# CREATE
# =============================
def create_cliente(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("📥 DATA CLIENTE:", data)

        cursor.execute("""
            INSERT INTO clientes (nombre, documento, telefono, direccion, usuario_id, activo)
            VALUES (?, ?, ?, ?, ?, 1)
        """, (
            data.get("nombre"),
            data.get("documento"),
            data.get("telefono"),
            data.get("direccion"),
            data.get("usuario_id") or 1  # 🔥 FIX
        ))

        conn.commit()

        print("✅ CLIENTE INSERTADO")

        return {"status": "success", "message": "Cliente creado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR CREATE CLIENTE:", e)
        return {"status": "error", "message": str(e)}

    finally:
        conn.close()


# =============================
# UPDATE
# =============================
def update_cliente(id, data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            UPDATE clientes
            SET nombre=?, documento=?, telefono=?, direccion=?
            WHERE id=? AND activo=1
        """, (
            data.get("nombre"),
            data.get("documento"),
            data.get("telefono"),
            data.get("direccion"),
            id
        ))

        conn.commit()

        return {"status": "success", "message": "Cliente actualizado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR UPDATE CLIENTE:", e)
        return {"status": "error", "message": str(e)}

    finally:
        conn.close()


# =============================
# DELETE
# =============================
def delete_cliente(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE clientes SET activo = 0 WHERE id = ?", (id,))
        conn.commit()

        return {"status": "success", "message": "Cliente desactivado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR DELETE CLIENTE:", e)
        return {"status": "error", "message": str(e)}

    finally:
        conn.close()


# =============================
# ACTIVATE
# =============================
def activar_cliente(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("UPDATE clientes SET activo = 1 WHERE id = ?", (id,))
        conn.commit()

        return {"status": "success", "message": "Cliente activado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR ACTIVATE CLIENTE:", e)
        return {"status": "error", "message": str(e)}

    finally:
        conn.close()