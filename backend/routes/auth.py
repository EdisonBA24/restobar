from flask import Blueprint, request, jsonify, session
from database.connection import get_connection
from werkzeug.security import check_password_hash
import logging

auth_bp = Blueprint("auth", __name__)

logger = logging.getLogger(__name__)


# =============================
# 🔐 LOGIN
# =============================
@auth_bp.route("/login", methods=["POST"])
def login():
    conn = None

    try:
        data = request.get_json(silent=True) or {}

        usuario = str(data.get("usuario", "")).strip().lower()
        password = str(data.get("password", "")).strip()

        # 🔥 VALIDACIÓN BÁSICA
        if not usuario or not password:
            return jsonify({
                "status": "error",
                "message": "Usuario y contraseña son obligatorios"
            }), 400

        conn = get_connection()
        cursor = conn.cursor()

        # 🔥 QUERY SEGURA (solo usuario)
        query = """
            SELECT id, nombre, perfil, activo, password
            FROM restobar.usuarios
            WHERE LOWER(usuario) = %s
        """

        # 🔥 ADAPTADOR MULTI DB (más limpio)
        paramstyle = getattr(conn, "paramstyle", "")
        if "pyodbc" in str(type(conn)).lower() or paramstyle == "qmark":
            query = query.replace("%s", "?")

        cursor.execute(query, (usuario,))
        user = cursor.fetchone()

        # ❌ usuario no existe
        if not user:
            return jsonify({
                "status": "error",
                "message": "Credenciales incorrectas"
            }), 401

        user_id, nombre, perfil, activo, password_hash = user

        # 🔥 VALIDAR HASH EXISTE
        if not password_hash:
            logger.warning(f"Usuario sin password hash: {usuario}")
            return jsonify({
                "status": "error",
                "message": "Credenciales incorrectas"
            }), 401

        # 🔐 VALIDAR PASSWORD
        if not check_password_hash(password_hash, password):
            logger.warning(f"Intento fallido login: {usuario}")
            return jsonify({
                "status": "error",
                "message": "Credenciales incorrectas"
            }), 401

        # ❌ usuario inactivo
        if int(activo) == 0:
            return jsonify({
                "status": "error",
                "message": "Usuario inactivo"
            }), 403

        # =============================
        # 🔥 SESIÓN
        # =============================
        session.clear()

        session.permanent = True  # 🔥 Habilitar sesión persistente

        session["user_id"] = user_id
        session["nombre"] = nombre
        session["nombreUsuario"] = nombre
        session["perfil"] = perfil

        return jsonify({
            "status": "success",
            "user": {
                "id": user_id,
                "nombre": nombre,
                "perfil": perfil
            }
        })

    except Exception as e:
        logger.exception("❌ ERROR LOGIN")
        return jsonify({
            "status": "error",
            "message": "Error interno"
        }), 500

    finally:
        if conn:
            conn.close()


# =============================
# 🔐 VALIDAR SESIÓN
# =============================
@auth_bp.route("/session", methods=["GET"])
def session_check():

    if "user_id" not in session:
        return jsonify({
            "status": "unauthorized"
        }), 401

    return jsonify({
        "status": "success",
        "user": {
            "id": session.get("user_id"),
            "nombre": session.get("nombre"),
            "perfil": session.get("perfil")
        }
    })


# =============================
# 🔐 LOGOUT
# =============================
@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({
        "status": "success"
    })