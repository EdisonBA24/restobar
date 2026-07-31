from flask import Blueprint, request, jsonify, session

from services.proveedores_service import (
    get_all_proveedores,
    get_proveedor_por_id,
    create_proveedor,
    update_proveedor,
    delete_proveedor,
    activar_proveedor,
    get_proveedores_autocomplete
)

proveedores_bp = Blueprint("proveedores", __name__)

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


def get_int_param(valor, default):

    try:
        return int(valor)
    except (TypeError, ValueError):
        return default
    

# =============================
# 📋 LISTAR
# =============================
@proveedores_bp.route("/proveedores", methods=["GET"])
def listar_proveedores():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        page = max(get_int_param(request.args.get("page"), 1), 1)
        limit = min(max(get_int_param(request.args.get("limit"), 10), 1), 100)

        solo_inactivos = request.args.get(
            "inactivos",
            "false"
        ).lower() in ["true", "1"]

        search = request.args.get("search")

        data = get_all_proveedores(
            page,
            limit,
            solo_inactivos,
            search
        )

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:

        print("❌ ERROR listar_proveedores:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo proveedores"
        }), 500


# =============================
# AUTOCOMPLETE
# =============================
@proveedores_bp.route("/proveedores/autocomplete", methods=["GET"])
def autocomplete_proveedores():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        search = request.args.get("search")

        activo = request.args.get(
            "activo",
            "true"
        ).lower() in ["true", "1"]

        data = get_proveedores_autocomplete(
            search=search,
            activos=activo
        )

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:

        print("❌ ERROR AUTOCOMPLETE PROVEEDORES:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# OBTENER PROVEEDOR
# =============================
@proveedores_bp.route("/proveedores/<int:id>", methods=["GET"])
def obtener_proveedor(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        proveedor = get_proveedor_por_id(id)

        if not proveedor:

            return jsonify({
                "status": "error",
                "message": "Proveedor no encontrado."
            }), 404

        return jsonify({
            "status": "success",
            "data": proveedor
        })

    except Exception as e:

        print("❌ ERROR obtener_proveedor:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo proveedor."
        }), 500
    

# =============================
# ➕ CREAR
# =============================
@proveedores_bp.route("/proveedores", methods=["POST"])
def crear_proveedor():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        data = request.get_json(silent=True) or {}

        data["usuario_id"] = session.get("user_id")

        result = create_proveedor(data)

        return responder_resultado(result)

    except Exception as e:

        print("❌ ERROR crear_proveedor:", e)

        return jsonify({
            "status": "error",
            "message": "Error creando proveedor."
        }), 500
    

# =============================
# ✏️ ACTUALIZAR
# =============================
@proveedores_bp.route("/proveedores/<int:id>", methods=["PUT"])
def actualizar_proveedor(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        data = request.get_json(silent=True) or {}

        data["usuario_id"] = session.get("user_id")

        result = update_proveedor(id, data)

        return responder_resultado(result)

    except Exception as e:

        print("❌ ERROR actualizar_proveedor:", e)

        return jsonify({
            "status": "error",
            "message": "Error actualizando proveedor."
        }), 500


# =============================
# 🗑️ ELIMINAR
# =============================
@proveedores_bp.route("/proveedores/<int:id>", methods=["DELETE"])
def eliminar_proveedor(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        result = delete_proveedor(id)

        return responder_resultado(result)

    except Exception as e:

        print("❌ ERROR eliminar_proveedor:", e)

        return jsonify({
            "status": "error",
            "message": "Error desactivando proveedor."
        }), 500
    

# =============================
# 🔄 ACTIVAR
# =============================
@proveedores_bp.route("/proveedores/<int:id>/activar", methods=["PUT"])
def activar(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:

        result = activar_proveedor(id)

        return responder_resultado(result)

    except Exception as e:

        print("❌ ERROR activar_proveedor:", e)

        return jsonify({
            "status": "error",
            "message": "Error activando proveedor."
        }), 500