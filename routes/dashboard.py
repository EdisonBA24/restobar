from flask import Blueprint, jsonify, session
from services.dashboard_service import get_dashboard

dashboard_bp = Blueprint("dashboard", __name__)


@dashboard_bp.route("/dashboard", methods=["GET"])
def dashboard():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    
    return jsonify({
        "status": "success",
        "data": get_dashboard()
    })