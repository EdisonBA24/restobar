from flask import Blueprint, request, jsonify, session
from services.productos_service import (
    get_all_productos,
    create_producto,
    update_producto,
    delete_producto,
    activar_producto
)

productos_bp = Blueprint("productos", __name__)


# =============================
# GET PRODUCTOS (CON SEARCH 🔥)
# =============================
@productos_bp.route("/productos", methods=["GET"])
def listar_productos():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))

        solo_inactivos = request.args.get("inactivos", "false").lower() in ["true", "1"]

        # 🔥 NUEVO
        search = request.args.get("search", None)

        print("📌 PAGE:", page, "| INACTIVOS:", solo_inactivos, "| SEARCH:", search)

        data = get_all_productos(page, limit, solo_inactivos, search)

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
# CREATE
# =============================
@productos_bp.route("/productos", methods=["POST"])
def crear_producto():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return jsonify(create_producto(request.json))
    except Exception as e:
        print("❌ ERROR CREAR:", e)
        return jsonify({"message": str(e)}), 500


# =============================
# UPDATE
# =============================
@productos_bp.route("/productos/<int:id>", methods=["PUT"])
def actualizar_producto(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return jsonify(update_producto(id, request.json))
    except Exception as e:
        print("❌ ERROR UPDATE:", e)
        return jsonify({"message": str(e)}), 500


# =============================
# DELETE
# =============================
@productos_bp.route("/productos/<int:id>", methods=["DELETE"])
def eliminar_producto(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return jsonify(delete_producto(id))
    except Exception as e:
        print("❌ ERROR DELETE:", e)
        return jsonify({"message": str(e)}), 500


# =============================
# ACTIVATE
# =============================
@productos_bp.route("/productos/<int:id>/activar", methods=["PUT"])
def activar(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return jsonify(activar_producto(id))
    except Exception as e:
        print("❌ ERROR ACTIVATE:", e)
        return jsonify({"message": str(e)}), 500