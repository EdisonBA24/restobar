from flask import Blueprint, request, jsonify, session
from services.ventas_service import crear_venta#, validar_stock
from services.ventas_service import get_ventas, get_venta_detalle

ventas_bp = Blueprint("ventas", __name__)


# =============================
# 🔐 VALIDACIÓN SESIÓN
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# 🧾 CREAR VENTA
# =============================
@ventas_bp.route("/ventas", methods=["POST"])
def crear():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json or {}

        if not data or "detalles" not in data:
            return jsonify({
                "status": "error",
                "message": "Datos inválidos"
            }), 400

        if not isinstance(data["detalles"], list) or len(data["detalles"]) == 0:
            return jsonify({
                "status": "error",
                "message": "Debe incluir al menos un producto"
            }), 400

        # 🔥 validación interna básica
        for d in data["detalles"]:
            if not d.get("producto_id") or float(d.get("cantidad", 0)) <= 0:
                return jsonify({
                    "status": "error",
                    "message": "Detalle inválido"
                }), 400

        result = crear_venta(data)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("❌ ERROR CREAR VENTA:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# 📦 VALIDAR STOCK
# =============================
#@ventas_bp.route("/ventas/validar-stock", methods=["POST"])
#def validar():

#    if not validar_sesion():
#        return jsonify({"status": "unauthorized"}), 401

#    try:
#        data = request.json or {}

#        if not data or "detalles" not in data:
#            return jsonify({
#                "ok": False,
#                "message": "Datos inválidos"
#            }), 400

#        return jsonify(validar_stock(data))

#    except Exception as e:
#        print("❌ ERROR VALIDAR STOCK:", e)

#        return jsonify({
#            "ok": False,
#            "message": "Error validando stock"
#        }), 500


# =============================
# 📊 LISTAR VENTAS
# =============================
@ventas_bp.route("/ventas", methods=["GET"])
def listar():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        return jsonify({
            "status": "success",
            "data": get_ventas()
        })

    except Exception as e:
        print("❌ ERROR LISTAR VENTAS:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# 🔍 DETALLE VENTA
# =============================
@ventas_bp.route("/ventas/<int:id>", methods=["GET"])
def detalle(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_venta_detalle(id)

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR DETALLE VENTA:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500