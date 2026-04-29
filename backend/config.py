import os


class Config:
    # =============================
    # 🔥 ENTORNO
    # =============================
    ENV = os.environ.get("ENV", "development")

    # =============================
    # 🔥 ENGINE (CLAVE DEL SISTEMA)
    # =============================
    # 🔥 PRIORIDAD:
    # 1. ENV DB_ENGINE
    # 2. Si hay DATABASE_URL → postgres
    # 3. Default → sqlserver
    DB_ENGINE = os.environ.get("DB_ENGINE") or (
        "postgres" if os.environ.get("DATABASE_URL") else "sqlserver"
    )

    # =============================
    # 🔥 RENDER (POSTGRES)
    # =============================
    DATABASE_URL = os.environ.get("DATABASE_URL")

    # 🔥 EXTRA (para uso directo si decides no usar DATABASE_URL)
    DB_HOST = os.environ.get("DB_HOST")
    DB_NAME = os.environ.get("DB_NAME")
    DB_PORT = os.environ.get("DB_PORT", 5432)

    # =============================
    # 🔥 LOCAL (SQL SERVER)
    # =============================
    DB_DRIVER = os.environ.get("DB_DRIVER", "ODBC Driver 17 for SQL Server")
    DB_SERVER = os.environ.get("DB_SERVER", "LAPTOP-ULEKB954")
    DB_DATABASE = os.environ.get("DB_DATABASE", "erp_restaurante")

    # Windows auth (local típico)
    DB_TRUSTED = os.environ.get("DB_TRUSTED", "yes")

    # SQL auth (opcional)
    DB_USER = os.environ.get("DB_USER")
    DB_PASSWORD = os.environ.get("DB_PASSWORD")

    # =============================
    # 🔥 CONEXIÓN UNIFICADA
    # =============================
    @staticmethod
    def get_connection_string():
        """
        🔥 Decide automáticamente qué motor usar
        """

        # =============================
        # 🚀 PRODUCCIÓN (Render → PostgreSQL)
        # =============================
        if Config.DATABASE_URL:
            return Config.DATABASE_URL

        # =============================
        # 🖥️ LOCAL (SQL SERVER)
        # =============================
        if Config.DB_USER and Config.DB_PASSWORD:
            # 🔐 SQL AUTH
            return (
                f"DRIVER={{{Config.DB_DRIVER}}};"
                f"SERVER={Config.DB_SERVER};"
                f"DATABASE={Config.DB_DATABASE};"
                f"UID={Config.DB_USER};"
                f"PWD={Config.DB_PASSWORD};"
            )
        else:
            # 🔓 WINDOWS AUTH
            return (
                f"DRIVER={{{Config.DB_DRIVER}}};"
                f"SERVER={Config.DB_SERVER};"
                f"DATABASE={Config.DB_DATABASE};"
                "Trusted_Connection=yes;"
            )

    # =============================
    # 🔥 VALIDACIÓN
    # =============================
    @staticmethod
    def validate():

        print(f"🔧 ENV: {Config.ENV}")
        print(f"🔌 DB_ENGINE: {Config.DB_ENGINE}")

        if Config.DB_ENGINE == "postgres":
            if not Config.DATABASE_URL and not Config.DB_HOST:
                raise Exception("Configuración incompleta de PostgreSQL")

        else:
            # SQL SERVER
            if not Config.DB_SERVER or not Config.DB_DATABASE:
                raise Exception("Configuración incompleta de SQL Server")

    # =============================
    DEBUG = ENV == "development"