from flask import Blueprint, jsonify, session
from database.connection import get_connection

insumos_bp = Blueprint("insumos", __name__)

@insumos_bp.route("/insumos", methods=["GET"])
def listar_insumos():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre FROM insumo WHERE activo=1")

    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "status": "success",
        "data": data
    })