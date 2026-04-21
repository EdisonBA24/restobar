from database.connection import get_connection
from decimal import Decimal


def convertir_cantidad(cantidad, unidad):
    cantidad = Decimal(cantidad)

    if unidad and unidad.lower() in ["kg", "kilogramo", "kilogramos"]:
        return cantidad / Decimal(1000)

    return cantidad


# =============================
# COSTO POR PRODUCTO
# =============================
def calcular_costo_producto(cursor, producto_id):

    cursor.execute("""
        SELECT rd.insumo_id, rd.cantidad, u.abreviatura
        FROM recetas r
        JOIN recetas_detalle rd ON r.id = rd.receta_id
        JOIN productos p ON rd.insumo_id = p.id
        LEFT JOIN unidades_medida u ON p.unidad_id = u.id
        WHERE r.producto_id = ?
    """, (producto_id,))

    insumos = cursor.fetchall()

    costo_total = Decimal("0")

    for insumo_id, cantidad_base, unidad in insumos:

        cantidad_real = convertir_cantidad(cantidad_base, unidad)

        cursor.execute("""
            SELECT TOP 1 precio
            FROM detalle_compras
            WHERE producto_id = ?
            ORDER BY id DESC
        """, (insumo_id,))

        compra = cursor.fetchone()
        if not compra:
            continue

        precio = Decimal(compra[0] or 0)

        costo_total += cantidad_real * precio

    return costo_total


# =============================
# 🔥 NUEVO: UTILIDAD POR PRODUCTO REAL (DESDE VENTAS)
# =============================
def get_utilidad_por_producto(cursor):

    cursor.execute("""
        SELECT 
            p.nombre,
            SUM(dv.cantidad) as cantidad,
            SUM((dv.precio * dv.cantidad)) as total
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        JOIN ventas v ON dv.venta_id = v.id
        WHERE CAST(v.fecha AS DATE) = CAST(GETDATE() AS DATE)
        GROUP BY p.nombre
    """)

    data = cursor.fetchall()

    resultado = []

    for nombre, cantidad, total in data:

        resultado.append({
            "producto": nombre,
            "cantidad": int(cantidad or 0),
            "utilidad": float(round(total or 0, 2))
        })

    resultado.sort(key=lambda x: x["utilidad"], reverse=True)

    return resultado


# =============================
# DASHBOARD
# =============================
def get_dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        # 🔥 ventas del día (SIN CAMBIOS)
        cursor.execute("""
            SELECT id, total
            FROM ventas
            WHERE CAST(fecha AS DATE) = CAST(GETDATE() AS DATE)
        """)

        ventas = cursor.fetchall()

        total_ventas = Decimal("0")
        utilidad_total = Decimal("0")

        productos = {}

        for venta_id, total in ventas:

            total_ventas += Decimal(total or 0)

            # 🔥 NUEVO: traer utilidad REAL de la venta
            cursor.execute("""
                SELECT utilidad
                FROM ventas
                WHERE id = ?
            """, (venta_id,))

            utilidad_bd = cursor.fetchone()
            utilidad_total += Decimal(utilidad_bd[0] or 0)

            # 🔥 mantenemos tu lógica original (NO se elimina)
            cursor.execute("""
                SELECT producto_id, cantidad, precio
                FROM detalle_ventas
                WHERE venta_id = ?
            """, (venta_id,))

            detalles = cursor.fetchall()

            for producto_id, cantidad, precio in detalles:

                cantidad = Decimal(cantidad)
                precio = Decimal(precio)

                # 🔥 se deja (pero ya NO afecta total final)
                costo = calcular_costo_producto(cursor, producto_id)

                utilidad = (precio - costo) * cantidad

                if producto_id not in productos:
                    productos[producto_id] = {
                        "cantidad": 0,
                        "utilidad": Decimal("0")
                    }

                productos[producto_id]["cantidad"] += int(cantidad)
                productos[producto_id]["utilidad"] += utilidad

        # 🔥 top productos (AHORA USAMOS MÉTODO REAL)
        top = get_utilidad_por_producto(cursor)

        return {
            "ventas_dia": float(total_ventas),
            "utilidad_dia": float(round(utilidad_total, 2)),
            "top_productos": top[:5]
        }

    finally:
        conn.close()