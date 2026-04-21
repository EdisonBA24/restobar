from flask import Blueprint, jsonify, session
from database.connection import get_connection

unidades_bp = Blueprint("unidades", __name__)

@unidades_bp.route("/unidades", methods=["GET"])
def listar_unidades():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, nombre, abreviatura FROM unidades_medida WHERE activo=1")

    columns = [column[0] for column in cursor.description]
    data = [dict(zip(columns, row)) for row in cursor.fetchall()]

    conn.close()

    return jsonify({
        "status": "success",
        "data": data
    })