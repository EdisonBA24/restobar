
from flask import Blueprint, request, jsonify, session

from services.usuarios_service import (
    crear_usuario,
    get_usuarios,
    get_usuarios_legacy,
    update_usuario,
    activar_usuario as activar_usuario_service,
    get_usuarios_select,
    UsuarioValidationError,
    UsuarioConflictError,
    UsuarioNotFoundError,
    UsuarioPermissionError
)


usuarios_bp = Blueprint("usuarios", __name__)


# =====================================================
# VALIDACION DE PERMISOS
# =====================================================

def es_admin():

    perfil = str(
        session.get("perfil") or ""
    ).strip().lower()

    return perfil == "admin"


def validar_admin():

    return (
        session.get("user_id") is not None
        and es_admin()
    )


def _respuesta_error(message, status_code):

    return jsonify({
        "status": "error",
        "message": message
    }), status_code


def _parsear_entero(valor, nombre, default, minimo=1):

    try:

        resultado = int(
            valor if valor is not None else default
        )

    except (TypeError, ValueError):

        raise ValueError(
            f"El parámetro '{nombre}' debe ser un número entero."
        )

    if resultado < minimo:

        raise ValueError(
            f"El parámetro '{nombre}' debe ser mayor o igual a {minimo}."
        )

    return resultado


# =====================================================
# SELECT DE USUARIOS ACTIVOS
# SE CONSERVA PARA EL MODULO DE PAGOS
# =====================================================

@usuarios_bp.route("/usuarios/select", methods=["GET"])
def usuarios_select():

    if not validar_admin():

        return _respuesta_error(
            "No tienes permisos para consultar usuarios.",
            403
        )

    try:

        return jsonify({
            "status": "success",
            "data": get_usuarios_select()
        })

    except Exception as e:

        print("ERROR LISTA SELECT DE USUARIOS:", e)

        return _respuesta_error(
            "No fue posible cargar los empleados.",
            500
        )


# =====================================================
# LISTAR USUARIOS
# =====================================================

@usuarios_bp.route("/usuarios", methods=["GET"])
def listar():

    if not validar_admin():

        return _respuesta_error(
            "No tienes permisos para consultar usuarios.",
            403
        )

    try:

        # =============================================
        # COMPATIBILIDAD CON FRONTEND ACTUAL
        # =============================================

        parametros_paginacion = {

            "page",
            "limit",
            "page_size",
            "inactivos",
            "search",
            "sort_by",
            "sort_order"

        }

        usa_paginacion = any(
            parametro in request.args
            for parametro in parametros_paginacion
        )

        if not usa_paginacion:

            return jsonify({
                "status": "success",
                "data": get_usuarios_legacy()
            })

        # =============================================
        # PAGINACION
        # =============================================

        page = _parsear_entero(
            request.args.get("page"),
            "page",
            default=1
        )

        limit = _parsear_entero(
            request.args.get(
                "limit",
                request.args.get("page_size")
            ),
            "limit",
            default=10
        )

        limit = min(limit, 100)

        # =============================================
        # FILTRO ESTADO
        # =============================================

        inactivos_raw = str(
            request.args.get("inactivos", "false")
        ).strip().lower()

        if inactivos_raw not in (
            "true", "false", "1", "0", "yes", "no"
        ):

            return _respuesta_error(
                "El filtro 'inactivos' no tiene un valor válido.",
                400
            )

        solo_inactivos = inactivos_raw in (
            "true", "1", "yes"
        )

        # =============================================
        # BUSQUEDA Y ORDENAMIENTO
        # =============================================

        search = request.args.get(
            "search",
            ""
        ).strip()

        sort_by = request.args.get(
            "sort_by",
            "id"
        )

        sort_order = request.args.get(
            "sort_order",
            "desc"
        )

        resultado = get_usuarios(
            page=page,
            limit=limit,
            solo_inactivos=solo_inactivos,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return jsonify({
            "status": "success",
            "data": resultado
        })

    except ValueError as e:

        return _respuesta_error(
            str(e),
            400
        )

    except Exception as e:

        print("ERROR LISTAR USUARIOS:", e)

        return _respuesta_error(
            "No fue posible consultar los usuarios.",
            500
        )


# =====================================================
# CREAR USUARIO
# =====================================================

@usuarios_bp.route("/usuarios", methods=["POST"])
def crear():

    if not validar_admin():

        return _respuesta_error(
            "No tienes permisos para crear usuarios.",
            403
        )

    data = request.get_json(silent=True) or {}

    if not data:

        return _respuesta_error(
            "No se enviaron datos del usuario.",
            400
        )

    try:

        resultado = crear_usuario(data)

        return jsonify({
            "status": "success",
            "message": resultado.get(
                "message",
                "Usuario creado correctamente."
            )
        }), 201

    except UsuarioConflictError as e:

        return _respuesta_error(str(e), 409)

    except UsuarioValidationError as e:

        return _respuesta_error(str(e), 400)

    except Exception as e:

        print("ERROR CREAR USUARIO:", e)

        return _respuesta_error(
            "No fue posible crear el usuario.",
            500
        )


# =====================================================
# ACTUALIZAR USUARIO
# =====================================================

@usuarios_bp.route("/usuarios/<int:id>", methods=["PUT"])
def actualizar(id):

    if not validar_admin():

        return _respuesta_error(
            "No tienes permisos para actualizar usuarios.",
            403
        )

    data = request.get_json(silent=True) or {}

    if not data:

        return _respuesta_error(
            "No se enviaron datos para actualizar.",
            400
        )

    try:

        resultado = update_usuario(
            id,
            data,
            actor_id=session.get("user_id")
        )

        return jsonify({
            "status": "success",
            "message": resultado.get(
                "message",
                "Usuario actualizado correctamente."
            )
        })

    except UsuarioConflictError as e:

        return _respuesta_error(str(e), 409)

    except UsuarioNotFoundError as e:

        return _respuesta_error(str(e), 404)

    except UsuarioPermissionError as e:

        return _respuesta_error(str(e), 403)

    except UsuarioValidationError as e:

        return _respuesta_error(str(e), 400)

    except Exception as e:

        print("ERROR ACTUALIZAR USUARIO:", e)

        return _respuesta_error(
            "No fue posible actualizar el usuario.",
            500
        )


# =====================================================
# ACTIVAR / DESACTIVAR USUARIO
# =====================================================

@usuarios_bp.route("/usuarios/<int:id>/activar", methods=["PUT"])
def activar_usuario(id):

    if not validar_admin():

        return _respuesta_error(
            "No tienes permisos para cambiar el estado de usuarios.",
            403
        )

    data = request.get_json(silent=True) or {}

    if "activo" not in data:

        return _respuesta_error(
            "Debes indicar el estado que deseas asignar.",
            400
        )

    try:

        resultado = activar_usuario_service(
            id,
            data.get("activo"),
            actor_id=session.get("user_id")
        )

        return jsonify({
            "status": "success",
            "message": resultado.get(
                "message",
                "Estado actualizado correctamente."
            )
        })

    except UsuarioNotFoundError as e:

        return _respuesta_error(str(e), 404)

    except UsuarioPermissionError as e:

        return _respuesta_error(str(e), 403)

    except UsuarioValidationError as e:

        return _respuesta_error(str(e), 400)

    except Exception as e:

        print("ERROR ACTIVAR/DESACTIVAR USUARIO:", e)

        return _respuesta_error(
            "No fue posible actualizar el estado del usuario.",
            500
        )
