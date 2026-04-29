from database.connection import get_connection
from config import Config


def get_all_clientes(page=1, limit=10, solo_inactivos=False, search=None):

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:
        estado = 0 if solo_inactivos else 1

        # 🔥 FIX CLAVE: evitar error si no existe DB_ENGINE
        db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
        is_postgres = db_engine == "postgres"

        # 🔥 funciones compatibles
        null_fn = "COALESCE" if is_postgres else "ISNULL"
        placeholder = "%s" if is_postgres else "?"

        query = f"""
        SELECT *
        FROM clientes
        WHERE activo = {placeholder}
        """

        params = [estado]

        if search and str(search).strip() != "":
            like = f"%{search.lower()}%"

            query += f"""
            AND (
                LOWER({null_fn}(nombre, '')) LIKE {placeholder} OR
                LOWER({null_fn}(documento, '')) LIKE {placeholder} OR
                LOWER({null_fn}(telefono, '')) LIKE {placeholder} OR
                LOWER({null_fn}(direccion, '')) LIKE {placeholder}
            )
            """

            params.extend([like, like, like, like])

        # 🔥 paginación compatible
        if is_postgres:
            query += f"""
            ORDER BY id DESC
            LIMIT {placeholder} OFFSET {placeholder}
            """
            params.extend([limit, offset])
        else:
            query += f"""
            ORDER BY id DESC
            OFFSET {placeholder} ROWS FETCH NEXT {placeholder} ROWS ONLY
            """
            params.extend([offset, limit])

        cursor.execute(query, params)

        columns = [column[0] for column in cursor.description]

        data = []
        for row in cursor.fetchall():
            r = dict(zip(columns, row))

            # 🔥 NORMALIZACIÓN (evita errores en frontend)
            r["id"] = int(r.get("id") or 0)

            data.append(r)

        return data

    except Exception as e:
        print("❌ ERROR GET CLIENTES:", e)
        return []

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

        db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
        is_postgres = db_engine == "postgres"
        placeholder = "%s" if is_postgres else "?"

        cursor.execute(f"""
            INSERT INTO clientes (nombre, documento, telefono, direccion, usuario_id, activo)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, 1)
        """, (
            data.get("nombre"),
            data.get("documento"),
            data.get("telefono"),
            data.get("direccion"),
            data.get("usuario_id") or 1
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
        db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
        is_postgres = db_engine == "postgres"
        placeholder = "%s" if is_postgres else "?"

        cursor.execute(f"""
            UPDATE clientes
            SET nombre={placeholder}, documento={placeholder}, telefono={placeholder}, direccion={placeholder}
            WHERE id={placeholder} AND activo=1
        """, (
            data.get("nombre"),
            data.get("documento"),
            data.get("telefono"),
            data.get("direccion"),
            id
        ))

        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ UPDATE CLIENTE: sin cambios")

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
        db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
        placeholder = "%s" if db_engine == "postgres" else "?"

        cursor.execute(f"UPDATE clientes SET activo = 0 WHERE id = {placeholder}", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ DELETE CLIENTE: no encontrado")

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
        db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
        placeholder = "%s" if db_engine == "postgres" else "?"

        cursor.execute(f"UPDATE clientes SET activo = 1 WHERE id = {placeholder}", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ ACTIVATE CLIENTE: no encontrado")

        return {"status": "success", "message": "Cliente activado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR ACTIVATE CLIENTE:", e)

        return {"status": "error", "message": str(e)}

    finally:
        conn.close()