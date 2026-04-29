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


def validar_admin():
    return "user_id" in session and es_admin()


# =============================
# LISTAR USUARIOS
# =============================
@usuarios_bp.route("/usuarios", methods=["GET"])
def listar():

    if not validar_admin():
        return jsonify({"status": "unauthorized"}), 403

    try:
        return jsonify({
            "status": "success",
            "data": get_usuarios()
        })

    except Exception as e:
        print("❌ ERROR LISTAR USUARIOS:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# CREAR USUARIO
# =============================
@usuarios_bp.route("/usuarios", methods=["POST"])
def crear():

    if not validar_admin():
        return jsonify({"status": "unauthorized"}), 403

    try:
        data = request.json or {}

        if not data:
            return jsonify({
                "status": "error",
                "message": "Datos vacíos"
            }), 400

        return jsonify(crear_usuario(data))

    except Exception as e:
        print("❌ ERROR CREAR USUARIO:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# ACTUALIZAR USUARIO
# =============================
@usuarios_bp.route("/usuarios/<int:id>", methods=["PUT"])
def actualizar(id):

    if not validar_admin():
        return jsonify({"status": "unauthorized"}), 403

    try:
        data = request.json or {}

        if not data:
            return jsonify({
                "status": "error",
                "message": "Datos vacíos"
            }), 400

        return jsonify(update_usuario(id, data))

    except Exception as e:
        print("❌ ERROR ACTUALIZAR USUARIO:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# 🔥 ACTIVAR / DESACTIVAR USUARIO
# =============================
@usuarios_bp.route("/usuarios/<int:id>/activar", methods=["PUT"])
def activar_usuario(id):

    if not validar_admin():
        return jsonify({"status": "unauthorized"}), 403

    # 🔥 evitar que el admin se desactive a sí mismo
    if id == session.get("user_id"):
        return jsonify({
            "status": "error",
            "message": "No puedes desactivarte a ti mismo"
        }), 400

    try:
        data = request.json or {}
        activo = data.get("activo", 1)

        activar_usuario_service(id, activo)

        return jsonify({
            "status": "success",
            "message": "Estado actualizado correctamente"
        })

    except Exception as e:
        print("❌ ERROR ACTIVAR/DESACTIVAR USUARIO:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500