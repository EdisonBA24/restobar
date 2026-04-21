import pyodbc
from config import Config


def get_connection():
    try:
        conn = pyodbc.connect(Config.get_connection_string())
        return conn
    except Exception as e:
        print("❌ ERROR REAL DB:", e)  # 👈 CLAVE
        raise e  # 👈 IMPORTANTE