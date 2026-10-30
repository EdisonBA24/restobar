
from database.connection import get_connection
from config import Config
from database.db_objects import USUARIOS
from werkzeug.security import generate_password_hash


# =====================================================
# EXCEPCIONES DEL MODULO
# =====================================================

class UsuarioValidationError(Exception):
    pass


class UsuarioConflictError(Exception):
    pass


class UsuarioNotFoundError(Exception):
    pass


class UsuarioPermissionError(Exception):
    pass


# =====================================================
# CONFIGURACION BASE DE DATOS
# =====================================================

def _get_db_settings():

    is_postgres = (
        getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
    )

    placeholder = "%s" if is_postgres else "?"

    return is_postgres, placeholder


# =====================================================
# VALIDACIONES
# =====================================================

def _normalizar_activo(valor, default=None):

    if valor is None:
        return default

    if isinstance(valor, bool):
        return 1 if valor else 0

    valor = str(valor).strip().lower()

    if valor in ("1", "true", "activo", "si", "sí"):
        return 1

    if valor in ("0", "false", "inactivo", "no"):
        return 0

    raise UsuarioValidationError(
        "El estado del usuario debe ser Activo o Inactivo."
    )


def _validar_datos_usuario(data, perfil_default="ventas"):

    if not isinstance(data, dict):
        raise UsuarioValidationError(
            "Los datos del usuario no tienen un formato válido."
        )

    nombre = str(
        data.get("nombre") or ""
    ).strip()

    usuario = str(
        data.get("usuario") or ""
    ).strip().lower()

    perfil = str(
        data.get("perfil") or perfil_default
    ).strip().lower()

    if not nombre:
        raise UsuarioValidationError(
            "El nombre completo es obligatorio."
        )

    if not usuario:
        raise UsuarioValidationError(
            "El nombre de usuario es obligatorio."
        )

    if any(caracter.isspace() for caracter in usuario):
        raise UsuarioValidationError(
            "El nombre de usuario no puede contener espacios."
        )

    if perfil not in ("admin", "ventas"):
        raise UsuarioValidationError(
            "El perfil seleccionado no es válido."
        )

    return {
        "nombre": nombre,
        "usuario": usuario,
        "perfil": perfil
    }


def _validar_password(password):

    if not isinstance(password, str) or not password:
        raise UsuarioValidationError(
            "La contraseña es obligatoria."
        )

    if password.isspace():
        raise UsuarioValidationError(
            "La contraseña no puede contener únicamente espacios."
        )

    if len(password) < 12:
        raise UsuarioValidationError(
            "La contraseña debe tener al menos 12 caracteres."
        )


def _contar_administradores_activos(cursor, placeholder):

    cursor.execute(
        f"""
        SELECT COUNT(*)
        FROM {USUARIOS}
        WHERE LOWER(perfil) = {placeholder}
          AND activo = {placeholder}
        """,
        ("admin", 1)
    )

    row = cursor.fetchone()

    return int(row[0] or 0)


def _es_mismo_id(id_a, id_b):

    if id_a is None or id_b is None:
        return False

    try:
        return int(id_a) == int(id_b)
    except (TypeError, ValueError):
        return str(id_a) == str(id_b)


# =====================================================
# SELECT DE USUARIOS ACTIVOS
# UTILIZADO POR EL MODULO DE PAGOS
# =====================================================

def get_usuarios_select():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(f"""
            SELECT
                id,
                nombre
            FROM {USUARIOS}
            WHERE activo = 1
            ORDER BY nombre
        """)

        columns = [
            c[0]
            for c in cursor.description
        ]

        return [
            dict(zip(columns, row))
            for row in cursor.fetchall()
        ]

    except Exception as e:

        print("ERROR LISTA USUARIOS:", e)
        raise

    finally:
        conn.close()


# =====================================================
# LISTADO COMPLETO LEGACY
#
# COMPATIBILIDAD TEMPORAL CON EL FRONTEND ACTUAL.
# SE ELIMINARA CUANDO SE IMPLEMENTE LA NUEVA UI.
# =====================================================

def get_usuarios_legacy():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(f"""
            SELECT
                id,
                nombre,
                usuario,
                perfil,
                activo
            FROM {USUARIOS}
            ORDER BY id DESC
        """)

        columns = [
            c[0]
            for c in cursor.description
        ]

        data = []

        for row in cursor.fetchall():

            usuario = dict(zip(columns, row))

            usuario["id"] = int(
                usuario.get("id") or 0
            )

            usuario["activo"] = _normalizar_activo(
                usuario.get("activo"),
                default=0
            )

            data.append(usuario)

        return data

    except Exception as e:

        print("ERROR LISTAR USUARIOS LEGACY:", e)
        raise

    finally:
        conn.close()


# =====================================================
# LISTADO PAGINADO DE USUARIOS
# =====================================================

def get_usuarios(
    page=1,
    limit=10,
    solo_inactivos=False,
    search=None,
    sort_by="id",
    sort_order="desc"
):

    page = max(int(page), 1)
    limit = min(max(int(limit), 1), 100)

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres, placeholder = _get_db_settings()

        estado = 0 if solo_inactivos else 1

        where = f"""
            WHERE u.activo = {placeholder}
        """

        params = [estado]
        count_params = [estado]

        # =============================================
        # BUSQUEDA
        # =============================================

        if search and str(search).strip():

            texto = str(search).strip().lower()[:100]

            like = f"%{texto}%"

            filtro = f"""
                AND (
                    LOWER(COALESCE(u.nombre, '')) LIKE {placeholder}
                    OR LOWER(COALESCE(u.usuario, '')) LIKE {placeholder}
                    OR LOWER(COALESCE(u.perfil, '')) LIKE {placeholder}
                )
            """

            where += filtro

            params.extend([like, like, like])
            count_params.extend([like, like, like])

        # =============================================
        # COLUMNAS PERMITIDAS PARA ORDENAR
        # =============================================

        columnas_validas = {

            "id": "u.id",
            "nombre": "u.nombre",
            "usuario": "u.usuario",
            "perfil": "u.perfil",
            "activo": "u.activo"

        }

        sort_by = str(
            sort_by or "id"
        ).strip().lower()

        if sort_by not in columnas_validas:
            sort_by = "id"

        sort_column = columnas_validas[sort_by]

        sort_order = (
            "ASC"
            if str(sort_order).strip().lower() == "asc"
            else "DESC"
        )

        # =============================================
        # TOTAL DE REGISTROS
        # =============================================

        count_query = f"""
            SELECT COUNT(*)
            FROM {USUARIOS} u
            {where}
        """

        cursor.execute(
            count_query,
            tuple(count_params)
        )

        total = int(
            cursor.fetchone()[0] or 0
        )

        total_pages = max(
            (total + limit - 1) // limit,
            1
        )

        if page > total_pages:

            page = total_pages
            offset = (page - 1) * limit

        # =============================================
        # CONSULTA PRINCIPAL
        # =============================================

        query = f"""
            SELECT
                u.id,
                u.nombre,
                u.usuario,
                u.perfil,
                u.activo
            FROM {USUARIOS} u
            {where}
            ORDER BY {sort_column} {sort_order}
        """

        if is_postgres:

            query += f"""
                LIMIT {placeholder}
                OFFSET {placeholder}
            """

            params.extend([
                limit,
                offset
            ])

        else:

            query += f"""
                OFFSET {placeholder}
                ROWS FETCH NEXT {placeholder} ROWS ONLY
            """

            params.extend([
                offset,
                limit
            ])

        cursor.execute(
            query,
            tuple(params)
        )

        columns = [
            c[0]
            for c in cursor.description
        ]

        items = []

        for row in cursor.fetchall():

            item = dict(zip(columns, row))

            item["id"] = int(
                item.get("id") or 0
            )

            item["activo"] = _normalizar_activo(
                item.get("activo"),
                default=0
            )

            items.append(item)

        return {

            "items": items,
            "page": page,
            "page_size": limit,
            "total": total,
            "total_pages": total_pages,
            "sort_by": sort_by,
            "sort_order": sort_order.lower()

        }

    except Exception as e:

        print("ERROR GET USUARIOS PAGINADOS:", e)
        raise

    finally:
        conn.close()


# =====================================================
# CREAR USUARIO
# =====================================================

def crear_usuario(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        datos = _validar_datos_usuario(data)

        password = data.get("password")

        _validar_password(password)

        _, placeholder = _get_db_settings()

        # =============================================
        # VALIDAR USUARIO UNICO
        # SIN DIFERENCIAR MAYUSCULAS
        # =============================================

        cursor.execute(
            f"""
            SELECT id
            FROM {USUARIOS}
            WHERE LOWER(usuario) = {placeholder}
            """,
            (datos["usuario"],)
        )

        if cursor.fetchone():

            raise UsuarioConflictError(
                "El nombre de usuario ya está registrado."
            )

        password_hash = generate_password_hash(
            password
        )

        # =============================================
        # INSERTAR USUARIO
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
                datos["nombre"],
                datos["usuario"],
                password_hash,
                datos["perfil"]
            )
        )

        conn.commit()

        return {
            "message": "Usuario creado correctamente."
        }

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


# =====================================================
# ACTUALIZAR USUARIO
# =====================================================

def update_usuario(id, data, actor_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        _, placeholder = _get_db_settings()

        # =============================================
        # OBTENER ESTADO ACTUAL
        # =============================================

        cursor.execute(
            f"""
            SELECT perfil, activo
            FROM {USUARIOS}
            WHERE id = {placeholder}
            """,
            (id,)
        )

        actual = cursor.fetchone()

        if not actual:

            raise UsuarioNotFoundError(
                "El usuario que intentas actualizar no existe."
            )

        perfil_actual = str(
            actual[0] or ""
        ).strip().lower()

        activo_actual = _normalizar_activo(
            actual[1],
            default=0
        )

        datos = _validar_datos_usuario(
            data,
            perfil_default=perfil_actual or "ventas"
        )

        # Si el formulario no envía activo,
        # se conserva el estado actual.

        activo_nuevo = _normalizar_activo(
            data.get("activo"),
            default=activo_actual
        )

        # =============================================
        # PROTEGER LA CUENTA ACTUAL
        # =============================================

        if _es_mismo_id(id, actor_id):

            if activo_nuevo == 0:

                raise UsuarioPermissionError(
                    "No puedes desactivar tu propio usuario."
                )

            if datos["perfil"] != "admin":

                raise UsuarioPermissionError(
                    "No puedes retirar tu propio perfil de administrador."
                )

        # =============================================
        # VALIDAR USUARIO DUPLICADO
        # =============================================

        cursor.execute(
            f"""
            SELECT id
            FROM {USUARIOS}
            WHERE LOWER(usuario) = {placeholder}
              AND id <> {placeholder}
            """,
            (
                datos["usuario"],
                id
            )
        )

        if cursor.fetchone():

            raise UsuarioConflictError(
                "El nombre de usuario ya está registrado."
            )

        # =============================================
        # PROTEGER ULTIMO ADMINISTRADOR ACTIVO
        # =============================================

        continua_como_admin = (
            datos["perfil"] == "admin"
            and activo_nuevo == 1
        )

        era_admin_activo = (
            perfil_actual == "admin"
            and activo_actual == 1
        )

        if era_admin_activo and not continua_como_admin:

            total_admins = _contar_administradores_activos(
                cursor,
                placeholder
            )

            if total_admins <= 1:

                raise UsuarioPermissionError(
                    "No se puede quitar el perfil o desactivar "
                    "al último administrador activo."
                )

        # =============================================
        # CONTRASEÑA OPCIONAL
        # =============================================

        password = data.get("password")

        if password is not None and password != "":

            _validar_password(password)

            password_hash = generate_password_hash(
                password
            )

            query = f"""
                UPDATE {USUARIOS}
                SET
                    nombre = {placeholder},
                    usuario = {placeholder},
                    password = {placeholder},
                    perfil = {placeholder},
                    activo = {placeholder}
                WHERE id = {placeholder}
            """

            params = (
                datos["nombre"],
                datos["usuario"],
                password_hash,
                datos["perfil"],
                activo_nuevo,
                id
            )

        else:

            query = f"""
                UPDATE {USUARIOS}
                SET
                    nombre = {placeholder},
                    usuario = {placeholder},
                    perfil = {placeholder},
                    activo = {placeholder}
                WHERE id = {placeholder}
            """

            params = (
                datos["nombre"],
                datos["usuario"],
                datos["perfil"],
                activo_nuevo,
                id
            )

        cursor.execute(
            query,
            params
        )

        conn.commit()

        return {
            "message": "Usuario actualizado correctamente."
        }

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()


# =====================================================
# ACTIVAR / DESACTIVAR USUARIO
# =====================================================

def activar_usuario(id, activo, actor_id=None):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        activo = _normalizar_activo(activo)

        if activo is None:

            raise UsuarioValidationError(
                "Debes indicar el nuevo estado del usuario."
            )

        _, placeholder = _get_db_settings()

        # =============================================
        # OBTENER USUARIO
        # =============================================

        cursor.execute(
            f"""
            SELECT perfil, activo
            FROM {USUARIOS}
            WHERE id = {placeholder}
            """,
            (id,)
        )

        usuario = cursor.fetchone()

        if not usuario:

            raise UsuarioNotFoundError(
                "Usuario no encontrado."
            )

        perfil_actual = str(
            usuario[0] or ""
        ).strip().lower()

        activo_actual = _normalizar_activo(
            usuario[1],
            default=0
        )

        # =============================================
        # PROTEGER USUARIO DE LA SESION ACTUAL
        # =============================================

        if activo == 0 and _es_mismo_id(id, actor_id):

            raise UsuarioPermissionError(
                "No puedes desactivar tu propio usuario."
            )

        # =============================================
        # PROTEGER ULTIMO ADMINISTRADOR
        # =============================================

        if (
            activo == 0
            and activo_actual == 1
            and perfil_actual == "admin"
        ):

            total_admins = _contar_administradores_activos(
                cursor,
                placeholder
            )

            if total_admins <= 1:

                raise UsuarioPermissionError(
                    "No se puede desactivar al último administrador activo."
                )

        # =============================================
        # ACTUALIZAR ESTADO
        # =============================================

        cursor.execute(
            f"""
            UPDATE {USUARIOS}
            SET activo = {placeholder}
            WHERE id = {placeholder}
            """,
            (
                activo,
                id
            )
        )

        conn.commit()

        return {
            "message": (
                "Usuario activado correctamente."
                if activo == 1
                else "Usuario desactivado correctamente."
            )
        }

    except Exception:

        conn.rollback()
        raise

    finally:
        conn.close()
