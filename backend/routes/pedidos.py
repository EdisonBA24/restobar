from flask import Blueprint, request, jsonify, session
from services.pedidos_service import crear_pedido#, validar_stock_pedido
from services.pedidos_service import get_pedidos, get_pedido_detalle
from services.pedidos_service import facturar_pedido

pedidos_bp = Blueprint("pedidos", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# 🧾 CREAR PEDIDO
# =============================
@pedidos_bp.route("/pedidos", methods=["POST"])
def crear():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json

        if not data or "detalles" not in data or not data["detalles"]:
            return jsonify({
                "status": "error",
                "message": "Datos inválidos"
            }), 400

        # 🔥 agregar usuario desde sesión
        data["usuario_id"] = session.get("user_id")

        result = crear_pedido(data)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("❌ ERROR CREAR PEDIDO:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# 📦 VALIDAR STOCK
# =============================
#@pedidos_bp.route("/pedidos/validar-stock", methods=["POST"])
#def validar():

#    if not validar_sesion():
#        return jsonify({"status": "unauthorized"}), 401

#    try:
#        data = request.json

#        if not data or "detalles" not in data:
#            return jsonify({
#                "status": "error",
#                "message": "Datos inválidos"
#            }), 400

#       return jsonify(validar_stock_pedido(data))

#    except Exception as e:
#        print("❌ ERROR VALIDAR STOCK PEDIDO:", e)

#        return jsonify({
#            "status": "error",
#            "message": "Error validando stock"
#        }), 500


# =============================
# 📄 LISTAR PEDIDOS
# =============================
@pedidos_bp.route("/pedidos", methods=["GET"])
def listar():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_pedidos()

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR LISTAR PEDIDOS:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo pedidos"
        }), 500


# =============================
# 🔍 DETALLE
# =============================
@pedidos_bp.route("/pedidos/<int:id>", methods=["GET"])
def detalle(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_pedido_detalle(id)

        if not data:
            return jsonify({
                "status": "error",
                "message": "Pedido no encontrado"
            }), 404

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR DETALLE PEDIDO:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo detalle"
        }), 500


# =============================
# 🔥 FACTURAR CON METODO PAGO
# =============================
@pedidos_bp.route("/pedidos/<int:id>/facturar", methods=["POST"])
def facturar(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json or {}

        # 🔥 método de pago
        metodo_pago = data.get("metodo_pago", "Efectivo")

        # 🔥 usuario que factura
        usuario_id = session.get("user_id")

        result = facturar_pedido(id, metodo_pago, usuario_id)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("❌ ERROR FACTURAR PEDIDO:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500