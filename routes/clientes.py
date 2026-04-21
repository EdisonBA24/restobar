from flask import Blueprint, request, jsonify, session
from services.clientes_service import (
    get_all_clientes,
    create_cliente,
    update_cliente,
    delete_cliente,
    activar_cliente
)

clientes_bp = Blueprint("clientes", __name__)


@clientes_bp.route("/clientes", methods=["GET"])
def listar_clientes():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        page = int(request.args.get("page", 1))
        limit = int(request.args.get("limit", 10))
        solo_inactivos = request.args.get("inactivos", "false").lower() in ["true", "1"]
        search = request.args.get("search", None)

        data = get_all_clientes(page, limit, solo_inactivos, search)

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@clientes_bp.route("/clientes", methods=["POST"])
def crear_cliente():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        data = request.json
        data["usuario_id"] = session.get("user_id")

        result = create_cliente(data)
        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@clientes_bp.route("/clientes/<int:id>", methods=["PUT"])
def actualizar_cliente(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return jsonify(update_cliente(id, request.json))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@clientes_bp.route("/clientes/<int:id>", methods=["DELETE"])
def eliminar_cliente(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return jsonify(delete_cliente(id))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@clientes_bp.route("/clientes/<int:id>/activar", methods=["PUT"])
def activar(id):

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        return jsonify(activar_cliente(id))
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500