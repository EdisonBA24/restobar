from flask import Blueprint, jsonify, session
from database.connection import get_connection

insumos_bp = Blueprint("insumos", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# 📦 LISTAR INSUMOS
# =============================
@insumos_bp.route("/insumos", methods=["GET"])
def listar_insumos():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    conn = None

    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT id, nombre FROM insumo WHERE activo=1")

        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()

        data = [dict(zip(columns, row)) for row in rows] if rows else []

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR INSUMOS:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo insumos"
        }), 500

    finally:
        try:
            if conn:
                conn.close()
        except:
            pass