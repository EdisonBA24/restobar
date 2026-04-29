from flask import Blueprint, jsonify, session
from services.costos_service import get_costo_producto

costos_bp = Blueprint("costos", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# 💰 COSTO PRODUCTO
# =============================
@costos_bp.route("/costos/<int:producto_id>", methods=["GET"])
def costo(producto_id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_costo_producto(producto_id)

        # 🔥 validar si no existe
        if not data:
            return jsonify({
                "status": "error",
                "message": "Producto no encontrado"
            }), 404

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR COSTOS:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo costo"
        }), 500