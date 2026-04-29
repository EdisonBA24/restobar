from flask import Blueprint, request, jsonify, session
from services.pagos_service import (
    crear_pago,
    get_pagos
)

pagos_bp = Blueprint("pagos", __name__)


def login_required():
    return "user_id" in session


# =============================
# 📄 LISTAR PAGOS
# =============================
@pagos_bp.route("/pagos", methods=["GET"])
def listar_pagos():

    if not login_required():
        return jsonify({"status": "unauthorized"}), 401  # 🔥 FIX (antes 403)

    try:

        data = get_pagos()

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR LISTAR PAGOS:", e)  # 🔥 LOG CLAVE

        return jsonify({
            "status": "error",
            "message": "Error obteniendo pagos"
        }), 500


# =============================
# 💾 CREAR PAGO
# =============================
@pagos_bp.route("/pagos", methods=["POST"])
def crear():

    if not login_required():
        return jsonify({"status": "unauthorized"}), 401  # 🔥 FIX

    data = request.json

    # 🔥 VALIDACIÓN REAL
    if not data:
        return jsonify({
            "status": "error",
            "message": "No se enviaron datos"
        }), 400

    try:

        # 🔥 agregar usuario desde sesión
        data["usuario_id"] = session.get("user_id")

        result = crear_pago(data)

        return jsonify({
            "status": "success",
            "message": result
        })

    except Exception as e:
        print("❌ ERROR CREAR PAGO:", e)  # 🔥 LOG CLAVE

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400