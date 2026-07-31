from flask import Blueprint, request, jsonify, session
from services.clientes_service import (
    get_all_clientes,
    get_cliente_por_id,
    create_cliente,
    update_cliente,
    delete_cliente,
    activar_cliente,
    get_clientes_autocomplete
)

clientes_bp = Blueprint("clientes", __name__)


def responder_resultado(result):

    if result is None:

        return jsonify({
            "status": "error",
            "message": "Registro no encontrado."
        }),404

    status_code = result.pop("status_code",200)

    return jsonify(result),status_code


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

        sort_by = request.args.get("sort_by", "id")
        
        sort_order = request.args.get("sort_order", "desc")

        data = get_all_clientes(
            page=page,
            limit=limit,
            solo_inactivos=solo_inactivos,
            search=search,
            sort_by=sort_by,
            sort_order=sort_order
        )

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


@clientes_bp.route("/clientes/autocomplete", methods=["GET"])
def autocomplete_clientes():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        search = request.args.get("search")

        activo = request.args.get(
            "activo",
            "true"
        ).lower() in ["true", "1"]

        data = get_clientes_autocomplete(
            search=search,
            activos=activo
        )

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:

        print("❌ ERROR AUTOCOMPLETE CLIENTES:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# OBTENER CLIENTE
# =============================
@clientes_bp.route("/clientes/<int:id>", methods=["GET"])
def obtener_cliente(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        cliente = get_cliente_por_id(id)

        if not cliente:

            return jsonify({

                "status": "error",

                "message": "Cliente no encontrado"

            }),404

        return jsonify({

            "status":"success",

            "data":cliente

        })

    except Exception as e:

        print(e)

        return jsonify({

            "status":"error",

            "message":"Error obteniendo cliente"

        }),500


# =============================
# ➕ CREAR
# =============================
@clientes_bp.route("/clientes", methods=["POST"])
def crear_cliente():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.get_json(silent=True) or {}

        data["usuario_id"] = session.get("user_id")

        # 🔥 validar mínimo
        if not data.get("nombre"):
            return jsonify({
                "status": "error",
                "message": "El nombre es obligatorio"
            }), 400

        data["usuario_id"] = session.get("user_id")

        result = create_cliente(data)

        return responder_resultado(result)

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

        data["usuario_id"] = session.get("user_id")

        result = update_cliente(id, data)

        return responder_resultado(result)

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
        return responder_resultado(result)

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
        return responder_resultado(result)

    except Exception as e:
        print("❌ ERROR activar_cliente:", e)
        return jsonify({
            "status": "error",
            "message": "Error activando cliente"
        }), 500
