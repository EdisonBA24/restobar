from database.connection import get_connection
from decimal import Decimal


# =============================
# CONVERSIÓN UNIDADES
# =============================
def convertir_cantidad(cantidad, unidad):

    cantidad = Decimal(cantidad)

    if not unidad:
        return cantidad

    unidad = unidad.lower()

    # gramos → kg
    if unidad in ["g", "gr", "gramos"]:
        return cantidad / Decimal(1000)

    # kg se queda igual
    if unidad in ["kg", "kilogramo", "kilogramos"]:
        return cantidad

    # unidad (und)
    return cantidad


# =============================
# COSTO PRODUCTO
# =============================
def get_costo_producto(producto_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 🔥 AHORA USA UNIDAD DE RECETA
        cursor.execute("""
            SELECT rd.insumo_id, rd.cantidad, rd.unidad
            FROM recetas r
            JOIN recetas_detalle rd ON r.id = rd.receta_id
            WHERE r.producto_id = ?
        """, (producto_id,))

        insumos = cursor.fetchall()

        if not insumos:
            return {
                "costo": 0,
                "precio_venta": 0,
                "utilidad": 0,
                "margen": 0
            }

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

        # precio venta
        cursor.execute("""
            SELECT precio_venta
            FROM productos
            WHERE id = ?
        """, (producto_id,))

        result = cursor.fetchone()

        precio_venta = Decimal(result[0] or 0)

        utilidad = precio_venta - costo_total

        margen = Decimal("0")
        if precio_venta > 0:
            margen = (utilidad / precio_venta) * 100

        return {
            "costo": float(round(costo_total, 2)),
            "precio_venta": float(precio_venta),
            "utilidad": float(round(utilidad, 2)),
            "margen": float(round(margen, 2))
        }

    except Exception as e:
        print("❌ ERROR COSTOS:", e)
        raise e

    finally:
        conn.close()