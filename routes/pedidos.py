from flask import Blueprint, request, jsonify, session
from services.pedidos_service import crear_pedido, validar_stock_pedido
from services.pedidos_service import get_pedidos, get_pedido_detalle
from services.pedidos_service import facturar_pedido

pedidos_bp = Blueprint("pedidos", __name__)


@pedidos_bp.route("/pedidos", methods=["POST"])
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

        result = crear_pedido(data)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


@pedidos_bp.route("/pedidos/validar-stock", methods=["POST"])
def validar():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    data = request.json
    return jsonify(validar_stock_pedido(data))


@pedidos_bp.route("/pedidos", methods=["GET"])
def listar():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    return jsonify({
        "status": "success",
        "data": get_pedidos()
    })


@pedidos_bp.route("/pedidos/<int:id>", methods=["GET"])
def detalle(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    return jsonify({
        "status": "success",
        "data": get_pedido_detalle(id)
    })


# =============================
# 🔥 FACTURAR CON METODO PAGO
# =============================
@pedidos_bp.route("/pedidos/<int:id>/facturar", methods=["POST"])
def facturar(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json or {}

        # 🔥 NUEVO: capturar metodo de pago
        metodo_pago = data.get("metodo_pago", "Efectivo")

        result = facturar_pedido(id, metodo_pago)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500