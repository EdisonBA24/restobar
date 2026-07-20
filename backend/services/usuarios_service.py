from database.connection import get_connection
from config import Config
from database.db_objects import USUARIOS
from werkzeug.security import generate_password_hash


# =============================
# 📋 LISTA SIMPLE DE USUARIOS
# =============================
def get_usuarios_select():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(f"""
            SELECT
                id,
                nombre
            FROM {USUARIOS}
            WHERE activo = 1
            ORDER BY nombre
        """)

        columns = [c[0] for c in cursor.description]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    except Exception as e:
        print("❌ ERROR LISTA USUARIOS:", e)
        raise

    finally:
        conn.close()


# =============================
# CREAR USUARIO
# =============================
def crear_usuario(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if not data.get("nombre") or not data.get("usuario"):
            raise Exception("Nombre y usuario son obligatorios")

        if not data.get("password"):
            raise Exception("Password requerido")

        # 🔥 MOTOR
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        # 🔥 VALIDAR USUARIO ÚNICO
        cursor.execute(f"""
            SELECT id FROM {USUARIOS} WHERE usuario = {placeholder}
        """, (data["usuario"],))

        if cursor.fetchone():
            raise Exception("El usuario ya existe")

        # 🔐 HASH PASSWORD
        password_hash = generate_password_hash(data["password"])

        cursor.execute(f"""
            INSERT INTO {USUARIOS} (nombre, usuario, password, perfil, activo)
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, 1)
        """, (
            data["nombre"],
            data["usuario"],
            password_hash,
            data.get("perfil", "ventas")
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

    try:
        cursor.execute(f"""
            SELECT id, nombre, usuario, perfil, activo
            FROM {USUARIOS}
            ORDER BY id DESC
        """)

        columns = [c[0] for c in cursor.description]

        data = []
        for r in cursor.fetchall():
            data.append(dict(zip(columns, r)))

        return data

    finally:
        conn.close()


# =============================
# ACTUALIZAR USUARIO
# =============================
def update_usuario(id, data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        if not data.get("nombre") or not data.get("usuario"):
            raise Exception("Nombre y usuario son obligatorios")

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        # 🔥 VALIDAR USUARIO ÚNICO (excepto él mismo)
        cursor.execute(f"""
            SELECT id FROM {USUARIOS}
            WHERE usuario = {placeholder} AND id != {placeholder}
        """, (data["usuario"], id))

        if cursor.fetchone():
            raise Exception("El usuario ya existe")

        # 🔐 solo actualizar password si viene
        password = data.get("password")

        if password:
            password_hash = generate_password_hash(password)

            query = f"""
                UPDATE {USUARIOS}
                SET nombre = {placeholder}, usuario = {placeholder}, password = {placeholder}, perfil = {placeholder}, activo = {placeholder}
                WHERE id = {placeholder}
            """

            params = (
                data["nombre"],
                data["usuario"],
                password_hash,
                data.get("perfil"),
                data.get("activo"),
                id
            )

        else:
            # 🔥 no tocar password
            query = f"""
                UPDATE {USUARIOS}
                SET nombre = {placeholder}, usuario = {placeholder}, perfil = {placeholder}, activo = {placeholder}
                WHERE id = {placeholder}
            """

            params = (
                data["nombre"],
                data["usuario"],
                data.get("perfil"),
                data.get("activo"),
                id
            )

        cursor.execute(query, params)

        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ Usuario no encontrado")

        return {"message": "Usuario actualizado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR ACTUALIZANDO USUARIO:", e)
        raise e

    finally:
        conn.close()


# =============================
# ACTIVAR / DESACTIVAR
# =============================
def activar_usuario(id, activo):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        cursor.execute(f"""
            UPDATE {USUARIOS}
            SET activo = {placeholder}
            WHERE id = {placeholder}
        """, (activo, id))

        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ Usuario no encontrado")

    except Exception as e:
        conn.rollback()
        print("❌ ERROR ACTIVAR USUARIO:", e)
        raise e

    finally:
        conn.close()