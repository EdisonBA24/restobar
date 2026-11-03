
from datetime import date, datetime

from flask import (
    Blueprint,
    request,
    jsonify,
    session,
    send_file
)

from openpyxl import Workbook

from services.pagos_service import (
    crear_pago,
    get_pagos,
    get_pagos_legacy,
    PagoValidationError
)

from services.pagos_reportes_service import (
    get_pagos_resumen,
    exportar_pagos as obtener_datos_exportacion
)

from utils.excel_utils import (
    crear_reporte_excel,
    guardar_workbook
)


pagos_bp = Blueprint("pagos", __name__)


# =====================================================
# VALIDAR ACCESO ADMINISTRADOR
# =====================================================

def validar_admin():

    if not session.get("user_id"):
        return "unauthorized"

    perfil = str(
        session.get("perfil") or ""
    ).strip().lower()

    if perfil != "admin":
        return "forbidden"

    return None


def _respuesta_acceso():

    estado = validar_admin()

    if estado == "unauthorized":

        return jsonify({

            "status": "unauthorized",

            "message": "La sesión no está activa."

        }), 401

    if estado == "forbidden":

        return jsonify({

            "status": "error",

            "message": "No tienes permisos para acceder al módulo de Pagos."

        }), 403

    return None


# =====================================================
# VALIDAR ENTEROS DE PAGINACION
# =====================================================

def _parsear_entero(
    valor,
    nombre,
    default,
    minimo=1
):

    try:

        resultado = int(
            valor if valor is not None else default
        )

    except (TypeError, ValueError):

        raise PagoValidationError(
            f"El parámetro '{nombre}' debe ser un número entero."
        )

    if resultado < minimo:

        raise PagoValidationError(
            f"El parámetro '{nombre}' debe ser mayor o igual a {minimo}."
        )

    return resultado


# =====================================================
# OBTENER FILTROS DEL HISTORIAL
#
# Estos mismos filtros se utilizan para:
# - Resumen financiero.
# - Exportación Excel.
#
# Así se garantiza que todos los resultados
# correspondan a la misma consulta.
# =====================================================

def _obtener_filtros_pagos():

    return {

        "search": request.args.get(
            "search",
            ""
        ).strip(),

        "fecha_inicio": request.args.get(
            "fecha_inicio"
        ),

        "fecha_fin": request.args.get(
            "fecha_fin"
        )

    }


# =====================================================
# PROTEGER TEXTOS PARA EXCEL
#
# Evita que los textos ingresados por usuarios
# se interpreten como fórmulas al abrir el archivo.
# =====================================================

def _texto_seguro_excel(valor):

    if not isinstance(valor, str):
        return valor

    texto = valor.strip()

    if texto.startswith(("=", "+", "-", "@")):

        return "'" + valor

    return valor


# =====================================================
# NORMALIZAR FECHAS PARA EXCEL
# =====================================================

def _fecha_excel(valor):

    if valor is None:
        return None

    if isinstance(valor, datetime):

        return valor.replace(
            tzinfo=None
        )

    if isinstance(valor, date):
        return valor

    texto = str(valor).strip()

    if not texto:
        return None

    try:

        if "T" in texto or " " in texto:

            fecha = datetime.fromisoformat(
                texto.replace("Z", "+00:00")
            )

            return fecha.replace(
                tzinfo=None
            )

        return date.fromisoformat(texto)

    except (ValueError, TypeError):

        return texto


# =====================================================
# SANEAR DATOS DEL DETALLE PARA EXCEL
# =====================================================

def _preparar_detalle_excel(detalle):

    resultado = []

    for pago in detalle:

        resultado.append({

            "id": pago.get("id"),

            "fecha": _fecha_excel(
                pago.get("fecha")
            ),

            "empleado": _texto_seguro_excel(
                pago.get("empleado") or ""
            ),

            "concepto": _texto_seguro_excel(
                pago.get("concepto") or ""
            ),

            "monto": pago.get("monto") or 0

        })

    return resultado


# =====================================================
# SANEAR AGRUPACION POR EMPLEADO PARA EXCEL
# =====================================================

def _preparar_empleados_excel(registros):

    resultado = []

    for registro in registros:

        resultado.append({

            "empleado": _texto_seguro_excel(
                registro.get("empleado") or ""
            ),

            "cantidad_pagos": registro.get(
                "cantidad_pagos", 0
            ),

            "total_pagado": registro.get(
                "total_pagado", 0
            ),

            "promedio_pago": registro.get(
                "promedio_pago", 0
            )

        })

    return resultado


# =====================================================
# LISTAR PAGOS
# =====================================================

@pagos_bp.route("/pagos", methods=["GET"])
def listar_pagos():

    acceso = _respuesta_acceso()

    if acceso:
        return acceso

    try:

        # =============================================
        # COMPATIBILIDAD CON FRONTEND ANTERIOR
        #
        # GET /pagos sin parámetros sigue devolviendo
        # una lista simple.
        # =============================================

        parametros_nuevos = {

            "page",

            "limit",

            "page_size",

            "search",

            "fecha_inicio",

            "fecha_fin",

            "sort_by",

            "sort_order"

        }

        usa_paginacion = any(
            parametro in request.args
            for parametro in parametros_nuevos
        )

        if not usa_paginacion:

            data = get_pagos_legacy()

            return jsonify({

                "status": "success",

                "data": data

            })

        # =============================================
        # PAGINACION
        # =============================================

        page = _parsear_entero(
            request.args.get("page"),
            "page",
            default=1
        )

        limit = _parsear_entero(
            request.args.get(
                "limit",
                request.args.get("page_size")
            ),
            "limit",
            default=10
        )

        limit = min(limit, 100)

        # =============================================
        # FILTROS
        # =============================================

        search = request.args.get(
            "search",
            ""
        ).strip()

        fecha_inicio = request.args.get(
            "fecha_inicio"
        )

        fecha_fin = request.args.get(
            "fecha_fin"
        )

        # =============================================
        # ORDENAMIENTO
        # =============================================

        sort_by = request.args.get(
            "sort_by",
            "id"
        )

        sort_order = request.args.get(
            "sort_order",
            "desc"
        )

        # =============================================
        # CONSULTAR
        # =============================================

        data = get_pagos(

            page=page,

            limit=limit,

            search=search,

            fecha_inicio=fecha_inicio,

            fecha_fin=fecha_fin,

            sort_by=sort_by,

            sort_order=sort_order

        )

        return jsonify({

            "status": "success",

            "data": data

        })

    except PagoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR LISTAR PAGOS:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible consultar los pagos."

        }), 500


# =====================================================
# REGISTRAR PAGO
# =====================================================

@pagos_bp.route("/pagos", methods=["POST"])
def crear():

    acceso = _respuesta_acceso()

    if acceso:
        return acceso

    data = request.get_json(
        silent=True
    ) or {}

    if not data:

        return jsonify({

            "status": "error",

            "message": "No se enviaron datos del pago."

        }), 400

    try:

        resultado = crear_pago(data)

        return jsonify({

            "status": "success",

            "message": resultado

        }), 201

    except PagoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR CREAR PAGO:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible registrar el pago."

        }), 500


# =====================================================
# RESUMEN FINANCIERO DE PAGOS
#
# GET /api/pagos/resumen
#
# Parámetros:
# search
# fecha_inicio
# fecha_fin
# =====================================================

@pagos_bp.route("/pagos/resumen", methods=["GET"])
def resumen_pagos():

    acceso = _respuesta_acceso()

    if acceso:
        return acceso

    try:

        filtros = _obtener_filtros_pagos()

        resumen = get_pagos_resumen(
            filtros
        )

        return jsonify({

            "status": "success",

            "data": resumen

        }), 200

    except PagoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR RESUMEN PAGOS:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible generar el resumen financiero de pagos."

        }), 500


# =====================================================
# EXPORTAR PAGOS A EXCEL
#
# GET /api/pagos/exportar
#
# Genera dos hojas:
#
# 1. Resumen por empleado.
# 2. Detalle completo de pagos.
#
# Respeta los filtros actuales de consulta.
# No depende de la paginación de la tabla.
# =====================================================

@pagos_bp.route("/pagos/exportar", methods=["GET"])
def exportar_pagos_excel():

    acceso = _respuesta_acceso()

    if acceso:
        return acceso

    try:

        # =============================================
        # OBTENER FILTROS
        # =============================================

        filtros = _obtener_filtros_pagos()

        # =============================================
        # OBTENER INFORMACION COMPLETA
        # =============================================

        resultado = obtener_datos_exportacion(
            filtros
        )

        resumen = resultado.get(
            "resumen",
            {}
        )

        detalle = resultado.get(
            "detalle",
            []
        )

        empleados = resultado.get(
            "por_empleado",
            []
        )

        if not detalle:

            return jsonify({

                "status": "error",

                "message": "No hay pagos registrados para los filtros seleccionados."

            }), 400

        # =============================================
        # PREPARAR DATOS
        # =============================================

        detalle_excel = _preparar_detalle_excel(
            detalle
        )

        empleados_excel = _preparar_empleados_excel(
            empleados
        )

        # =============================================
        # INFORMACION DE FILTROS Y RESUMEN
        # =============================================

        resumen_filtros = [

            (
                "Búsqueda",
                _texto_seguro_excel(
                    filtros.get("search") or "Sin filtro"
                )
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
                "Cantidad de pagos",
                resumen.get("cantidad_pagos", 0)
            ),

            (
                "Total pagado (COP)",
                resumen.get("total_pagado", 0)
            ),

            (
                "Empleados con pagos",
                resumen.get("empleados", 0)
            ),

            (
                "Promedio por pago (COP)",
                resumen.get("promedio_pago", 0)
            )

        ]

        # =============================================
        # CREAR LIBRO
        # =============================================

        workbook = Workbook()

        workbook.remove(
            workbook.active
        )

        # =============================================
        # CONFIGURAR HOJAS
        # =============================================

        hojas = [

            # -----------------------------------------
            # HOJA 1: RESUMEN POR EMPLEADO
            # -----------------------------------------

            {

                "nombre_hoja": "Resumen por empleado",

                "titulo": "RESUMEN DE PAGOS POR EMPLEADO",

                "resumen": resumen_filtros,

                "encabezados": [

                    "Empleado",

                    "Cantidad de pagos",

                    "Total pagado (COP)",

                    "Promedio por pago (COP)"

                ],

                "columnas": [

                    "empleado",

                    "cantidad_pagos",

                    "total_pagado",

                    "promedio_pago"

                ],

                "datos": empleados_excel,

                "columnas_moneda": [
                    3,
                    4
                ],

                "columnas_totales": {

                    "cantidad_pagos": 2,

                    "total_pagado": 3

                },

                "columnas_width": {

                    1: 30,

                    2: 20,

                    3: 25,

                    4: 28

                }

            },

            # -----------------------------------------
            # HOJA 2: DETALLE COMPLETO
            # -----------------------------------------

            {

                "nombre_hoja": "Detalle de pagos",

                "titulo": "DETALLE DE PAGOS REGISTRADOS",

                "resumen": resumen_filtros,

                "encabezados": [

                    "ID",

                    "Fecha",

                    "Empleado",

                    "Concepto",

                    "Monto (COP)"

                ],

                "columnas": [

                    "id",

                    "fecha",

                    "empleado",

                    "concepto",

                    "monto"

                ],

                "datos": detalle_excel,

                "columnas_moneda": [
                    5
                ],

                "columnas_totales": {

                    "monto": 5

                },

                "columnas_width": {

                    1: 12,

                    2: 22,

                    3: 30,

                    4: 40,

                    5: 22

                }

            }

        ]

        # =============================================
        # GENERAR EXCEL CON UTILIDAD DEL PROYECTO
        # =============================================

        crear_reporte_excel(
            workbook,
            hojas
        )

        # =============================================
        # FORMATO DE FECHA EN EXCEL
        # =============================================

        ws_detalle = workbook[
            "Detalle de pagos"
        ]

        for fila in ws_detalle.iter_rows(
            min_col=2,
            max_col=2
        ):

            celda = fila[0]

            if isinstance(celda.value, datetime):

                celda.number_format = "dd/mm/yyyy hh:mm"

            elif isinstance(celda.value, date):

                celda.number_format = "dd/mm/yyyy"

        # =============================================
        # GUARDAR EN MEMORIA
        # =============================================

        archivo = guardar_workbook(
            workbook
        )

        # =============================================
        # NOMBRE DEL ARCHIVO
        # =============================================

        nombre_archivo = (
            "pagos_"
            + datetime.now().strftime("%Y%m%d_%H%M%S")
            + ".xlsx"
        )

        # =============================================
        # DESCARGAR ARCHIVO
        # =============================================

        return send_file(

            archivo,

            mimetype=(
                "application/vnd.openxmlformats-officedocument."
                "spreadsheetml.sheet"
            ),

            as_attachment=True,

            download_name=nombre_archivo

        )

    except PagoValidationError as e:

        return jsonify({

            "status": "error",

            "message": str(e)

        }), 400

    except Exception as e:

        print(
            "ERROR EXPORTAR PAGOS:",
            e
        )

        return jsonify({

            "status": "error",

            "message": "No fue posible generar el archivo Excel de pagos."

        }), 500
