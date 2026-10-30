import os

from werkzeug.security import generate_password_hash

from config import Config
from database.connection import get_connection
from database.db_objects import USUARIOS


def init_admin():

    conn = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        is_postgres = (
            getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        )

        placeholder = "%s" if is_postgres else "?"

        # =============================================
        # CONFIGURACION ADMINISTRADOR INICIAL
        # =============================================

        username = str(
            os.environ.get("ADMIN_INITIAL_USERNAME", "admin")
        ).strip().lower()

        nombre = str(
            os.environ.get("ADMIN_INITIAL_NAME", "Administrador")
        ).strip()

        raw_password = os.environ.get(
            "ADMIN_INITIAL_PASSWORD"
        )

        if not username:
            raise RuntimeError(
                "ADMIN_INITIAL_USERNAME no puede estar vacío."
            )

        if not nombre:
            raise RuntimeError(
                "ADMIN_INITIAL_NAME no puede estar vacío."
            )

        # =============================================
        # VERIFICAR SI EL ADMINISTRADOR YA EXISTE
        # =============================================

        cursor.execute(
            f"""
            SELECT id, perfil, activo
            FROM {USUARIOS}
            WHERE LOWER(usuario) = {placeholder}
            """,
            (username,)
        )

        existing = cursor.fetchone()

        if existing:

            perfil_existente = str(
                existing[1] or ""
            ).strip().lower()

            activo_existente = int(
                existing[2] or 0
            )

            if perfil_existente != "admin" or activo_existente != 1:

                raise RuntimeError(
                    "La cuenta configurada como administrador inicial "
                    "ya existe, pero no tiene perfil ADMIN activo. "
                    "No se modificó la cuenta. Revisa el usuario."
                )

            print(
                "Administrador inicial existente y activo. "
                "No se modificaron sus credenciales."
            )

            return {
                "created": False,
                "message": "El administrador ya existe y no fue modificado."
            }

        # =============================================
        # VALIDAR CONTRASEÑA INICIAL
        # Solo se necesita cuando el administrador
        # todavía no existe.
        # =============================================

                # =============================================
        # EVITAR CREAR UN SEGUNDO ADMINISTRADOR
        # =============================================

        cursor.execute(
            f"""
            SELECT COUNT(*)
            FROM {USUARIOS}
            WHERE LOWER(perfil) = {placeholder}
              AND activo = {placeholder}
            """,
            ("admin", 1)
        )

        administradores_activos = int(
            cursor.fetchone()[0] or 0
        )

        if administradores_activos > 0:

            print(
                "Ya existe un administrador activo. "
                "No se requiere crear la cuenta inicial."
            )

            return {
                "created": False,
                "message": "Ya existe un administrador activo."
            }

        if not raw_password:

            raise RuntimeError(
                "No existe un administrador y falta configurar "
                "ADMIN_INITIAL_PASSWORD en las variables de entorno."
            )

        if len(raw_password) < 12:

            raise RuntimeError(
                "ADMIN_INITIAL_PASSWORD debe tener al menos 12 caracteres."
            )

        password_hash = generate_password_hash(
            raw_password
        )

        # =============================================
        # CREAR ADMINISTRADOR
        # =============================================

        cursor.execute(
            f"""
            INSERT INTO {USUARIOS}
            (
                nombre,
                usuario,
                password,
                perfil,
                activo
            )
            VALUES
            (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                1
            )
            """,
            (
                nombre,
                username,
                password_hash,
                "admin"
            )
        )

        conn.commit()

        print(
            "Administrador inicial creado correctamente."
        )

        return {
            "created": True,
            "message": "Administrador inicial creado correctamente."
        }

    except Exception:

        if conn:
            conn.rollback()

        raise

    finally:

        if conn:
            conn.close()


if __name__ == "__main__":
    init_admin()