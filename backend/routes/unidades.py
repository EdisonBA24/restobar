from flask import Blueprint, jsonify, session
from database.connection import get_connection

unidades_bp = Blueprint("unidades", __name__)


@unidades_bp.route("/unidades", methods=["GET"])
def listar_unidades():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401

    conn = None

    try:
        conn = get_connection()

        if not conn:
            return jsonify({
                "status": "error",
                "message": "Error de conexión a la base de datos"
            }), 500

        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nombre, abreviatura
            FROM restobar.unidades_medida
            WHERE activo = 1
            ORDER BY nombre
        """)

        columns = [column[0] for column in cursor.description]
        data = [dict(zip(columns, row)) for row in cursor.fetchall()]

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR UNIDADES:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

    finally:
        if conn:
            conn.close()