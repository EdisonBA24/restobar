
from flask import Blueprint, request, jsonify, session

from services.pagos_service import (
    crear_pago,
    get_pagos,
    get_pagos_legacy,
    PagoValidationError
)


pagos_bp = Blueprint("pagos", __name__)


# =====================================================
# VALIDAR ACCESO ADMINISTRADOR
# =====================================================

def validar_admin():

    if not session.get("user_id"):
        return "unauthorized"

    perfil = str(
        session.get("perfil") or ""
    ).strip().lower()

    if perfil != "admin":
        return "forbidden"

    return None


def _respuesta_acceso():

    estado = validar_admin()

    if estado == "unauthorized":

        return jsonify({

            "status": "unauthorized",

            "message": "La sesión no está activa."

        }), 401

    if estado == "forbidden":

        return jsonify({

            "status": "error",

            "message": "No tienes permisos para acceder al módulo de Pagos."

        }), 403

    return None


# =====================================================
# VALIDAR ENTEROS DE PAGINACION
# =====================================================

def _parsear_entero(
    valor,
    nombre,
    default,
    minimo=1
):

    try:

        resultado = int(
            valor if valor is not None else default
        )

    except (TypeError, ValueError):

        raise PagoValidationError(
            f"El parámetro '{nombre}' debe ser un número entero."
        )

    if resultado < minimo:

        raise PagoValidationError(
            f"El parámetro '{nombre}' debe ser mayor o igual a {minimo}."
        )

    return resultado


# =====================================================
# LISTAR PAGOS
# =====================================================

@pagos_bp.route("/pagos", methods=["GET"])
def listar_pagos():

    acceso = _respuesta_acceso()

    if acceso:
        return acceso

    try:

        # =============================================
        # COMPATIBILIDAD CON FRONTEND ANTERIOR
        #
        # GET /pagos sin parámetros sigue devolviendo
        # una lista simple.
        # =============================================

        parametros_nuevos = {

            "page",

            "limit",

            "page_size",

            "search",

            "fecha_inicio",

            "fecha_fin",

            "sort_by",

            "sort_order"

        }

        usa_paginacion = any(
            parametro in request.args
            for parametro in parametros_nuevos
        )

        if not usa_paginacion:

            data = get_pagos_legacy()

            return jsonify({

                "status": "success",

                "data": data

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
        # FILTROS
        # =============================================

        search = request.args.get(
            "search",
            ""
        ).strip()

        fecha_inicio = request.args.get(
            "fecha_inicio"
        )

        fecha_fin = request.args.get(
            "fecha_fin"
        )

        # =============================================
        # ORDENAMIENTO
        # =============================================

        sort_by = request.args.get(
            "sort_by",
            "id"
        )

        sort_order = request.args.get(
            "sort_order",
            "desc"
        )

        # =============================================
        # CONSULTAR
        # =============================================

        data = get_pagos(

            page=page,

            limit=limit,

            search=search,

            fecha_inicio=fecha_inicio,

            fecha_fin=fecha_fin,

            sort_by=sort_by,

            sort_order=sort_order

        )

        return jsonify({

            "status": "success",

            "data": data

        })

    except PagoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR LISTAR PAGOS:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible consultar los pagos."

        }), 500


# =====================================================
# REGISTRAR PAGO
# =====================================================

@pagos_bp.route("/pagos", methods=["POST"])
def crear():

    acceso = _respuesta_acceso()

    if acceso:
        return acceso

    data = request.get_json(
        silent=True
    ) or {}

    if not data:

        return jsonify({

            "status": "error",

            "message": "No se enviaron datos del pago."

        }), 400

    try:

        resultado = crear_pago(data)

        return jsonify({

            "status": "success",

            "message": resultado

        }), 201

    except PagoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR CREAR PAGO:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible registrar el pago."

        }), 500
