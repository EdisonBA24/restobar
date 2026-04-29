from config import Config

# 🔥 IMPORTS DINÁMICOS
import os

# 🔥 MEJORA: fallback inteligente (Config → ENV → default)
DB_ENGINE = getattr(Config, "DB_ENGINE", os.environ.get("DB_ENGINE", "sqlserver")).lower()


# =============================
# 🔥 POSTGRES (RENDER)
# =============================
def get_postgres_connection():
    import psycopg2

    try:
        return psycopg2.connect(
            host=Config.DB_HOST,
            database=Config.DB_NAME,
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            port=Config.DB_PORT,
            sslmode="require"  # 🔥 obligatorio en Render
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

        print(f"🔌 DB_ENGINE detectado: {DB_ENGINE}")  # 🔥 DEBUG PRO

        if DB_ENGINE == "postgres":
            return get_postgres_connection()

        elif DB_ENGINE == "sqlserver":
            return get_sqlserver_connection()

        else:
            raise Exception(f"DB_ENGINE no soportado: {DB_ENGINE}")

    except Exception as e:
        print("❌ ERROR CONEXIÓN DB:", e)
        raise e