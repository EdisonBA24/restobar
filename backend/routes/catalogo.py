
from flask import Blueprint, jsonify, request, session

from utils.security import tiene_sesion, es_admin

from services.catalogo_service import (
    CatalogoValidationError,
    listar_lineas_catalogo,
    listar_categorias_catalogo,
    crear_categoria_catalogo,
    actualizar_categoria_catalogo,
    cambiar_estado_categoria_catalogo,
    listar_items_catalogo,
    obtener_item_catalogo,
    crear_item_catalogo,
    actualizar_item_catalogo,
    cambiar_estado_item_catalogo,
    obtener_precios_catalogo,
    guardar_precios_catalogo,
    obtener_historial_precios,
    resolver_precio_catalogo,
)

from services.storage_service import (
    ImageValidationError,
    StorageConfigurationError,
    StorageUploadError,
    subir_imagen_catalogo
)


catalogo_bp = Blueprint(
    "catalogo",
    __name__
)


# =====================================================
# RESPUESTAS DE SEGURIDAD
# =====================================================

def _respuesta_no_autenticado():

    return jsonify({

        "status": "unauthorized",

        "message": "La sesión no está activa."

    }), 401


def _respuesta_sin_permiso():

    return jsonify({

        "status": "error",

        "message": (
            "Esta operación está permitida únicamente "
            "para usuarios ADMIN."
        )

    }), 403


# =====================================================
# VALIDAR SESION
# =====================================================

def _requiere_sesion():

    if not tiene_sesion():

        return _respuesta_no_autenticado()

    return None


# =====================================================
# VALIDAR ADMIN
# =====================================================

def _requiere_admin():

    if not tiene_sesion():

        return _respuesta_no_autenticado()

    if not es_admin():

        return _respuesta_sin_permiso()

    return None


# =====================================================
# SUBIR IMAGEN AL CATALOGO
#
# POST /api/catalogo/imagenes
# EXCLUSIVO ADMIN
# =====================================================

@catalogo_bp.route(
    "/catalogo/imagenes",
    methods=["POST"]
)
def subir_imagen_catalogo_endpoint():

    acceso = _requiere_admin()

    if acceso:
        return acceso

    archivo = request.files.get("imagen")

    if archivo is None or not archivo.filename:

        return jsonify({

            "status": "error",

            "message": "Seleccione una imagen para cargar."

        }), 400

    try:

        resultado = subir_imagen_catalogo(
            archivo
        )

        return jsonify({

            "status": "success",

            "message": "Imagen cargada correctamente.",

            "data": resultado

        }), 201

    except ImageValidationError as error:

        return jsonify({

            "status": "error",

            "message": str(error)

        }), 400

    except StorageConfigurationError as error:

        print(
            "ERROR CONFIGURACION STORAGE:",
            error
        )

        return jsonify({

            "status": "error",

            "message": str(error)

        }), 503

    except StorageUploadError as error:

        print(
            "ERROR SUPABASE STORAGE:",
            error
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible guardar la imagen en Supabase Storage."

        }), 502

    except Exception as error:

        print(
            "ERROR SUBIR IMAGEN CATALOGO:",
            error
        )

        return jsonify({

            "status": "error",

            "message": "Ocurrió un error interno al subir la imagen."

        }), 500


# =====================================================
# VALIDAR JSON
# =====================================================

def _body_json():

    data = request.get_json(
        silent=True
    )

    if not isinstance(data, dict):

        raise CatalogoValidationError(
            "El cuerpo de la solicitud debe ser un objeto JSON."
        )

    return data


# =====================================================
# ERROR GENERAL
# =====================================================

def _error_operacion(error, contexto):

    print(
        f"ERROR {contexto}:",
        error
    )

    return jsonify({

        "status": "error",

        "message": (
            "No fue posible completar la operación del catálogo."
        )

    }), 500


# =====================================================
# LINEAS COMERCIALES
#
# GET /api/catalogo/lineas
# =====================================================

@catalogo_bp.route(
    "/catalogo/lineas",
    methods=["GET"]
)
def obtener_lineas():

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    incluir_inactivas = (

        request.args.get(
            "incluir_inactivas",
            "false"
        ).strip().lower()

        in {"1", "true", "si", "sí"}

    ) and es_admin()

    try:

        data = listar_lineas_catalogo(
            incluir_inactivas
        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except Exception as e:

        return _error_operacion(
            e,
            "LISTAR LINEAS CATALOGO"
        )


# =====================================================
# CATEGORIAS COMERCIALES
#
# GET /api/catalogo/categorias
# POST /api/catalogo/categorias ADMIN
# PUT /api/catalogo/categorias/<id> ADMIN
# PATCH /api/catalogo/categorias/<id>/estado ADMIN
# =====================================================

@catalogo_bp.route(
    "/catalogo/categorias",
    methods=["GET"]
)
def obtener_categorias():

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    incluir_inactivas = (

        request.args.get(
            "incluir_inactivas",
            "false"
        ).strip().lower()

        in {"1", "true", "si", "sí"}

    ) and es_admin()

    try:

        linea_id = request.args.get(
            "linea_id"
        )

        data = listar_categorias_catalogo(

            linea_id=linea_id,

            incluir_inactivas=incluir_inactivas

        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "LISTAR CATEGORIAS CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/categorias",
    methods=["POST"]
)
def crear_categoria():

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        resultado = crear_categoria_catalogo(
            _body_json()
        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 201

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "CREAR CATEGORIA CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/categorias/<int:categoria_id>",
    methods=["PUT"]
)
def actualizar_categoria(categoria_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        resultado = actualizar_categoria_catalogo(

            categoria_id,

            _body_json()

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "ACTUALIZAR CATEGORIA CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/categorias/<int:categoria_id>/estado",
    methods=["PATCH"]
)
def cambiar_estado_categoria(categoria_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        data = _body_json()

        if "activo" not in data:

            raise CatalogoValidationError(
                "Debes indicar el nuevo estado de la categoría."
            )

        resultado = cambiar_estado_categoria_catalogo(

            categoria_id,

            data.get("activo")

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "CAMBIAR ESTADO CATEGORIA CATALOGO"
        )


# =====================================================
# ARTICULOS COMERCIALES
#
# GET /api/catalogo/items
# GET /api/catalogo/items/<id>
# POST /api/catalogo/items ADMIN
# PUT /api/catalogo/items/<id> ADMIN
# PATCH /api/catalogo/items/<id>/estado ADMIN
# =====================================================

@catalogo_bp.route(
    "/catalogo/items",
    methods=["GET"]
)
def obtener_items():

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    filtros = {

        "page": request.args.get(
            "page",
            1
        ),

        "page_size": request.args.get(
            "page_size",
            20
        ),

        "linea_id": request.args.get(
            "linea_id"
        ),

        "categoria_id": request.args.get(
            "categoria_id"
        ),

        "tipo_item": request.args.get(
            "tipo_item"
        ),

        "search": request.args.get(
            "search",
            ""
        ),

        "incluir_inactivos": (

            request.args.get(
                "incluir_inactivos",
                "false"
            ).strip().lower()

            in {"1", "true", "si", "sí"}

        ) and es_admin()

    }

    try:

        data = listar_items_catalogo(
            filtros
        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "LISTAR ITEMS CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/items/<int:item_id>",
    methods=["GET"]
)
def obtener_item(item_id):

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    try:

        data = obtener_item_catalogo(

            item_id,

            incluir_precios_inactivos=es_admin()

        )

        if not data:

            return jsonify({

                "status": "error",

                "message": "Artículo comercial no encontrado."

            }), 404

        if (
            not es_admin()
            and not data.get("activo")
        ):

            return jsonify({

                "status": "error",

                "message": "Artículo comercial no disponible."

            }), 404

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "OBTENER ITEM CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/items",
    methods=["POST"]
)
def crear_item():

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        resultado = crear_item_catalogo(
            _body_json()
        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 201

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "CREAR ITEM CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/items/<int:item_id>",
    methods=["PUT"]
)
def actualizar_item(item_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        resultado = actualizar_item_catalogo(

            item_id,

            _body_json()

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "ACTUALIZAR ITEM CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/items/<int:item_id>/estado",
    methods=["PATCH"]
)
def cambiar_estado_item(item_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        data = _body_json()

        if "activo" not in data:

            raise CatalogoValidationError(
                "Debes indicar el nuevo estado del artículo."
            )

        resultado = cambiar_estado_item_catalogo(

            item_id,

            data.get("activo")

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "CAMBIAR ESTADO ITEM CATALOGO"
        )


# =====================================================
# PRECIOS COMERCIALES
#
# GET /api/catalogo/items/<id>/precios
# PUT /api/catalogo/items/<id>/precios ADMIN
# GET /api/catalogo/items/<id>/precio
# =====================================================

@catalogo_bp.route(
    "/catalogo/items/<int:item_id>/precios",
    methods=["GET"]
)
def obtener_precios(item_id):

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    try:

        data = obtener_precios_catalogo(

            item_id,

            incluir_inactivos=es_admin()

        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "OBTENER PRECIOS CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/items/<int:item_id>/precios",
    methods=["PUT"]
)
def guardar_precios(item_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        data = _body_json()

        resultado = guardar_precios_catalogo(

            item_id=item_id,

            precios=data.get("precios"),

            usuario_id=session.get("user_id")

        )

        return jsonify({

            "status": "success",

            "data": resultado

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "GUARDAR PRECIOS CATALOGO"
        )


@catalogo_bp.route(
    "/catalogo/items/<int:item_id>/precio",
    methods=["GET"]
)
def resolver_precio(item_id):

    acceso = _requiere_sesion()

    if acceso:
        return acceso

    tipo_servicio = request.args.get(
        "tipo_servicio",
        "GENERAL"
    )

    try:

        data = resolver_precio_catalogo(

            item_id,

            tipo_servicio

        )

        if data is None:

            return jsonify({

                "status": "error",

                "message": (
                    "El artículo no tiene un precio activo "
                    "configurado para esta modalidad ni un precio general."
                )

            }), 404

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "RESOLVER PRECIO CATALOGO"
        )


# =====================================================
# HISTORIAL DE PRECIOS
#
# SOLO ADMIN
# =====================================================

@catalogo_bp.route(
    "/catalogo/items/<int:item_id>/historial-precios",
    methods=["GET"]
)
def historial_precios(item_id):

    acceso = _requiere_admin()

    if acceso:
        return acceso

    try:

        limit = request.args.get(
            "limit",
            100
        )

        data = obtener_historial_precios(

            item_id,

            limit

        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except CatalogoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        return _error_operacion(
            e,
            "HISTORIAL PRECIOS CATALOGO"
        )
