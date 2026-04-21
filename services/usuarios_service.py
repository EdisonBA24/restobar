from database.connection import get_connection


# =============================
# CREAR USUARIO
# =============================
def crear_usuario(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            INSERT INTO usuarios (nombre, usuario, password, perfil, activo)
            VALUES (?, ?, ?, ?, 1)
        """, (
            data["nombre"],
            data["usuario"],
            data["password"],
            data["perfil"]
        ))

        conn.commit()

        return {"message": "Usuario creado correctamente"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR CREANDO USUARIO:", e)
        raise e

    finally:
        conn.close()


# =============================
# CONSULTAR USUARIOS
# =============================
def get_usuarios():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, nombre, usuario, perfil, activo
        FROM usuarios
        ORDER BY id DESC
    """)

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data


# =============================
# ACTUALIZAR USUARIO
# =============================
def update_usuario(id, data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            UPDATE usuarios
            SET nombre = ?, usuario = ?, password = ?, perfil = ?, activo = ?
            WHERE id = ?
        """, (
            data["nombre"],
            data["usuario"],
            data["password"],
            data["perfil"],
            data["activo"],
            id
        ))

        conn.commit()

        return {"message": "Usuario actualizado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR ACTUALIZANDO USUARIO:", e)
        raise e

    finally:
        conn.close()


def activar_usuario(id, activo):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE usuarios
        SET activo = ?
        WHERE id = ?
    """, (activo, id))

    conn.commit()
    conn.close()