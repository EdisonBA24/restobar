from database.connection import get_connection
import hashlib
from werkzeug.security import generate_password_hash  # 🔥 NUEVO

# 🔧 Se mantiene tu función (no se elimina)
def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

conn = get_connection()
cursor = conn.cursor()

# 🔥 PASSWORD ORIGINAL
raw_password = "Admin123*"

# 🔥 HASH SEGURO (el que usa Flask login)
password = generate_password_hash(raw_password)

# 🔥 DEBUG OPCIONAL (no afecta)
print("🔐 HASH GENERADO:", password)

# 🔥 EVITAR DUPLICADOS (MEJORA)
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