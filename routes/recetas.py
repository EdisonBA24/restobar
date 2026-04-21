from flask import Blueprint, request, jsonify, session
from services.recetas_service import crear_receta, obtener_receta

recetas_bp = Blueprint("recetas", __name__)


@recetas_bp.route("/recetas", methods=["POST"])
def crear():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    return crear_receta(request.json)

@recetas_bp.route("/recetas/<int:producto_id>", methods=["GET"])
def obtener(producto_id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    return obtener_receta(producto_id)