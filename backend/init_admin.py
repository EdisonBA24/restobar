from database.connection import get_connection
import hashlib
from werkzeug.security import generate_password_hash


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def init_admin():
    conn = get_connection()
    cursor = conn.cursor()

    raw_password = "Admin123*"
    password = generate_password_hash(raw_password)

    print("🔐 HASH GENERADO:", password)

    cursor.execute("SELECT id FROM usuarios WHERE usuario = ?", ("admin",))
    existing = cursor.fetchone()

    if existing:
        print("⚠️ El usuario admin ya existe, se actualizará password...")

        cursor.execute("""
            UPDATE usuarios
            SET password = ?, nombre = ?, perfil = ?, activo = 1
            WHERE usuario = ?
        """, (
            password,
            "Administrador",
            "admin",
            "admin"
        ))

    else:
        cursor.execute("""
            INSERT INTO usuarios (nombre, usuario, password, perfil, activo)
            VALUES (?, ?, ?, ?, 1)
        """, (
            "Administrador",
            "admin",
            password,
            "admin"
        ))

    conn.commit()
    conn.close()

    print("✅ Admin listo: admin / Admin123*")


# 👇 SOLO SE EJECUTA SI LLAMAS LA FUNCIÓN
if __name__ == "__main__":
    init_admin()