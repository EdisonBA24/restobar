from database.connection import get_connection
from config import Config
from werkzeug.security import generate_password_hash


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
            SELECT id FROM usuarios WHERE usuario = {placeholder}
        """, (data["usuario"],))

        if cursor.fetchone():
            raise Exception("El usuario ya existe")

        # 🔐 HASH PASSWORD
        password_hash = generate_password_hash(data["password"])

        cursor.execute(f"""
            INSERT INTO usuarios (nombre, usuario, password, perfil, activo)
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
        cursor.execute("""
            SELECT id, nombre, usuario, perfil, activo
            FROM usuarios
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
            SELECT id FROM usuarios 
            WHERE usuario = {placeholder} AND id != {placeholder}
        """, (data["usuario"], id))

        if cursor.fetchone():
            raise Exception("El usuario ya existe")

        # 🔐 solo actualizar password si viene
        password = data.get("password")

        if password:
            password_hash = generate_password_hash(password)

            query = f"""
                UPDATE usuarios
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
                UPDATE usuarios
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
            UPDATE usuarios
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