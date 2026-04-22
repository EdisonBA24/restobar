import os

class Config:
    DB_HOST = os.environ.get("DB_HOST")
    DB_NAME = os.environ.get("DB_NAME")
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")
    DB_PORT = os.environ.get("DB_PORT")


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