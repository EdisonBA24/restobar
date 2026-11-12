
from flask import Blueprint, jsonify, request
import traceback

from utils.security import tiene_sesion, es_admin

from services.catalogo_menus_service import (
    CatalogoMenuValidationError,
    obtener_configuracion_menu,
    crear_categoria_menu,
    actualizar_categoria_menu,
    cambiar_estado_categoria_menu,
    listar_productos_categoria_menu,
    listar_productos_disponibles_menu_categoria,
    guardar_productos_categoria_menu,
)


catalogo_menus_bp = Blueprint(
    "catalogo_menus",
    __name__
)


# =====================================================
# SEGURIDAD
# =====================================================

def _requiere_sesion():

    if not tiene_sesion():

        return jsonify({

            "status": "unauthorized",

            "message": "La sesión no está activa."

        }), 401

    return None


def _requiere_admin():

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    if not es_admin():

        return jsonify({

            "status": "error",

            "message": (
                "Esta operación está permitida únicamente "
                "para usuarios ADMIN."
            )

        }), 403

    return None


# =====================================================
# VALIDAR JSON
# =====================================================

def _body_json():

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):

        raise CatalogoMenuValidationError(
            "El cuerpo de la solicitud debe ser un objeto JSON."
        )

    return data


# =====================================================
# MANEJO DE ERRORES
# =====================================================

def _error_operacion(error, contexto):

    print(
        f"ERROR {contexto}:",
        error
    )

    traceback.print_exc()

    return jsonify({

        "status": "error",

        "message": (
            "No fue posible completar la operación "
            "de configuración del menú."
        )

    }), 500


# =====================================================
# CONFIGURACION COMPLETA DE MENU
#
# GET /api/catalogo/items/<id>/configuracion-menu
# =====================================================

@catalogo_menus_bp.route(
    "/catalogo/items/<int:menu_item_id>/configuracion-menu",
    methods=["GET"]
)
def obtener_configuracion(menu_item_id):

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    incluir_inactivos = (

        request.args.get(
            "incluir_inactivos",
            "false"
        ).strip().lower()

        in {"1", "true", "si", "sí"}

    ) and es_admin()

    try:

        data = obtener_configuracion_menu(

            menu_item_id,

            incluir_inactivos=incluir_inactivos

        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoMenuValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "OBTENER CONFIGURACION MENU"
        )


# =====================================================
# CREAR CATEGORIA DENTRO DEL MENU
#
# POST /api/catalogo/items/<id>/categorias-menu
# ADMIN
# =====================================================

@catalogo_menus_bp.route(
    "/catalogo/items/<int:menu_item_id>/categorias-menu",
    methods=["POST"]
)
def crear_categoria(menu_item_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        resultado = crear_categoria_menu(

            menu_item_id,

            _body_json()

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 201

    except CatalogoMenuValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "CREAR CATEGORIA MENU"
        )


# =====================================================
# ACTUALIZAR CATEGORIA DEL MENU
#
# PUT /api/catalogo/items/<id>/categorias-menu/<categoria_id>
# ADMIN
# =====================================================

@catalogo_menus_bp.route(
    "/catalogo/items/<int:menu_item_id>/categorias-menu/<int:menu_categoria_id>",
    methods=["PUT"]
)
def actualizar_categoria(
    menu_item_id,
    menu_categoria_id
):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        resultado = actualizar_categoria_menu(

            menu_item_id,

            menu_categoria_id,

            _body_json()

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoMenuValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "ACTUALIZAR CATEGORIA MENU"
        )


# =====================================================
# ACTIVAR / DESACTIVAR CATEGORIA
#
# PATCH /api/catalogo/items/<id>/categorias-menu/<categoria_id>/estado
# ADMIN
# =====================================================

@catalogo_menus_bp.route(
    "/catalogo/items/<int:menu_item_id>/categorias-menu/<int:menu_categoria_id>/estado",
    methods=["PATCH"]
)
def cambiar_estado_categoria(
    menu_item_id,
    menu_categoria_id
):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        data = _body_json()

        if "activo" not in data:

            raise CatalogoMenuValidationError(
                "Debes indicar el estado de la categoría."
            )

        resultado = cambiar_estado_categoria_menu(

            menu_item_id,

            menu_categoria_id,

            data["activo"]

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoMenuValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "CAMBIAR ESTADO CATEGORIA MENU"
        )


# =====================================================
# CONSULTAR PRODUCTOS ASOCIADOS
#
# GET /api/catalogo/menu-categorias/<id>/productos
# =====================================================

@catalogo_menus_bp.route(
    "/catalogo/menu-categorias/<int:menu_categoria_id>/productos",
    methods=["GET"]
)
def obtener_productos_categoria(menu_categoria_id):

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    incluir_inactivos = (

        request.args.get(
            "incluir_inactivos",
            "false"
        ).strip().lower()

        in {"1", "true", "si", "sí"}

    ) and es_admin()

    try:

        data = listar_productos_categoria_menu(

            menu_categoria_id,

            incluir_inactivos=incluir_inactivos

        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoMenuValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "OBTENER PRODUCTOS CATEGORIA MENU"
        )


# =====================================================
# LISTAR PRODUCTOS DISPONIBLES
#
# GET /api/catalogo/menu-categorias/<id>/productos-disponibles
# =====================================================

@catalogo_menus_bp.route(
    "/catalogo/menu-categorias/<int:menu_categoria_id>/productos-disponibles",
    methods=["GET"]
)
def obtener_productos_disponibles(menu_categoria_id):

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    incluir_inactivos = (

        request.args.get(
            "incluir_inactivos",
            "false"
        ).strip().lower()

        in {"1", "true", "si", "sí"}

    ) and es_admin()

    try:

        data = listar_productos_disponibles_menu_categoria(

            menu_categoria_id,

            search=request.args.get(
                "search",
                ""
            ),

            incluir_inactivos=incluir_inactivos

        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoMenuValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "LISTAR PRODUCTOS DISPONIBLES MENU"
        )


# =====================================================
# ASIGNAR / ACTUALIZAR PRODUCTOS DE UNA CATEGORIA
#
# PUT /api/catalogo/menu-categorias/<id>/productos
# ADMIN
# =====================================================

@catalogo_menus_bp.route(
    "/catalogo/menu-categorias/<int:menu_categoria_id>/productos",
    methods=["PUT"]
)
def guardar_productos_categoria(menu_categoria_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        data = _body_json()

        if "productos" not in data:

            raise CatalogoMenuValidationError(
                "Debes enviar la lista de productos de la categoría."
            )

        resultado = guardar_productos_categoria_menu(

            menu_categoria_id,

            data["productos"]

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoMenuValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "GUARDAR PRODUCTOS CATEGORIA MENU"
        )
