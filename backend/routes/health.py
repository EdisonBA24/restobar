from flask import Blueprint, jsonify
from database.connection import get_connection
from config import Config

health_bp = Blueprint("health", __name__)


@health_bp.route("/health", methods=["GET"])
def health():
    conn = None

    try:
        conn = get_connection()

        if conn:
            conn.close()

            return jsonify({
                "status": "ok",
                "message": f"Conexión a {Config.DB_TYPE} exitosa"
            })

        else:
            return jsonify({
                "status": "error",
                "message": "No se pudo establecer conexión"
            }), 500

    except Exception as e:
        print("❌ ERROR HEALTH:", e)

        return jsonify({
            "status": "error",
            "message": "Error conectando a la base de datos"
        }), 500

    finally:
        try:
            if conn:
                conn.close()
        except:
            pass