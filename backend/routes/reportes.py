from flask import Blueprint, request, jsonify, send_file, session
import pandas as pd
import io
from services.reportes_service import (
    reporte_inventario as obtener_reporte_inventario,
    reporte_ventas as obtener_reporte_ventas,
    reporte_costos as obtener_reporte_costos,
)


reportes_bp = Blueprint("reportes", __name__)


# =============================
# 🔐 HELPERS
# =============================
def validar_sesion():
    return "user_id" in session


# ==========================
# 📦 REPORTE DE INVENTARIO
# ==========================

# ======================================================
# TODO (Módulo Inventario)
#
# Este reporte es temporal.
#
# Actualmente consulta el stock almacenado directamente
# en la tabla PRODUCTOS.
#
# En la siguiente fase del proyecto, este endpoint deberá
# obtener la información desde inventario_service.py,
# evitando acceder directamente a la base de datos.
#
# Funcionalidades futuras:
# - Stock disponible
# - Stock mínimo
# - Stock máximo
# - Valor del inventario
# - Último costo
# - Último movimiento
# - Kardex de movimientos
# ======================================================

@reportes_bp.route("/reportes/inventario", methods=["GET"])
def reporte_inventario():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        return jsonify(obtener_reporte_inventario())

    except Exception as e:
        print("❌ ERROR obteniendo reporte:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ==========================
# 💰 REPORTE DE VENTAS
# ==========================

# ======================================================
# TODO (Módulo Ventas)
#
# Este reporte actualmente obtiene la información
# directamente desde la tabla VENTAS.
#
# Si en el futuro las ventas incluyen nuevos estados,
# múltiples métodos de pago o facturación electrónica,
# este endpoint deberá consumir ventas_service.py para
# centralizar la lógica de negocio.
#
# Posibles mejoras:
# - Método de pago
# - Cajero
# - Cliente
# - Estado de la venta
# - Número de factura
# ======================================================

@reportes_bp.route("/reportes/ventas", methods=["GET"])
def reporte_ventas():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        inicio = request.args.get("inicio")
        fin = request.args.get("fin")
        return jsonify(obtener_reporte_ventas(inicio, fin))

    except Exception as e:
        print("❌ ERROR obteniendo reporte:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ==========================
# 📊 REPORTE DE COSTOS
# ==========================

# ======================================================
# TODO (Módulo Inventario / Costos)
#
# El cálculo de costos fue desacoplado completamente del
# módulo de Ventas y Reportes.
#
# En una siguiente fase este endpoint consumirá
# inventario_service.py, el cual calculará:
#
# - costo de receta
# - costo promedio
# - utilidad
# - margen
# - costo por ingrediente
# - conversiones de unidades
#
# Se conserva el endpoint para no afectar el frontend.
# ======================================================

@reportes_bp.route("/reportes/costos", methods=["GET"])
def reporte_costos():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        return jsonify(obtener_reporte_costos())

    except Exception as e:
        print("❌ ERROR obteniendo reporte:", e)
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# ==========================
# 📥 EXPORTAR EXCEL
# ==========================
@reportes_bp.route("/reportes/exportar", methods=["POST"])
def exportar_excel():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json.get("data", [])
        nombre = request.json.get("nombre", "reporte")

        if not data:
            return jsonify({
                "status": "error",
                "message": "No hay datos para exportar"
            }), 400

        df = pd.DataFrame(data)
        df.fillna("", inplace=True)

        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        return send_file(
            output,
            download_name=f"{nombre}.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print("❌ ERROR EXPORTAR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500