
from datetime import datetime
import traceback

from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    send_file
)

from openpyxl import Workbook

from services.ventas_service import (
    crear_venta,
    get_ventas,
    get_venta_detalle
)

from services.ventas_reportes_service import (
    listar_ventas,
    obtener_kpis_ventas,
    exportar_ventas as obtener_datos_exportacion,
    VentasFiltroError
)

from utils.excel_utils import (
    crear_reporte_excel,
    guardar_workbook
)


ventas_bp = Blueprint("ventas", __name__)


# =====================================================
# VALIDACION DE SESION
# =====================================================

def validar_sesion():

    return "user_id" in session


def respuesta_no_autorizada():

    return jsonify({

        "status": "unauthorized",

        "message": "La sesión no está activa."

    }), 401


# =====================================================
# OBTENER FILTROS
# =====================================================

def obtener_filtros():

    return {

        "buscar": (
            request.args.get("buscar")
            or request.args.get("search")
            or ""
        ).strip(),

        "metodo_pago": (
            request.args.get("metodo_pago")
            or ""
        ).strip(),

        "fecha_inicio": (
            request.args.get("fecha_inicio")
            or ""
        ).strip(),

        "fecha_fin": (
            request.args.get("fecha_fin")
            or ""
        ).strip()

    }


# =====================================================
# COMPATIBILIDAD CON LISTADO ANTERIOR
#
# Si no se envian parametros, conserva la respuesta
# del endpoint original.
#
# Si se envian parametros, utiliza el nuevo servicio
# paginado y filtrado.
# =====================================================

def solicitar_listado_paginado():

    parametros = {

        "page",

        "page_size",

        "limit",

        "sort_by",

        "sort_order",

        "buscar",

        "search",

        "metodo_pago",

        "fecha_inicio",

        "fecha_fin"

    }

    return any(
        parametro in request.args
        for parametro in parametros
    )


# =====================================================
# CREAR VENTA
# =====================================================

@ventas_bp.route(
    "/ventas",
    methods=["POST"]
)
def crear():

    if not validar_sesion():

        return respuesta_no_autorizada()

    try:

        data = request.get_json(
            silent=True
        ) or {}

        if not data or "detalles" not in data:

            return jsonify({

                "status": "error",

                "message": "Datos inválidos."

            }), 400

        if (
            not isinstance(data["detalles"], list)
            or len(data["detalles"]) == 0
        ):

            return jsonify({

                "status": "error",

                "message": "Debe incluir al menos un producto."

            }), 400

        # =============================================
        # VALIDAR DETALLES
        # =============================================

        for detalle in data["detalles"]:

            if not isinstance(detalle, dict):

                return jsonify({

                    "status": "error",

                    "message": "Detalle de venta inválido."

                }), 400

            if not detalle.get("producto_id") and not (
                detalle.get("nombre_item")
            ):

                return jsonify({

                    "status": "error",

                    "message": "Cada detalle debe tener un producto o nombre de artículo."

                }), 400

            try:

                cantidad = float(
                    detalle.get("cantidad", 0)
                )

            except (ValueError, TypeError):

                cantidad = 0

            if cantidad <= 0:

                return jsonify({

                    "status": "error",

                    "message": "La cantidad debe ser mayor a cero."

                }), 400

        # =============================================
        # REGISTRAR VENTA
        # =============================================

        result = crear_venta(data)

        return jsonify({

            "status": "success",

            "data": result

        }), 201

    except Exception as e:

        print(
            "ERROR CREAR VENTA:",
            e
        )

        traceback.print_exc()

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 500


# =====================================================
# LISTAR VENTAS
#
# GET /api/ventas
#
# Sin parametros:
# conserva el listado tradicional.
#
# Con parametros:
# utiliza paginacion, filtros y ordenamiento.
# =====================================================

@ventas_bp.route(
    "/ventas",
    methods=["GET"]
)
def listar():

    if not validar_sesion():

        return respuesta_no_autorizada()

    try:

        # =============================================
        # LISTADO ANTERIOR
        # =============================================

        if not solicitar_listado_paginado():

            data = get_ventas()

            return jsonify({

                "status": "success",

                "data": data

            }), 200

        # =============================================
        # NUEVO LISTADO
        # =============================================

        data = listar_ventas(
            request.args
        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except VentasFiltroError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR LISTAR VENTAS:",
            e
        )

        traceback.print_exc()

        return jsonify({

            "status": "error",

            "message": "Error obteniendo el historial de ventas."

        }), 500


# =====================================================
# KPIS DE VENTAS
#
# GET /api/ventas/kpis
#
# Respeta los filtros:
# - Busqueda.
# - Metodo de pago.
# - Fecha inicial.
# - Fecha final.
# =====================================================

@ventas_bp.route(
    "/ventas/kpis",
    methods=["GET"]
)
def obtener_kpis():

    if not validar_sesion():

        return respuesta_no_autorizada()

    try:

        filtros = obtener_filtros()

        data = obtener_kpis_ventas(
            filtros
        )

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except VentasFiltroError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR KPIS VENTAS:",
            e
        )

        traceback.print_exc()

        return jsonify({

            "status": "error",

            "message": "No fue posible calcular los indicadores de ventas."

        }), 500


# =====================================================
# EXPORTAR VENTAS A EXCEL
#
# GET /api/ventas/exportar
#
# HOJA 1:
# Encabezados de ventas.
#
# HOJA 2:
# Detalle de productos vendidos.
#
# No utiliza paginacion.
# Respeta los filtros aplicados.
# =====================================================

@ventas_bp.route(
    "/ventas/exportar",
    methods=["GET"]
)
def exportar_excel():

    if not validar_sesion():

        return respuesta_no_autorizada()

    try:

        # =============================================
        # FILTROS
        # =============================================

        filtros = obtener_filtros()

        print(
            "FILTROS EXPORTAR VENTAS:"
        )

        print(filtros)

        # =============================================
        # CONSULTAR INFORMACION
        # =============================================

        data = obtener_datos_exportacion(
            filtros
        )

        ventas = data.get(
            "ventas",
            []
        )

        detalles = data.get(
            "detalle",
            []
        )

        kpis = data.get(
            "kpis",
            {}
        )

        # =============================================
        # VALIDAR RESULTADOS
        # =============================================

        if not ventas:

            return jsonify({

                "status": "error",

                "message": "No hay ventas registradas para los filtros seleccionados."

            }), 400

        # =============================================
        # CREAR WORKBOOK
        # =============================================

        workbook = Workbook()

        workbook.remove(
            workbook.active
        )

        # =============================================
        # RESUMEN DEL REPORTE
        # =============================================

        resumen = [

            (
                "Fecha de generación",
                datetime.now().strftime("%d/%m/%Y %H:%M")
            ),

            (
                "Fecha inicial",
                filtros.get("fecha_inicio") or "Todas"
            ),

            (
                "Fecha final",
                filtros.get("fecha_fin") or "Todas"
            ),

            (
                "Método de pago",
                filtros.get("metodo_pago") or "Todos"
            ),

            (
                "Búsqueda",
                filtros.get("buscar") or "Todas"
            ),

            (
                "Cantidad de ventas",
                kpis.get("total_ventas", 0)
            ),

            (
                "Total vendido (COP)",
                kpis.get("total_vendido", 0)
            ),

            (
                "Clientes identificados",
                kpis.get("clientes_identificados", 0)
            ),

            (
                "Ticket promedio (COP)",
                kpis.get("ticket_promedio", 0)
            )

        ]

        # =============================================
        # HOJA 1: VENTAS
        # =============================================

        hoja_ventas = {

            "nombre_hoja": "Ventas",

            "titulo": "HISTORIAL DE VENTAS",

            "resumen": resumen,

            "encabezados": [

                "Venta",

                "Fecha",

                "Cliente",

                "Mesa",

                "Método de pago",

                "Categoría",

                "Usuario",

                "Total (COP)"

            ],

            "columnas": [

                "id",

                "fecha",

                "cliente",

                "mesa",

                "metodo_pago",

                "categoria",

                "usuario",

                "total"

            ],

            "datos": ventas,

            "columnas_moneda": [

                8

            ],

            "columnas_totales": {

                "total": 8

            },

            "columnas_width": {

                1: 12,

                2: 22,

                3: 30,

                4: 12,

                5: 20,

                6: 22,

                7: 22,

                8: 22

            }

        }

        # =============================================
        # HOJA 2: DETALLE DE VENTAS
        # =============================================

        hoja_detalle = {

            "nombre_hoja": "Detalle ventas",

            "titulo": "DETALLE DE PRODUCTOS VENDIDOS",

            "resumen": resumen,

            "encabezados": [

                "Venta",

                "Fecha",

                "Cliente",

                "Método de pago",

                "Usuario",

                "Producto",

                "Tipo",

                "Cantidad",

                "Precio unitario (COP)",

                "Subtotal (COP)"

            ],

            "columnas": [

                "venta_id",

                "fecha",

                "cliente",

                "metodo_pago",

                "usuario",

                "producto",

                "tipo_item",

                "cantidad",

                "precio",

                "subtotal"

            ],

            "datos": detalles,

            "columnas_moneda": [

                9,

                10

            ],

            "columnas_decimal": [

                8

            ],

            "columnas_totales": {

                "subtotal": 10

            },

            "columnas_width": {

                1: 12,

                2: 22,

                3: 28,

                4: 20,

                5: 22,

                6: 35,

                7: 20,

                8: 14,

                9: 24,

                10: 22

            }

        }

        # =============================================
        # CONSTRUIR HOJAS
        # =============================================

        crear_reporte_excel(

            workbook,

            [

                hoja_ventas,

                hoja_detalle

            ]

        )

        # =============================================
        # GUARDAR EN MEMORIA
        # =============================================

        output = guardar_workbook(
            workbook
        )

        # =============================================
        # NOMBRE DEL ARCHIVO
        # =============================================

        nombre_archivo = (

            f"Reporte_Ventas_"

            f"{datetime.now():%Y%m%d_%H%M%S}.xlsx"

        )

        # =============================================
        # DESCARGAR
        # =============================================

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

    except VentasFiltroError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR EXPORTAR VENTAS:"
        )

        print(e)

        traceback.print_exc()

        return jsonify({

            "status": "error",

            "message": "No fue posible generar el reporte Excel de ventas."

        }), 500


# =====================================================
# DETALLE DE VENTA
#
# Se conserva el endpoint original.
# =====================================================

@ventas_bp.route(
    "/ventas/<int:id>",
    methods=["GET"]
)
def detalle(id):

    if not validar_sesion():

        return respuesta_no_autorizada()

    try:

        data = get_venta_detalle(id)

        if not data:

            return jsonify({

                "status": "error",

                "message": "Venta no encontrada."

            }), 404

        return jsonify({

            "status": "success",

            "data": data

        }), 200

    except Exception as e:

        print(
            "ERROR DETALLE VENTA:",
            e
        )

        traceback.print_exc()

        return jsonify({

            "status": "error",

            "message": "Error obteniendo el detalle de la venta."

        }), 500
