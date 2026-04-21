from flask import Blueprint, request, jsonify, session
from services.compras_service import crear_compra, get_compras, get_detalle_compra

compras_bp = Blueprint("compras", __name__)


@compras_bp.route("/compras", methods=["POST"])
def crear():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        data = request.json

        if not data:
            return jsonify({
                "status": "error",
                "message": "No se enviaron datos"
            }), 400

        if "detalles" not in data or not data["detalles"]:
            return jsonify({
                "status": "error",
                "message": "Debe incluir productos"
            }), 400

        result = crear_compra(data)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("❌ ERROR ROUTE COMPRAS:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    
@compras_bp.route("/compras", methods=["GET"])
def listar():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        data = get_compras()

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500
    

@compras_bp.route("/compras/<int:id>", methods=["GET"])
def detalle(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    data = get_detalle_compra(id)

    return jsonify({
        "status": "success",
        "data": data
    })