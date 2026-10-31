
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from config import Config
from database.connection import get_connection
from database.db_objects import PAGOS, USUARIOS


# =====================================================
# EXCEPCIONES DEL MODULO
# =====================================================

class PagoValidationError(Exception):
    """Error de validacion de los datos de un pago."""


# =====================================================
# CONFIGURACION DE BASE DE DATOS
# =====================================================

def _get_db_settings():

    is_postgres = (
        getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
    )

    placeholder = "%s" if is_postgres else "?"

    return is_postgres, placeholder


# =====================================================
# VALIDAR MONTO
# =====================================================

def to_decimal(value, field="Monto"):

    if value is None or str(value).strip() == "":
        raise PagoValidationError(
            f"{field} es obligatorio."
        )

    try:

        valor = Decimal(str(value).strip())

    except (InvalidOperation, ValueError, TypeError):

        raise PagoValidationError(
            f"{field} no tiene un formato válido."
        )

    if not valor.is_finite():

        raise PagoValidationError(
            f"{field} no tiene un valor válido."
        )

    if valor <= 0:

        raise PagoValidationError(
            f"{field} debe ser mayor que cero."
        )

    return valor


# =====================================================
# VALIDAR EMPLEADO
# =====================================================

def _normalizar_usuario_id(value):

    try:

        usuario_id = int(value)

    except (TypeError, ValueError):

        raise PagoValidationError(
            "Debes seleccionar un empleado válido."
        )

    if usuario_id <= 0:

        raise PagoValidationError(
            "Debes seleccionar un empleado válido."
        )

    return usuario_id


# =====================================================
# VALIDAR FECHA
# =====================================================

def _parsear_fecha(value, campo="fecha"):

    if value is None or str(value).strip() == "":

        raise PagoValidationError(
            "La fecha del pago es obligatoria."
        )

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, date):
        return value

    texto = str(value).strip()

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
# SERIALIZAR FECHA
# =====================================================

def _serializar_fecha(value):

    if value is None:
        return None

    if isinstance(value, datetime):

        return value.isoformat(
            sep=" ",
            timespec="seconds"
        )

    if isinstance(value, date):
        return value.isoformat()

    return str(value)


# =====================================================
# EXPRESION DEL NOMBRE DEL EMPLEADO
#
# Primero utiliza el nombre guardado en PAGOS.
# Si está vacío, utiliza el nombre actual de USUARIOS.
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
# NORMALIZAR REGISTRO
# =====================================================

def _normalizar_pago(row):

    pago = dict(row)

    pago["id"] = int(
        pago.get("id") or 0
    )

    pago["usuario_id"] = (
        int(pago["usuario_id"])
        if pago.get("usuario_id") is not None
        else None
    )

    pago["monto"] = float(
        pago.get("monto") or 0
    )

    pago["fecha"] = _serializar_fecha(
        pago.get("fecha")
    )

    return pago


# =====================================================
# CREAR PAGO
# =====================================================

def crear_pago(data):

    if not isinstance(data, dict):

        raise PagoValidationError(
            "Los datos del pago no son válidos."
        )

    usuario_id = _normalizar_usuario_id(
        data.get("usuario_id")
    )

    monto = to_decimal(
        data.get("monto"),
        "Monto"
    )

    concepto = str(
        data.get("concepto") or ""
    ).strip()

    if not concepto:

        raise PagoValidationError(
            "El concepto del pago es obligatorio."
        )

    fecha_pago = _parsear_fecha(
        data.get("fecha")
    )

    conn = None

    try:

        conn = get_connection()
        cursor = conn.cursor()

        _, placeholder = _get_db_settings()

        # =============================================
        # VALIDAR EMPLEADO ACTIVO
        # =============================================

        cursor.execute(
            f"""
            SELECT nombre
            FROM {USUARIOS}
            WHERE id = {placeholder}
              AND activo = 1
            """,
            (usuario_id,)
        )

        empleado_row = cursor.fetchone()

        if not empleado_row:

            raise PagoValidationError(
                "El empleado seleccionado no existe o está inactivo."
            )

        empleado = str(
            empleado_row[0] or ""
        ).strip()

        if not empleado:

            raise PagoValidationError(
                "El empleado seleccionado no tiene un nombre válido."
            )

        # =============================================
        # INSERTAR PAGO
        # =============================================

        cursor.execute(
            f"""
            INSERT INTO {PAGOS}
            (
                empleado,
                monto,
                concepto,
                fecha,
                usuario_id
            )
            VALUES
            (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
            """,
            (
                empleado,
                monto,
                concepto,
                fecha_pago,
                usuario_id
            )
        )

        conn.commit()

        return "Pago registrado correctamente."

    except Exception:

        if conn:
            conn.rollback()

        raise

    finally:

        if conn:
            conn.close()


# =====================================================
# CONSULTA COMPLETA LEGACY
#
# COMPATIBILIDAD TEMPORAL CON EL FRONTEND ACTUAL
# GET /pagos SIN PARAMETROS
# =====================================================

def get_pagos_legacy():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        empleado_expr = _expresion_empleado()

        cursor.execute(
            f"""
            SELECT
                p.id,
                {empleado_expr} AS empleado,
                p.monto,
                p.concepto,
                p.fecha,
                p.usuario_id
            FROM {PAGOS} p
            LEFT JOIN {USUARIOS} u
                ON p.usuario_id = u.id
            ORDER BY p.id DESC
            """
        )

        columnas = [
            columna[0]
            for columna in cursor.description
        ]

        return [
            _normalizar_pago(
                dict(zip(columnas, row))
            )
            for row in cursor.fetchall()
        ]

    finally:

        conn.close()


# =====================================================
# LISTADO PAGINADO DE PAGOS
# =====================================================

def get_pagos(
    page=1,
    limit=10,
    search=None,
    fecha_inicio=None,
    fecha_fin=None,
    sort_by="id",
    sort_order="desc"
):

    # =============================================
    # VALIDAR PAGINACION
    # =============================================

    try:

        page = int(page)
        limit = int(limit)

    except (TypeError, ValueError):

        raise PagoValidationError(
            "Los parámetros de paginación no son válidos."
        )

    if page < 1:

        raise PagoValidationError(
            "La página debe ser mayor o igual a 1."
        )

    if limit < 1:

        raise PagoValidationError(
            "La cantidad de registros debe ser mayor que cero."
        )

    limit = min(limit, 100)

    # =============================================
    # VALIDAR FECHAS
    # =============================================

    fecha_desde = (
        _parsear_fecha(
            fecha_inicio,
            "fecha_inicio"
        )
        if fecha_inicio
        else None
    )

    fecha_hasta = (
        _parsear_fecha(
            fecha_fin,
            "fecha_fin"
        )
        if fecha_fin
        else None
    )

    if (
        fecha_desde
        and fecha_hasta
        and fecha_hasta < fecha_desde
    ):

        raise PagoValidationError(
            "La fecha final no puede ser anterior a la fecha inicial."
        )

    # =============================================
    # BUSQUEDA
    # =============================================

    busqueda = str(
        search or ""
    ).strip()[:100].lower()

    # =============================================
    # COLUMNAS PERMITIDAS PARA ORDENAR
    # =============================================

    empleado_expr = _expresion_empleado()

    columnas_validas = {

        "id": "p.id",

        "empleado": empleado_expr,

        "monto": "p.monto",

        "concepto": "p.concepto",

        "fecha": "p.fecha"

    }

    sort_by = str(
        sort_by or "id"
    ).strip().lower()

    if sort_by not in columnas_validas:
        sort_by = "id"

    columna_orden = columnas_validas[sort_by]

    sort_order = (
        "ASC"
        if str(sort_order or "").strip().lower() == "asc"
        else "DESC"
    )

    is_postgres, placeholder = _get_db_settings()

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # =============================================
        # CONSTRUIR FILTROS
        # =============================================

        condiciones = []
        params = []

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

            params.extend([
                like,
                like
            ])

        if fecha_desde:

            condiciones.append(
                f"p.fecha >= {placeholder}"
            )

            params.append(fecha_desde)

        if fecha_hasta:

            condiciones.append(
                f"p.fecha < {placeholder}"
            )

            # Se utiliza el día siguiente como límite exclusivo
            # para incluir todas las horas de la fecha final.

            params.append(
                fecha_hasta + timedelta(days=1)
            )

        where_sql = (
            "WHERE " + " AND ".join(condiciones)
            if condiciones
            else ""
        )

        # =============================================
        # TOTAL DE REGISTROS
        # =============================================

        count_query = f"""
            SELECT COUNT(*)
            FROM {PAGOS} p
            LEFT JOIN {USUARIOS} u
                ON p.usuario_id = u.id
            {where_sql}
        """

        cursor.execute(
            count_query,
            tuple(params)
        )

        total = int(
            cursor.fetchone()[0] or 0
        )

        total_pages = max(
            (total + limit - 1) // limit,
            1
        )

        if page > total_pages:
            page = total_pages

        offset = (page - 1) * limit

                # =============================================
        # CONSTRUIR ORDENAMIENTO
        # =============================================

        if sort_by == "id":

            # El ID es único, no necesita segundo criterio.

            order_by_sql = (
                f"p.id {sort_order}"
            )

        else:

            # Para otras columnas utilizamos el ID
            # como segundo criterio de ordenamiento.

            order_by_sql = (
                f"{columna_orden} {sort_order}, p.id DESC"
            )

        # =============================================
        # CONSULTA PRINCIPAL
        # =============================================

        query = f"""
            SELECT
                p.id,
                {empleado_expr} AS empleado,
                p.monto,
                p.concepto,
                p.fecha,
                p.usuario_id
            FROM {PAGOS} p
            LEFT JOIN {USUARIOS} u
                ON p.usuario_id = u.id
            {where_sql}
            ORDER BY {order_by_sql}
        """

        query_params = list(params)

        if is_postgres:

            query += f"""
                LIMIT {placeholder}
                OFFSET {placeholder}
            """

            query_params.extend([
                limit,
                offset
            ])

        else:

            query += f"""
                OFFSET {placeholder}
                ROWS FETCH NEXT {placeholder} ROWS ONLY
            """

            query_params.extend([
                offset,
                limit
            ])

        cursor.execute(
            query,
            tuple(query_params)
        )

        columnas = [
            columna[0]
            for columna in cursor.description
        ]

        items = [
            _normalizar_pago(
                dict(zip(columnas, row))
            )
            for row in cursor.fetchall()
        ]

        return {

            "items": items,

            "page": page,

            "page_size": limit,

            "total": total,

            "total_pages": total_pages,

            "sort_by": sort_by,

            "sort_order": sort_order.lower()

        }

    finally:

        conn.close()
