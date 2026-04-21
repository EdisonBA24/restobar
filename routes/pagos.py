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
        return jsonify({"status": "unauthorized"}), 403

    return jsonify({
        "status": "success",
        "data": get_pagos()
    })


# =============================
# 💾 CREAR PAGO
# =============================
@pagos_bp.route("/pagos", methods=["POST"])
def crear():

    if not login_required():
        return jsonify({"status": "unauthorized"}), 403

    data = request.json

    try:
        result = crear_pago(data)
        return jsonify({
            "status": "success",
            "message": result
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 400