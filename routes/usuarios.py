from flask import Blueprint, request, jsonify, session
from services.usuarios_service import (
    crear_usuario,
    get_usuarios,
    update_usuario,
    activar_usuario as activar_usuario_service
)

usuarios_bp = Blueprint("usuarios", __name__)


# =============================
# VALIDACIÓN ADMIN
# =============================
def es_admin():
    return session.get("perfil") == "admin"


# =============================
# LISTAR USUARIOS
# =============================
@usuarios_bp.route("/usuarios", methods=["GET"])
def listar():

    if "user_id" not in session or not es_admin():
        return jsonify({"status": "unauthorized"}), 403

    return jsonify({
        "status": "success",
        "data": get_usuarios()
    })


# =============================
# CREAR USUARIO
# =============================
@usuarios_bp.route("/usuarios", methods=["POST"])
def crear():

    if "user_id" not in session or not es_admin():
        return jsonify({"status": "unauthorized"}), 403

    data = request.json
    return jsonify(crear_usuario(data))


# =============================
# ACTUALIZAR USUARIO
# =============================
@usuarios_bp.route("/usuarios/<int:id>", methods=["PUT"])
def actualizar(id):

    if "user_id" not in session or not es_admin():
        return jsonify({"status": "unauthorized"}), 403

    data = request.json
    return jsonify(update_usuario(id, data))


# =============================
# 🔥 ACTIVAR / DESACTIVAR USUARIO
# =============================
@usuarios_bp.route("/usuarios/<int:id>/activar", methods=["PUT"])
def activar_usuario(id):

    if "user_id" not in session or not es_admin():
        return jsonify({"status": "unauthorized"}), 403

    # 🔥 evitar que el admin se desactive a sí mismo
    if id == session.get("user_id"):
        return jsonify({
            "status": "error",
            "message": "No puedes desactivarte a ti mismo"
        }), 400

    data = request.json
    activo = data.get("activo", 1)

    try:

        activar_usuario_service(id, activo)

        return jsonify({
            "status": "success",
            "message": "Estado actualizado correctamente"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500