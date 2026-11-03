
from datetime import date, datetime, timedelta
from decimal import Decimal

from config import Config
from database.connection import get_connection
from database.db_objects import PAGOS, USUARIOS
from services.pagos_service import PagoValidationError


# =====================================================
# CONFIGURACION DE BASE DE DATOS
# =====================================================

def _get_db_settings():

    engine = str(
        getattr(Config, "DB_ENGINE", "sqlserver") or "sqlserver"
    ).strip().lower()

    is_postgres = engine == "postgres"

    placeholder = "%s" if is_postgres else "?"

    return is_postgres, placeholder


# =====================================================
# EXPRESION DEL NOMBRE DEL EMPLEADO
# =====================================================

def _expresion_empleado():

    return """
        COALESCE(
            NULLIF(LTRIM(RTRIM(p.empleado)), ''),
            u.nombre,
            'Empleado no disponible'
        )
    """


# =====================================================
# VALIDAR FECHAS DE LOS FILTROS
# =====================================================

def _parsear_fecha_filtro(valor, campo):

    if valor is None or str(valor).strip() == "":
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    texto = str(valor).strip()

    try:

        if "T" in texto or " " in texto:

            return datetime.fromisoformat(
                texto.replace("Z", "+00:00")
            ).date()

        return date.fromisoformat(texto)

    except (ValueError, TypeError):

        raise PagoValidationError(
            f"El campo '{campo}' debe tener formato YYYY-MM-DD."
        )


# =====================================================
# CONSTRUIR FILTROS SQL
#
# Mantiene los mismos filtros que utiliza el listado:
# - Busqueda por empleado o concepto.
# - Fecha inicial.
# - Fecha final.
#
# La fecha final se maneja con limite exclusivo
# para incluir todos los registros de ese día.
# =====================================================

def _construir_filtros_pagos(filtros=None):

    if filtros is None:
        filtros = {}

    if not isinstance(filtros, dict):

        raise PagoValidationError(
            "Los filtros enviados no son válidos."
        )

    _, placeholder = _get_db_settings()

    condiciones = []
    parametros = []

    empleado_expr = _expresion_empleado()

    # ---------------------------------------------
    # BUSQUEDA
    # ---------------------------------------------

    busqueda = str(
        filtros.get("search") or filtros.get("buscar") or ""
    ).strip()[:100].lower()

    if busqueda:

        like = f"%{busqueda}%"

        condiciones.append(
            f"""
            (
                LOWER(COALESCE({empleado_expr}, ''))
                LIKE {placeholder}

                OR

                LOWER(COALESCE(p.concepto, ''))
                LIKE {placeholder}
            )
            """
        )

        parametros.extend([
            like,
            like
        ])

    # ---------------------------------------------
    # FECHA INICIAL
    # ---------------------------------------------

    fecha_inicio = _parsear_fecha_filtro(
        filtros.get("fecha_inicio"),
        "fecha_inicio"
    )

    # ---------------------------------------------
    # FECHA FINAL
    # ---------------------------------------------

    fecha_fin = _parsear_fecha_filtro(
        filtros.get("fecha_fin"),
        "fecha_fin"
    )

    if (
        fecha_inicio
        and fecha_fin
        and fecha_fin < fecha_inicio
    ):

        raise PagoValidationError(
            "La fecha final no puede ser anterior a la fecha inicial."
        )

    if fecha_inicio:

        condiciones.append(
            f"p.fecha >= {placeholder}"
        )

        parametros.append(fecha_inicio)

    if fecha_fin:

        condiciones.append(
            f"p.fecha < {placeholder}"
        )

        parametros.append(
            fecha_fin + timedelta(days=1)
        )

    where_sql = (
        "WHERE " + " AND ".join(condiciones)
        if condiciones
        else ""
    )

    return where_sql, tuple(parametros)


# =====================================================
# NORMALIZAR VALORES NUMERICOS
# =====================================================

def _normalizar_numero(valor):

    if valor is None:
        return 0.0

    if isinstance(valor, Decimal):
        return float(valor)

    return float(valor or 0)


# =====================================================
# NORMALIZAR FECHAS PARA EXPORTACION
# =====================================================

def _normalizar_fecha(valor):

    if valor is None:
        return None

    if isinstance(valor, datetime):

        return valor.isoformat(
            sep=" ",
            timespec="seconds"
        )

    if isinstance(valor, date):
        return valor.isoformat()

    return str(valor)


# =====================================================
# CONVERTIR RESULTADOS SQL A DICCIONARIOS
# =====================================================

def _obtener_registros(cursor):

    columnas = [
        columna[0]
        for columna in cursor.description
    ]

    return [
        dict(zip(columnas, fila))
        for fila in cursor.fetchall()
    ]


# =====================================================
# CONSULTAR INDICADORES FINANCIEROS
# =====================================================

def _consultar_resumen(cursor, where_sql, parametros, placeholder):

    cursor.execute(
        f"""
        SELECT

            COUNT(*) AS cantidad_pagos,

            COALESCE(
                SUM(p.monto),
                0
            ) AS total_pagado,

            COUNT(
                DISTINCT p.usuario_id
            ) AS empleados,

            COALESCE(
                AVG(p.monto),
                0
            ) AS promedio_pago

        FROM {PAGOS} p

        LEFT JOIN {USUARIOS} u
            ON p.usuario_id = u.id

        {where_sql}
        """,
        parametros
    )

    fila = cursor.fetchone()

    if not fila:

        return {
            "cantidad_pagos": 0,
            "total_pagado": 0.0,
            "empleados": 0,
            "promedio_pago": 0.0
        }

    return {

        "cantidad_pagos": int(
            fila[0] or 0
        ),

        "total_pagado": _normalizar_numero(
            fila[1]
        ),

        "empleados": int(
            fila[2] or 0
        ),

        "promedio_pago": _normalizar_numero(
            fila[3]
        )

    }


# =====================================================
# OBTENER RESUMEN FINANCIERO DE PAGOS
#
# Utilizado por los indicadores del frontend.
# Respeta exactamente los filtros seleccionados.
# =====================================================

def get_pagos_resumen(filtros=None):

    where_sql, parametros = _construir_filtros_pagos(
        filtros
    )

    _, placeholder = _get_db_settings()

    conn = None

    try:

        conn = get_connection()

        cursor = conn.cursor()

        resumen = _consultar_resumen(
            cursor,
            where_sql,
            parametros,
            placeholder
        )

        return resumen

    finally:

        if conn:
            conn.close()


# =====================================================
# EXPORTAR PAGOS
#
# Consulta todos los registros filtrados.
# No utiliza paginacion.
#
# Retorna:
# - resumen: indicadores financieros.
# - detalle: todos los pagos.
# - por_empleado: agrupacion por empleado.
# =====================================================

def exportar_pagos(filtros=None):

    where_sql, parametros = _construir_filtros_pagos(
        filtros
    )

    _, placeholder = _get_db_settings()

    empleado_expr = _expresion_empleado()

    conn = None

    try:

        conn = get_connection()

        cursor = conn.cursor()

        # -----------------------------------------
        # RESUMEN GENERAL
        # -----------------------------------------

        resumen = _consultar_resumen(
            cursor,
            where_sql,
            parametros,
            placeholder
        )

        # -----------------------------------------
        # DETALLE COMPLETO DE PAGOS
        # -----------------------------------------

        query_detalle = f"""
            SELECT

                p.id,

                p.fecha,

                {empleado_expr} AS empleado,

                p.concepto,

                p.monto,

                p.usuario_id

            FROM {PAGOS} p

            LEFT JOIN {USUARIOS} u
                ON p.usuario_id = u.id

            {where_sql}

            ORDER BY
                p.fecha DESC,
                p.id DESC
        """

        cursor.execute(
            query_detalle,
            parametros
        )

        detalle = _obtener_registros(cursor)

        # -----------------------------------------
        # NORMALIZAR DETALLE
        # -----------------------------------------

        for pago in detalle:

            pago["id"] = int(
                pago.get("id") or 0
            )

            pago["usuario_id"] = (
                int(pago["usuario_id"])
                if pago.get("usuario_id") is not None
                else None
            )

            pago["fecha"] = _normalizar_fecha(
                pago.get("fecha")
            )

            pago["empleado"] = str(
                pago.get("empleado") or "Empleado no disponible"
            )

            pago["concepto"] = str(
                pago.get("concepto") or ""
            )

            pago["monto"] = _normalizar_numero(
                pago.get("monto")
            )

        # -----------------------------------------
        # RESUMEN AGRUPADO POR EMPLEADO
        # -----------------------------------------

        query_empleados = f"""
            SELECT

                p.usuario_id AS usuario_id,

                {empleado_expr} AS empleado,

                COUNT(*) AS cantidad_pagos,

                COALESCE(
                    SUM(p.monto),
                    0
                ) AS total_pagado,

                COALESCE(
                    AVG(p.monto),
                    0
                ) AS promedio_pago

            FROM {PAGOS} p

            LEFT JOIN {USUARIOS} u
                ON p.usuario_id = u.id

            {where_sql}

            GROUP BY
                p.usuario_id,
                {empleado_expr}

            ORDER BY
                total_pagado DESC,
                empleado ASC
        """

        cursor.execute(
            query_empleados,
            parametros
        )

        por_empleado = _obtener_registros(cursor)

        # -----------------------------------------
        # NORMALIZAR AGRUPACION
        # -----------------------------------------

        for registro in por_empleado:

            registro["usuario_id"] = (
                int(registro["usuario_id"])
                if registro.get("usuario_id") is not None
                else None
            )

            registro["empleado"] = str(
                registro.get("empleado") or "Empleado no disponible"
            )

            registro["cantidad_pagos"] = int(
                registro.get("cantidad_pagos") or 0
            )

            registro["total_pagado"] = _normalizar_numero(
                registro.get("total_pagado")
            )

            registro["promedio_pago"] = _normalizar_numero(
                registro.get("promedio_pago")
            )

        return {

            "resumen": resumen,

            "detalle": detalle,

            "por_empleado": por_empleado

        }

    finally:

        if conn:
            conn.close()
