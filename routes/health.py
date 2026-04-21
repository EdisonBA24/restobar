from flask import Blueprint, jsonify
from database.connection import get_connection

health_bp = Blueprint("health", __name__)

@health_bp.route("/health", methods=["GET"])
def health():
    conn = get_connection()

    if conn:
        conn.close()
        return jsonify({
            "status": "ok",
            "message": "Conexión a SQL Server exitosa"
        })
    else:
        return jsonify({
            "status": "error",
            "message": "No se pudo conectar a la base de datos"
        }), 500