from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    send_file
)

from services.pedidos_service import (

    crear_pedido,

    get_pedidos,

    get_pedido_detalle,

    get_pedidos_kpis,

    facturar_pedido,

    exportar_pedidos

)

from openpyxl import Workbook

from utils.excel_utils import (

    crear_reporte_excel,

    guardar_workbook

)

from utils.report_configs import (

    construir_resumen_pedidos,

    obtener_hojas_pedidos

)

from datetime import datetime

import traceback

pedidos_bp = Blueprint("pedidos", __name__)


# =============================
# 🔐 HELPER AUTH
# =============================
def validar_sesion():
    return "user_id" in session


# =============================
# 🧾 CREAR PEDIDO
# =============================
@pedidos_bp.route("/pedidos", methods=["POST"])
def crear():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json

        if not data or "detalles" not in data or not data["detalles"]:
            return jsonify({
                "status": "error",
                "message": "Datos inválidos"
            }), 400

        # 🔥 agregar usuario desde sesión
        data["usuario_id"] = session.get("user_id")

        result = crear_pedido(data)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("❌ ERROR CREAR PEDIDO:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


# =============================
# 📦 VALIDAR STOCK
# =============================
#@pedidos_bp.route("/pedidos/validar-stock", methods=["POST"])
#def validar():

#    if not validar_sesion():
#        return jsonify({"status": "unauthorized"}), 401

#    try:
#        data = request.json

#        if not data or "detalles" not in data:
#            return jsonify({
#                "status": "error",
#                "message": "Datos inválidos"
#            }), 400

#       return jsonify(validar_stock_pedido(data))

#    except Exception as e:
#        print("❌ ERROR VALIDAR STOCK PEDIDO:", e)

#        return jsonify({
#            "status": "error",
#            "message": "Error validando stock"
#        }), 500


# =============================
# 📄 LISTAR PEDIDOS
# =============================
@pedidos_bp.route("/pedidos", methods=["GET"])
def listar():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_pedidos(

            request.args

        )

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR LISTAR PEDIDOS:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo pedidos"
        }), 500


# =====================================================
# 📊 EXPORTAR PEDIDOS A EXCEL
# =====================================================

@pedidos_bp.route(
    "/pedidos/exportar",
    methods=["GET"]
)
def exportar_excel_pedidos():

    if not validar_sesion():

        return jsonify({
            "status": "unauthorized"
        }), 401

    try:

        # ==========================================
        # FILTROS
        # ==========================================

        filtros = {

            "periodo":
                request.args.get(
                    "periodo"
                ),

            "fecha_inicio":
                request.args.get(
                    "fecha_inicio"
                ),

            "fecha_fin":
                request.args.get(
                    "fecha_fin"
                ),

            "estado":
                request.args.get(
                    "estado"
                ),

            "servicio":
                request.args.get(
                    "servicio"
                ),

            "buscar":
                request.args.get(
                    "buscar"
                )

        }

        print(
            "📊 FILTROS EXPORTAR PEDIDOS:"
        )

        print(filtros)

        # ==========================================
        # OBTENER DATOS
        # ==========================================

        data = exportar_pedidos(
            filtros
        )

        # ==========================================
        # CREAR WORKBOOK
        # ==========================================

        workbook = Workbook()

        workbook.remove(
            workbook.active
        )

        # ==========================================
        # RESUMEN FILTROS
        # ==========================================

        resumen = construir_resumen_pedidos(
            filtros
        )

        # ==========================================
        # CREAR HOJAS
        # ==========================================

        hojas = obtener_hojas_pedidos(
            data,
            resumen
        )

        # ==========================================
        # CONSTRUIR EXCEL
        # ==========================================

        crear_reporte_excel(
            workbook,
            hojas
        )

        # ==========================================
        # GUARDAR WORKBOOK
        # ==========================================

        output = guardar_workbook(
            workbook
        )

        # ==========================================
        # NOMBRE ARCHIVO
        # ==========================================

        nombre_archivo = (
            f"Reporte_Pedidos_"
            f"{datetime.now():%Y%m%d_%H%M%S}.xlsx"
        )

        # ==========================================
        # DESCARGAR
        # ==========================================

        return send_file(

            output,

            as_attachment=True,

            download_name=nombre_archivo,

            mimetype=(
                "application/"
                "vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            )

        )

    except Exception as e:

        print(
            "❌ ERROR EXPORTAR PEDIDOS:"
        )

        print(e)

        traceback.print_exc()

        return jsonify({

            "status": "error",

            "message":
                str(e)

        }), 500


# =============================
# 📊 KPIS PEDIDOS
# =============================
@pedidos_bp.route("/pedidos/kpis", methods=["GET"])
def obtener_kpis():

    if not validar_sesion():

        return jsonify({

            "status": "unauthorized"

        }), 401

    try:

        data = get_pedidos_kpis(

            request.args

        )

        return jsonify({

            "status": "success",

            "data": data

        })

    except Exception as e:

        print("❌ ERROR KPIS PEDIDOS:", e)

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500    


# =============================
# 🔍 DETALLE
# =============================
@pedidos_bp.route("/pedidos/<int:id>", methods=["GET"])
def detalle(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = get_pedido_detalle(id)

        if not data:
            return jsonify({
                "status": "error",
                "message": "Pedido no encontrado"
            }), 404

        return jsonify({
            "status": "success",
            "data": data
        })

    except Exception as e:
        print("❌ ERROR DETALLE PEDIDO:", e)

        return jsonify({
            "status": "error",
            "message": "Error obteniendo detalle"
        }), 500


# =============================
# 🔥 FACTURAR CON METODO PAGO
# =============================
@pedidos_bp.route("/pedidos/<int:id>/facturar", methods=["POST"])
def facturar(id):

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json or {}

        # 🔥 método de pago
        metodo_pago = data.get("metodo_pago", "Efectivo")

        # 🔥 usuario que factura
        usuario_id = session.get("user_id")

        result = facturar_pedido(id, metodo_pago, usuario_id)

        return jsonify({
            "status": "success",
            "data": result
        })

    except Exception as e:
        print("❌ ERROR FACTURAR PEDIDO:", e)

        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500


