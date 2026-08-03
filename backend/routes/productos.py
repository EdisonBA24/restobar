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


# =============================
# CREATE
# =============================
@productos_bp.route("/productos", methods=["POST"])
def crear_producto():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        data = request.json

        if not data:
            return jsonify({
                "status": "error",
                "message": "No se enviaron datos"
            }), 400

        # 🔥 trazabilidad
        data["usuario_id"] = session.get("user_id")

        return responder_resultado(create_producto(data))

    except Exception as e:
        print("❌ ERROR CREAR:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# UPDATE
# =============================
@productos_bp.route("/productos/<int:id>", methods=["PUT"])
def actualizar_producto(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        data = request.json

        if not data:
            return jsonify({
                "status": "error",
                "message": "No se enviaron datos"
            }), 400

        return responder_resultado(update_producto(id, data))

    except Exception as e:
        print("❌ ERROR UPDATE:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
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