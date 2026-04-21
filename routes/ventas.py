from flask import Blueprint, request, jsonify, session
from services.ventas_service import crear_venta, validar_stock
from services.ventas_service import get_ventas, get_venta_detalle

ventas_bp = Blueprint("ventas", __name__)


@ventas_bp.route("/ventas", methods=["POST"])
def crear():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        data = request.json

        if not data or "detalles" not in data:
            return jsonify({
                "status": "error",
                "message": "Datos inválidos"
            }), 400

        result = crear_venta(data)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@ventas_bp.route("/ventas/validar-stock", methods=["POST"])
def validar():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    data = request.json
    return jsonify(validar_stock(data))


@ventas_bp.route("/ventas", methods=["GET"])
def listar():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    return jsonify({
        "status": "success",
        "data": get_ventas()
    })


@ventas_bp.route("/ventas/<int:id>", methods=["GET"])
def detalle(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    return jsonify({
        "status": "success",
        "data": get_venta_detalle(id)
    })