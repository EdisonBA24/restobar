from config import Config
from database.connection import get_connection
from database.db_objects import PRODUCTOS, VENTAS, UNIDADES_MEDIDA

def _get_placeholder():
    return "?" if Config.DB_ENGINE == "sqlserver" else "%s"


# ======================================================
# REPORTE INVENTARIO
# ======================================================

def reporte_inventario():
    """
    Obtiene el stock actual de todos los productos.

    Temporalmente consulta la tabla PRODUCTOS.
    En una siguiente fase consumirá inventario_service.py.
    """

    conn = get_connection()

    try:
        cursor = conn.cursor()

        cursor.execute(f"""
            SELECT
                p.nombre,
                p.stock,
                um.nombre AS unidad
            FROM {PRODUCTOS} p
            JOIN {UNIDADES_MEDIDA} um
                ON p.unidad_id = um.id
            ORDER BY p.nombre
        """)

        rows = cursor.fetchall()

        return [
            {
                "Producto": row[0],
                "Stock": float(row[1] or 0),
                "Unidad": row[2]
            }
            for row in rows
        ]

    finally:
        conn.close()


# ======================================================
# REPORTE VENTAS
# ======================================================

def reporte_ventas(inicio=None, fin=None):
    """
    Obtiene el listado de ventas.

    Puede filtrarse por rango de fechas.
    """

    conn = get_connection()

    try:

        cursor = conn.cursor()

        placeholder = _get_placeholder()

        query = f"""
            SELECT
                v.fecha,
                v.categoria,
                v.total
            FROM {VENTAS} v
        """

        params = None

        if inicio and fin:
            query += f"""
                WHERE CAST(v.fecha AS DATE)
                BETWEEN {placeholder} AND {placeholder}
            """
            params = [inicio, fin]

        query += """
            ORDER BY v.fecha DESC
        """

        if params:
            cursor.execute(query, params)
        else:
            cursor.execute(query)

        rows = cursor.fetchall()

        return [
            {
                "Fecha": row[0].strftime("%Y-%m-%d") if row[0] else "",
                "Categoria": row[1] or "",
                "Total": float(row[2] or 0)
            }
            for row in rows
        ]

    finally:
        conn.close()


# ======================================================
# REPORTE COSTOS
# ======================================================

def reporte_costos():
    """
    Endpoint temporal.

    El cálculo de costos será implementado posteriormente
    desde inventario_service.py.
    """

    return []