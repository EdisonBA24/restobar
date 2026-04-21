from flask import Blueprint, request, jsonify, session
import pyodbc
from config import Config

auth_bp = Blueprint("auth", __name__)


def get_connection():
    return pyodbc.connect(Config.get_connection_string())


@auth_bp.route("/login", methods=["POST"])
def login():
    try:
        data = request.json

        conn = get_connection()
        cursor = conn.cursor()

        # 🔥 TRAEMOS TAMBIÉN EL ESTADO ACTIVO
        cursor.execute("""
            SELECT id, nombre, perfil, activo
            FROM usuarios
            WHERE usuario = ? AND password = ?
        """, (data["usuario"], data["password"]))

        user = cursor.fetchone()

        conn.close()

        # ❌ NO EXISTE USUARIO
        if not user:
            return jsonify({
                "status": "error",
                "message": "Credenciales incorrectas"
            }), 401

        # ❌ USUARIO INACTIVO
        if user[3] == 0:
            return jsonify({
                "status": "error",
                "message": "Usuario inactivo"
            }), 403

        # ✅ LOGIN OK
        session["user_id"] = user[0]
        session["nombre"] = user[1]
        session["nombreUsuario"] = user[1]
        session["perfil"] = user[2]

        return jsonify({
            "status": "success",
            "user": {
                "id": user[0],
                "nombre": user[1],
                "perfil": user[2]
            }
        })

    except Exception as e:
        print("ERROR LOGIN:", e)
        return jsonify({
            "status": "error",
            "message": "Error interno"
        }), 500


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return jsonify({"status": "success"})