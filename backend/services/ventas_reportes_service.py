
import math
from datetime import date, datetime
from decimal import Decimal

from config import Config
from database.connection import get_connection
from database.db_objects import (
    VENTAS,
    DETALLE_VENTAS,
    USUARIOS
)


# =====================================================
# EXCEPCION DE VALIDACION
# =====================================================

class VentasFiltroError(ValueError):
    pass


# =====================================================
# COLUMNAS PERMITIDAS PARA ORDENAMIENTO
# =====================================================

COLUMNAS_ORDEN_VENTAS = {

    "id": "v.id",

    "fecha": "v.fecha",

    "cliente": "v.cliente",

    "total": "v.total",

    "usuario": "u.nombre",

    "metodo_pago": "v.metodo_pago",

    "mesa": "v.mesa",

    "categoria": "v.categoria"

}


# =====================================================
# CONFIGURACION BASE DE DATOS
# =====================================================

def _configuracion_bd():

    is_postgres = (
        str(
            getattr(Config, "DB_ENGINE", "sqlserver")
        ).strip().lower() == "postgres"
    )

    placeholder = "%s" if is_postgres else "?"

    return is_postgres, placeholder


# =====================================================
# VALIDAR FECHAS
# =====================================================

def _parsear_fecha(valor, nombre):

    if valor is None or str(valor).strip() == "":
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    try:

        return date.fromisoformat(
            str(valor).strip()
        )

    except (ValueError, TypeError):

        raise VentasFiltroError(
            f"La fecha '{nombre}' debe tener formato YYYY-MM-DD."
        )


# =====================================================
# NORMALIZAR PARAMETROS DE CONSULTA
# =====================================================

def _obtener_parametros_ventas(args=None):

    if args is None:
        args = {}

    try:

        page = int(
            args.get("page") or 1
        )

        page_size = int(
            args.get("page_size")
            or args.get("limit")
            or 10
        )

    except (ValueError, TypeError):

        raise VentasFiltroError(
            "La paginación contiene valores inválidos."
        )

    if page < 1:

        raise VentasFiltroError(
            "La página debe ser mayor o igual a 1."
        )

    if page_size < 1:

        raise VentasFiltroError(
            "El tamaño de página debe ser mayor a cero."
        )

    page_size = min(page_size, 100)

    fecha_inicio = _parsear_fecha(
        args.get("fecha_inicio"),
        "fecha_inicio"
    )

    fecha_fin = _parsear_fecha(
        args.get("fecha_fin"),
        "fecha_fin"
    )

    if (
        fecha_inicio
        and fecha_fin
        and fecha_fin < fecha_inicio
    ):

        raise VentasFiltroError(
            "La fecha final no puede ser anterior a la fecha inicial."
        )

    sort_by = str(
        args.get("sort_by") or "id"
    ).strip().lower()

    sort_order = str(
        args.get("sort_order") or "desc"
    ).strip().lower()

    if sort_by not in COLUMNAS_ORDEN_VENTAS:

        sort_by = "id"

    if sort_order not in ("asc", "desc"):

        sort_order = "desc"

    return {

        "page": page,

        "page_size": page_size,

        "sort_by": sort_by,

        "sort_order": sort_order,

        "buscar": str(
            args.get("buscar")
            or args.get("search")
            or ""
        ).strip()[:100],

        "metodo_pago": str(
            args.get("metodo_pago")
            or ""
        ).strip()[:50],

        "fecha_inicio": fecha_inicio,

        "fecha_fin": fecha_fin

    }


# =====================================================
# CONSTRUIR FILTROS SQL
#
# Los mismos filtros se utilizan en:
# - Listado.
# - Indicadores.
# - Exportacion.
#
# Esto garantiza consistencia entre resultados.
# =====================================================

def _construir_where_ventas(parametros, placeholder):

    condiciones = []

    valores = []

    # =============================================
    # BUSQUEDA
    # Cliente, ID venta, usuario y medio de pago
    # =============================================

    buscar = parametros["buscar"]

    if buscar:

        condiciones.append(
            f"""
            (
                LOWER(COALESCE(v.cliente, ''))
                LIKE {placeholder}

                OR

                LOWER(CAST(v.id AS VARCHAR(30)))
                LIKE {placeholder}

                OR

                LOWER(COALESCE(u.nombre, ''))
                LIKE {placeholder}

                OR

                LOWER(COALESCE(v.metodo_pago, ''))
                LIKE {placeholder}
            )
            """
        )

        texto = f"%{buscar.lower()}%"

        valores.extend([
            texto,
            texto,
            texto,
            texto
        ])

    # =============================================
    # METODO DE PAGO
    # =============================================

    metodo_pago = parametros["metodo_pago"]

    if metodo_pago:

        condiciones.append(
            f"""
            LOWER(COALESCE(v.metodo_pago, ''))
            = LOWER({placeholder})
            """
        )

        valores.append(
            metodo_pago
        )

    # =============================================
    # FECHA INICIAL
    # =============================================

    if parametros["fecha_inicio"]:

        condiciones.append(
            f"CAST(v.fecha AS DATE) >= {placeholder}"
        )

        valores.append(
            parametros["fecha_inicio"]
        )

    # =============================================
    # FECHA FINAL
    # =============================================

    if parametros["fecha_fin"]:

        condiciones.append(
            f"CAST(v.fecha AS DATE) <= {placeholder}"
        )

        valores.append(
            parametros["fecha_fin"]
        )

    where_sql = ""

    if condiciones:

        where_sql = (
            " WHERE " + " AND ".join(condiciones)
        )

    return where_sql, valores


# =====================================================
# ORDER BY SEGURO
# =====================================================

def _obtener_order_by(parametros):

    columna = COLUMNAS_ORDEN_VENTAS.get(
        parametros["sort_by"],
        "v.id"
    )

    direccion = (
        "ASC"
        if parametros["sort_order"] == "asc"
        else "DESC"
    )

    return f"{columna} {direccion}"


# =====================================================
# PAGINACION
# =====================================================

def _obtener_paginacion(parametros):

    page = parametros["page"]

    page_size = parametros["page_size"]

    offset = (page - 1) * page_size

    return {

        "page": page,

        "page_size": page_size,

        "offset": offset

    }


# =====================================================
# NORMALIZAR NUMEROS
# =====================================================

def _numero(valor):

    if valor is None:
        return 0.0

    if isinstance(valor, Decimal):
        return float(valor)

    return float(valor or 0)


# =====================================================
# NORMALIZAR FECHAS
# =====================================================

def _fecha_texto(valor):

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
# CONVERTIR FILA SQL EN DICCIONARIO
# =====================================================

def _filas_diccionario(cursor):

    columnas = [
        columna[0]
        for columna in cursor.description
    ]

    return [

        dict(zip(columnas, fila))

        for fila in cursor.fetchall()

    ]


# =====================================================
# CONSULTAR KPIS
#
# Utiliza exactamente el mismo WHERE
# del historial de ventas.
# =====================================================

def _consultar_kpis_ventas(
    cursor,
    where_sql,
    valores
):

    cursor.execute(
        f"""
        SELECT

            COUNT(*) AS total_ventas,

            COALESCE(
                SUM(v.total),
                0
            ) AS total_vendido,

            COUNT(
                DISTINCT v.cliente_id
            ) AS clientes_identificados,

            COALESCE(
                AVG(v.total),
                0
            ) AS ticket_promedio

        FROM {VENTAS} v

        LEFT JOIN {USUARIOS} u
            ON u.id = v.usuario_id

        {where_sql}
        """,
        valores
    )

    fila = cursor.fetchone()

    if not fila:

        return {

            "total_ventas": 0,

            "total_vendido": 0.0,

            "clientes_identificados": 0,

            "ticket_promedio": 0.0

        }

    return {

        "total_ventas": int(
            fila[0] or 0
        ),

        "total_vendido": _numero(
            fila[1]
        ),

        "clientes_identificados": int(
            fila[2] or 0
        ),

        "ticket_promedio": _numero(
            fila[3]
        )

    }


# =====================================================
# LISTAR VENTAS
#
# Incluye:
# - Filtros.
# - Paginacion.
# - Ordenamiento.
#
# Retorna la misma estructura utilizada
# por el historico de pedidos.
# =====================================================

def listar_ventas(args=None):

    parametros = _obtener_parametros_ventas(
        args
    )

    paginacion = _obtener_paginacion(
        parametros
    )

    order_by = _obtener_order_by(
        parametros
    )

    is_postgres, placeholder = _configuracion_bd()

    conn = None

    try:

        conn = get_connection()

        cursor = conn.cursor()

        where_sql, valores = _construir_where_ventas(
            parametros,
            placeholder
        )

        # =========================================
        # TOTAL DE REGISTROS
        # =========================================

        cursor.execute(
            f"""
            SELECT COUNT(*)

            FROM {VENTAS} v

            LEFT JOIN {USUARIOS} u
                ON u.id = v.usuario_id

            {where_sql}
            """,
            valores
        )

        total = int(
            cursor.fetchone()[0] or 0
        )

        # =========================================
        # CONSULTA PAGINADA
        # =========================================
        
        columnas = """
            v.id,
            v.cliente,
            v.cliente_id,
            v.fecha,
            v.total,
            v.metodo_pago,
            v.mesa,
            v.categoria,
            v.usuario_id,
            u.nombre AS usuario,
            v.tipo_servicio,
            v.direccion_entrega
        """


        if is_postgres:

            sql = f"""
                SELECT
                    {columnas}

                FROM {VENTAS} v

                LEFT JOIN {USUARIOS} u
                    ON u.id = v.usuario_id

                {where_sql}

                ORDER BY {order_by}

                LIMIT %s

                OFFSET %s
            """

            cursor.execute(
                sql,
                valores + [
                    paginacion["page_size"],
                    paginacion["offset"]
                ]
            )

        else:

            sql = f"""
                SELECT
                    {columnas}

                FROM {VENTAS} v

                LEFT JOIN {USUARIOS} u
                    ON u.id = v.usuario_id

                {where_sql}

                ORDER BY {order_by}

                OFFSET ? ROWS

                FETCH NEXT ? ROWS ONLY
            """

            cursor.execute(
                sql,
                valores + [
                    paginacion["offset"],
                    paginacion["page_size"]
                ]
            )

        # =========================================
        # NORMALIZAR RESULTADOS
        # =========================================

        items = _filas_diccionario(cursor)

        for venta in items:

            venta["id"] = int(
                venta.get("id") or 0
            )

            venta["total"] = _numero(
                venta.get("total")
            )

            venta["fecha"] = _fecha_texto(
                venta.get("fecha")
            )

            venta["cliente"] = (
                venta.get("cliente")
                or "Consumidor final"
            )

            venta["metodo_pago"] = (
                venta.get("metodo_pago")
                or "No especificado"
            )

            venta["mesa"] = (
                venta.get("mesa")
                or ""
            )

            venta["categoria"] = (
                venta.get("categoria")
                or ""
            )

            venta["usuario"] = (
                venta.get("usuario")
                or "Usuario no disponible"
            )

            venta["tipo_servicio"] = (
                str(venta.get("tipo_servicio") or "").strip().upper()
            )

            venta["direccion_entrega"] = (
                str(venta.get("direccion_entrega") or "").strip()
            )

        total_paginas = (
            math.ceil(
                total / paginacion["page_size"]
            )
            if total
            else 1
        )

        return {

            "items": items,

            "pagination": {

                "page": paginacion["page"],

                "page_size": paginacion["page_size"],

                "total": total,

                "total_pages": total_paginas

            }

        }

    finally:

        if conn:
            conn.close()


# =====================================================
# OBTENER KPIS DE VENTAS
#
# Funcion publica para el endpoint.
# =====================================================

def obtener_kpis_ventas(filtros=None):

    parametros = _obtener_parametros_ventas(
        filtros
    )

    is_postgres, placeholder = _configuracion_bd()

    conn = None

    try:

        conn = get_connection()

        cursor = conn.cursor()

        where_sql, valores = _construir_where_ventas(
            parametros,
            placeholder
        )

        return _consultar_kpis_ventas(
            cursor,
            where_sql,
            valores
        )

    finally:

        if conn:
            conn.close()


# =====================================================
# PROTEGER TEXTOS PARA EXCEL
#
# Evita que los datos ingresados por usuarios
# se ejecuten como formulas al abrir Excel.
# =====================================================

def _texto_seguro_excel(valor):

    if valor is None:
        return ""

    texto = str(valor)

    if texto.lstrip().startswith(
        ("=", "+", "-", "@")
    ):

        return "'" + texto

    return texto


# =====================================================
# EXPORTAR VENTAS
#
# No utiliza paginacion.
#
# Devuelve:
# - kpis
# - ventas: encabezados de las ventas
# - detalle: productos de todas las ventas
# =====================================================

def exportar_ventas(filtros=None):

    parametros = _obtener_parametros_ventas(
        filtros
    )

    is_postgres, placeholder = _configuracion_bd()

    conn = None

    try:

        conn = get_connection()

        cursor = conn.cursor()

        where_sql, valores = _construir_where_ventas(
            parametros,
            placeholder
        )

        # =========================================
        # INDICADORES GENERALES
        # =========================================

        kpis = _consultar_kpis_ventas(
            cursor,
            where_sql,
            valores
        )

        # =========================================
        # HOJA 1: ENCABEZADOS DE VENTAS
        # =========================================

        cursor.execute(
            f"""
            SELECT

                v.id,

                v.fecha,

                v.cliente,

                v.mesa,

                v.metodo_pago,

                v.categoria,

                u.nombre AS usuario,

                v.total,

                v.tipo_servicio,

                v.direccion_entrega

            FROM {VENTAS} v

            LEFT JOIN {USUARIOS} u
                ON u.id = v.usuario_id

            {where_sql}

            ORDER BY
                v.fecha DESC,
                v.id DESC
            """,
            valores
        )

        ventas = _filas_diccionario(cursor)

        for venta in ventas:

            venta["id"] = int(
                venta.get("id") or 0
            )

            venta["fecha"] = _fecha_texto(
                venta.get("fecha")
            )

            venta["cliente"] = _texto_seguro_excel(
                venta.get("cliente") or "Consumidor final"
            )

            venta["mesa"] = _texto_seguro_excel(
                venta.get("mesa") or ""
            )

            venta["metodo_pago"] = _texto_seguro_excel(
                venta.get("metodo_pago") or "No especificado"
            )

            venta["categoria"] = _texto_seguro_excel(
                venta.get("categoria") or ""
            )

            venta["usuario"] = _texto_seguro_excel(
                venta.get("usuario") or "Usuario no disponible"
            )

            venta["total"] = _numero(
                venta.get("total")
            )

        # =========================================
        # HOJA 2: DETALLE DE VENTAS
        # =========================================

        cursor.execute(
            f"""
            SELECT

                v.id AS venta_id,

                v.fecha,

                v.cliente,

                v.metodo_pago,

                u.nombre AS usuario,

                dv.id AS detalle_id,

                COALESCE(
                    NULLIF(dv.nombre_item, ''),
                    NULLIF(dv.tipo_item, ''),
                    'Sin nombre'
                ) AS producto,

                dv.tipo_item,

                dv.cantidad,

                dv.precio

            FROM {DETALLE_VENTAS} dv

            INNER JOIN {VENTAS} v
                ON v.id = dv.venta_id

            LEFT JOIN {USUARIOS} u
                ON u.id = v.usuario_id

            {where_sql}

            ORDER BY
                v.fecha DESC,
                v.id DESC,
                dv.id ASC
            """,
            valores
        )

        detalle = _filas_diccionario(cursor)

        for item in detalle:

            item["venta_id"] = int(
                item.get("venta_id") or 0
            )

            item["detalle_id"] = int(
                item.get("detalle_id") or 0
            )

            item["fecha"] = _fecha_texto(
                item.get("fecha")
            )

            item["cliente"] = _texto_seguro_excel(
                item.get("cliente") or "Consumidor final"
            )

            item["metodo_pago"] = _texto_seguro_excel(
                item.get("metodo_pago") or "No especificado"
            )

            item["usuario"] = _texto_seguro_excel(
                item.get("usuario") or "Usuario no disponible"
            )

            item["producto"] = _texto_seguro_excel(
                item.get("producto") or "Sin nombre"
            )

            item["tipo_item"] = _texto_seguro_excel(
                item.get("tipo_item") or ""
            )

            item["cantidad"] = _numero(
                item.get("cantidad")
            )

            item["precio"] = _numero(
                item.get("precio")
            )

            item["subtotal"] = (
                item["cantidad"] * item["precio"]
            )

        return {

            "kpis": kpis,

            "ventas": ventas,

            "detalle": detalle

        }

    finally:

        if conn:
            conn.close()
