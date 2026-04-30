from config import Config
import os

# =============================
# 🔥 DETECTAR ENGINE
# =============================
DB_ENGINE = (
    os.environ.get("DB_ENGINE") or
    getattr(Config, "DB_ENGINE", "sqlserver")
).lower()


# =============================
# 🔥 POSTGRES (RENDER / SUPABASE)
# =============================
def get_postgres_connection():
    import psycopg2

    try:
        return psycopg2.connect(
            host=os.environ.get("DB_HOST", Config.DB_HOST),
            database=os.environ.get("DB_NAME", Config.DB_NAME),
            user=os.environ.get("DB_USER", Config.DB_USER),
            password=os.environ.get("DB_PASSWORD", Config.DB_PASSWORD),
            port=os.environ.get("DB_PORT", Config.DB_PORT),
            sslmode="require"
        )
    except Exception as e:
        print("❌ ERROR REAL DB (POSTGRES):", e)
        raise e


# =============================
# 🔥 SQL SERVER (LOCAL)
# =============================
def get_sqlserver_connection():
    import pyodbc

    try:
        conn = pyodbc.connect(Config.get_connection_string())
        return conn
    except Exception as e:
        print("❌ ERROR REAL DB (SQL SERVER):", e)
        raise e


# =============================
# 🔥 CONEXIÓN UNIFICADA
# =============================
def get_connection():

    try:
        print(f"🔌 DB_ENGINE detectado: {DB_ENGINE}")

        if DB_ENGINE == "postgres":
            print("🐘 Conectando a PostgreSQL (Supabase)...")
            return get_postgres_connection()

        elif DB_ENGINE == "sqlserver":
            print("🟦 Conectando a SQL Server (Local)...")
            return get_sqlserver_connection()

        else:
            raise Exception(f"DB_ENGINE no soportado: {DB_ENGINE}")

    except Exception as e:
        print("❌ ERROR CONEXIÓN DB:", e)
        raise e