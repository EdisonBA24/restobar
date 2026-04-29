from flask import Blueprint, jsonify, session
from services.dashboard_service import get_dashboard

dashboard_bp = Blueprint("dashboard", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# 📊 DASHBOARD
# =============================
@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_dashboard()

        # 🔥 evitar null / undefined en frontend
        if not data:
            return jsonify({
                "status": "success",
                "data": {}
            })

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR DASHBOARD:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo dashboard"
        }), 500