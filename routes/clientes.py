from flask import Blueprint, request, jsonify, session
from services.clientes_service import (
    get_all_clientes,
    create_cliente,
    update_cliente,
    delete_cliente,
    activar_cliente
)

clientes_bp = Blueprint("clientes", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    if "user_id" not in session:
        return False
    return True


# =============================
# 📋 LISTAR
# =============================
@clientes_bp.route("/clientes", methods=["GET"])
def listar_clientes():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        # 🔥 seguros
        page = max(int(request.args.get("page", 1)), 1)
        limit = min(max(int(request.args.get("limit", 10)), 1), 100)

        solo_inactivos = request.args.get("inactivos", "false").lower() in ["true", "1"]
        search = request.args.get("search")

        data = get_all_clientes(page, limit, solo_inactivos, search)

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR listar_clientes:", e)
        return jsonify({
            "status": "error",
            "message": "Error obteniendo clientes"
        }), 500


# =============================
# ➕ CREAR
# =============================
@clientes_bp.route("/clientes", methods=["POST"])
def crear_cliente():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.get_json(silent=True) or {}

        # 🔥 validar mínimo
        if not data.get("nombre"):
            return jsonify({
                "status": "error",
                "message": "El nombre es obligatorio"
            }), 400

        data["usuario_id"] = session.get("user_id")

        result = create_cliente(data)

        return jsonify(result)

    except Exception as e:
        print("❌ ERROR crear_cliente:", e)
        return jsonify({
            "status": "error",
            "message": "Error creando cliente"
        }), 500


# =============================
# ✏️ EDITAR
# =============================
@clientes_bp.route("/clientes/<int:id>", methods=["PUT"])
def actualizar_cliente(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.get_json(silent=True) or {}

        result = update_cliente(id, data)

        return jsonify(result)

    except Exception as e:
        print("❌ ERROR actualizar_cliente:", e)
        return jsonify({
            "status": "error",
            "message": "Error actualizando cliente"
        }), 500


# =============================
# 🗑️ ELIMINAR
# =============================
@clientes_bp.route("/clientes/<int:id>", methods=["DELETE"])
def eliminar_cliente(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        result = delete_cliente(id)
        return jsonify(result)

    except Exception as e:
        print("❌ ERROR eliminar_cliente:", e)
        return jsonify({
            "status": "error",
            "message": "Error eliminando cliente"
        }), 500


# =============================
# 🔄 ACTIVAR
# =============================
@clientes_bp.route("/clientes/<int:id>/activar", methods=["PUT"])
def activar(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        result = activar_cliente(id)
        return jsonify(result)

    except Exception as e:
        print("❌ ERROR activar_cliente:", e)
        return jsonify({
            "status": "error",
            "message": "Error activando cliente"
        }), 500