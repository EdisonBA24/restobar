from flask import Blueprint, request, jsonify, session
from services.compras_service import crear_compra, get_compras, get_detalle_compra

compras_bp = Blueprint("compras", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# ➕ CREAR COMPRA
# =============================
@compras_bp.route("/compras", methods=["POST"])
def crear():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.get_json(silent=True) or {}

        # 🔥 VALIDACIONES
        if not data:
            return jsonify({
                "status": "error",
                "message": "No se enviaron datos"
            }), 400

        detalles = data.get("detalles", [])

        if not isinstance(detalles, list) or len(detalles) == 0:
            return jsonify({
                "status": "error",
                "message": "Debe incluir productos"
            }), 400

        # 🔥 validar estructura de detalles
        for d in detalles:
            if not d.get("producto_id") or float(d.get("cantidad", 0)) <= 0:
                return jsonify({
                    "status": "error",
                    "message": "Detalle inválido en productos"
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
            "message": "Error creando compra"
        }), 500


# =============================
# 📋 LISTAR COMPRAS
# =============================
@compras_bp.route("/compras", methods=["GET"])
def listar():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_compras()

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR LISTAR COMPRAS:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo compras"
        }), 500


# =============================
# 🔍 DETALLE COMPRA
# =============================
@compras_bp.route("/compras/<int:id>", methods=["GET"])
def detalle(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_detalle_compra(id)

        if not data:
            return jsonify({
                "status": "error",
                "message": "Compra no encontrada"
            }), 404

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR DETALLE COMPRA:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo detalle"
        }), 500