from decimal import Decimal, InvalidOperation
from utils.security import puede_modificar_precios
from flask import Blueprint, request, jsonify, session
from services.productos_service import (
    get_all_productos,
    create_producto,
    update_producto,
    delete_producto,
    activar_producto,
    get_producto_por_id,
    get_productos_por_categoria,
    get_componentes_almuerzo,
    get_productos_autocomplete
)

productos_bp = Blueprint("productos", __name__)


def responder_resultado(result):
    status_code = result.pop("status_code", 200)
    return jsonify(result), status_code


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session



# =====================================================
# VALIDAR PERMISOS PARA MODIFICAR PRECIO DE PRODUCTO
# =====================================================

def validar_precio_producto(
    data,
    precio_actual=None
):

    if "precio_venta" not in data:
        return None

    try:

        precio_nuevo = Decimal(
            str(data.get("precio_venta") or 0)
        )

    except (InvalidOperation, TypeError, ValueError):

        return jsonify({

            "status": "error",

            "message": "El precio de venta no tiene un valor válido."

        }), 400

    if precio_nuevo < 0:

        return jsonify({

            "status": "error",

            "message": "El precio de venta no puede ser negativo."

        }), 400

    # =============================================
    # CREACION
    # =============================================

    if precio_actual is None:

        hay_precio = precio_nuevo > 0

    # =============================================
    # ACTUALIZACION
    # =============================================

    else:

        anterior = Decimal(
            str(precio_actual or 0)
        )

        hay_precio = precio_nuevo != anterior

    # =============================================
    # AUTORIZACION
    # =============================================

    if (
        hay_precio
        and not puede_modificar_precios()
    ):

        return jsonify({

            "status": "error",

            "message": (
                "Solo un administrador puede crear o modificar "
                "el precio de venta de un producto."
            )

        }), 403

    return None



# =============================
# GET PRODUCTOS (CON SEARCH 🔥)
# =============================
@productos_bp.route("/productos", methods=["GET"])
def listar_productos():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        page = int(request.args.get("page", 1))

        limit = int(request.args.get("limit", 10))

        solo_inactivos = (
            request.args.get(
                "inactivos",
                "false"
            ).lower() in ["true", "1"]
        )

        search = request.args.get("search")

        sort_by = request.args.get(
            "sort_by",
            "id"
        )

        sort_order = request.args.get(
            "sort_order",
            "desc"
        )

        print("===== FILTROS PRODUCTOS =====")

        print({
            "page": page,
            "limit": limit,
            "inactivos": solo_inactivos,
            "search": search,
            "sort_by": sort_by,
            "sort_order": sort_order
        })

        data = get_all_productos(
            page=page,
            limit=limit,
            solo_inactivos=solo_inactivos,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:

        print("❌ ERROR LISTAR PRODUCTOS:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# AUTOCOMPLETE PRODUCTOS
# =============================
@productos_bp.route("/productos/autocomplete", methods=["GET"])
def autocomplete_productos():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        search = request.args.get("search")

        # Puede venir como:
        # ?tipo=INSUMO
        # ?tipo=INSUMO,LICOR
        # ?tipo=INSUMO&tipo=LICOR
        tipos = request.args.getlist("tipo")

        if len(tipos) == 1 and "," in tipos[0]:
            tipos = [
                t.strip()
                for t in tipos[0].split(",")
                if t.strip()
            ]

        if not tipos:
            tipos = None

        activo = request.args.get(
            "activo",
            "true"
        ).lower() in ["true", "1"]

        data = get_productos_autocomplete(
            search=search,
            tipos=tipos,
            activos=activo
        )

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:

        print("❌ ERROR AUTOCOMPLETE PRODUCTOS:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500



# =====================================================
# CREAR PRODUCTO
# =====================================================

@productos_bp.route("/productos", methods=["POST"])
def crear_producto():

    if not validar_sesion():

        return jsonify({
            "status": "unauthorized"
        }), 401

    try:

        data = request.get_json(
            silent=True
        ) or {}

        if not data:

            return jsonify({

                "status": "error",

                "message": "No se enviaron datos."

            }), 400

        # =============================================
        # VALIDAR PRECIO
        # =============================================

        error_precio = validar_precio_producto(
            data
        )

        if error_precio:
            return error_precio

        # =============================================
        # TRAZABILIDAD
        # =============================================

        data["usuario_id"] = session.get("user_id")

        return responder_resultado(
            create_producto(data)
        )

    except Exception as e:

        print(
            "ERROR CREAR PRODUCTO:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible crear el producto."

        }), 500




# =====================================================
# ACTUALIZAR PRODUCTO
# =====================================================

@productos_bp.route("/productos/<int:id>", methods=["PUT"])
def actualizar_producto(id):

    if not validar_sesion():

        return jsonify({
            "status": "unauthorized"
        }), 401

    try:

        data = request.get_json(
            silent=True
        ) or {}

        if not data:

            return jsonify({

                "status": "error",

                "message": "No se enviaron datos para actualizar."

            }), 400

        # =============================================
        # CONSULTAR PRODUCTO ACTUAL
        # =============================================

        producto_actual = get_producto_por_id(id)

        if not producto_actual:

            return jsonify({

                "status": "error",

                "message": "Producto no encontrado."

            }), 404

        precio_actual = producto_actual.get(
            "precio_venta"
        )

        # =============================================
        # PRESERVAR PRECIO SI NO VIENE EN EL REQUEST
        # =============================================

        if "precio_venta" not in data:

            data["precio_venta"] = precio_actual or 0

        # =============================================
        # VALIDAR PERMISO DE MODIFICACION
        # =============================================

        error_precio = validar_precio_producto(
            data,
            precio_actual
        )

        if error_precio:
            return error_precio

        # =============================================
        # ACTUALIZAR
        # =============================================

        return responder_resultado(
            update_producto(id, data)
        )

    except Exception as e:

        print(
            "ERROR ACTUALIZAR PRODUCTO:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible actualizar el producto."

        }), 500



# =============================
# DELETE
# =============================
@productos_bp.route("/productos/<int:id>", methods=["DELETE"])
def eliminar_producto(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return responder_resultado(delete_producto(id))
    except Exception as e:
        print("❌ ERROR DELETE:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# ACTIVATE
# =============================
@productos_bp.route("/productos/<int:id>/activar", methods=["PUT"])
def activar(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return responder_resultado(activar_producto(id))
    except Exception as e:
        print("❌ ERROR ACTIVATE:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    

# =============================
# GET PRODUCTOS POR CATEGORIA
# =============================
@productos_bp.route("/productos/categoria/<string:categoria>", methods=["GET"])
def listar_por_categoria(categoria):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        data = get_productos_por_categoria(categoria)

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:

        print("❌ ERROR PRODUCTOS CATEGORIA:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }),500
    

# =============================
# COMPONENTES ALMUERZO
# =============================
@productos_bp.route("/productos/almuerzo", methods=["GET"])
def componentes_almuerzo():

    if not validar_sesion():
        return jsonify({"status":"unauthorized"}),401

    try:

        return jsonify({

            "status":"success",

            "data":get_componentes_almuerzo()

        })

    except Exception as e:

        print("❌ ERROR COMPONENTES:",e)

        return jsonify({

            "status":"error",

            "message":str(e)

        }),500
 

# =============================
# GET PRODUCTO
# =============================
@productos_bp.route("/productos/<int:id>", methods=["GET"])
def producto(id):

    if not validar_sesion():
        return jsonify({"status":"unauthorized"}),401

    try:

        data = get_producto_por_id(id)

        if not data:

            return jsonify({

                "status":"error",

                "message":"Producto no encontrado"

            }),404

        return jsonify({

            "status":"success",

            "data":data

        })

    except Exception as e:

        print("❌ ERROR PRODUCTO:",e)

        return jsonify({

            "status":"error",

            "message":str(e)

        }),500