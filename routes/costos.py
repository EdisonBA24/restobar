from flask import Blueprint, jsonify, session
from services.costos_service import get_costo_producto

costos_bp = Blueprint("costos", __name__)


@costos_bp.route("/costos/<int:producto_id>", methods=["GET"])
def costo(producto_id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    return jsonify({
        "status": "success",
        "data": get_costo_producto(producto_id)
    })