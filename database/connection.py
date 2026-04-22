from config import Config
import psycopg2

def get_connection():
    return psycopg2.connect(
        host=Config.DB_HOST,
        database=Config.DB_NAME,
        user=Config.DB_USER,
        password=Config.DB_PASSWORD,
        port=Config.DB_PORT,
        sslmode="require"
    )

#import pyodbc
#from config import Config


#def get_connection():
#    try:
#        conn = pyodbc.connect(Config.get_connection_string())
#        return conn
#    except Exception as e:
#        print("❌ ERROR REAL DB:", e)  # 👈 CLAVE
#       raise e  # 👈 IMPORTANTE