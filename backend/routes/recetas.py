from flask import Blueprint, request, jsonify, session
from services.recetas_service import crear_receta, obtener_receta

recetas_bp = Blueprint("recetas", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# 🧾 CREAR RECETA
# =============================
@recetas_bp.route("/recetas", methods=["POST"])
def crear():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json

        # 🔥 VALIDACIÓN REAL
        if not data:
            return jsonify({
                "status": "error",
                "message": "No se enviaron datos"
            }), 400

        if "producto_id" not in data or not data["producto_id"]:
            return jsonify({
                "status": "error",
                "message": "producto_id es obligatorio"
            }), 400

        if "detalle" not in data or not isinstance(data["detalle"], list) or len(data["detalle"]) == 0:
            return jsonify({
                "status": "error",
                "message": "Debe incluir ingredientes"
            }), 400

        # 🔥 VALIDAR CADA INGREDIENTE
        for d in data["detalle"]:
            if not d.get("insumo_id") or float(d.get("cantidad", 0)) <= 0:
                return jsonify({
                    "status": "error",
                    "message": "Ingredientes inválidos"
                }), 400

        # 🔥 TRAZABILIDAD
        data["usuario_id"] = session.get("user_id")

        result = crear_receta(data)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("❌ ERROR CREAR RECETA:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# 📄 OBTENER RECETA
# =============================
@recetas_bp.route("/recetas/<int:producto_id>", methods=["GET"])
def obtener(producto_id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = obtener_receta(producto_id)

        return jsonify({
            "status": "success",
            "detalle": data or []  # 🔥 evita null
        })

    except Exception as e:
        print("❌ ERROR OBTENER RECETA:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500