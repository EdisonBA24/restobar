import os
import psycopg2

def get_connection():
    return psycopg2.connect(
        host=os.environ.get("DB_HOST"),
        database=os.environ.get("DB_NAME"),
        user=os.environ.get("DB_USER"),
        password=os.environ.get("DB_PASSWORD"),
        port=os.environ.get("DB_PORT"),
        sslmode="require"
    )


##
# import os

#class Config:
#    DB_DRIVER = "ODBC Driver 17 for SQL Server"
#    DB_SERVER = "LAPTOP-ULEKB954"
#    DB_DATABASE = "erp_restaurante"

#    @staticmethod
#    def get_connection_string():
#        return (
#            f"DRIVER={{{Config.DB_DRIVER}}};"
#            f"SERVER={Config.DB_SERVER};"
#            f"DATABASE={Config.DB_DATABASE};"
#            "Trusted_Connection=yes;"
#        )