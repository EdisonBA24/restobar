from database.connection import get_connection
from decimal import Decimal
from config import Config


# =============================
# CONVERSIÓN UNIDADES
# =============================
def convertir_cantidad(cantidad, unidad):

    cantidad = Decimal(cantidad or 0)

    if not unidad:
        return cantidad

    unidad = str(unidad).lower().strip()

    # gramos → kg
    if unidad in ["g", "gr", "gramos"]:
        return cantidad / Decimal(1000)

    # kg se queda igual
    if unidad in ["kg", "kilogramo", "kilogramos"]:
        return cantidad

    # unidad (und u otras)
    return cantidad


# =============================
# COSTO PRODUCTO
# =============================
def get_costo_producto(producto_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 🔥 DETECTAR MOTOR UNA SOLA VEZ (mejor performance)
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        # =============================
        # 🔥 INSUMOS RECETA
        # =============================
        cursor.execute(f"""
            SELECT rd.insumo_id, rd.cantidad, rd.unidad
            FROM restobar.recetas r
            JOIN restobar.recetas_detalle rd ON r.id = rd.receta_id
            WHERE r.producto_id = {placeholder}
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

        # =============================
        # 🔥 QUERY DINÁMICO PRECIO
        # =============================
        query_precio = f"""
            SELECT precio
            FROM restobar.detalle_compras
            WHERE producto_id = {placeholder}
            ORDER BY id DESC
            {"LIMIT 1" if is_postgres else ""}
        """

        if not is_postgres:
            query_precio = f"""
                SELECT TOP 1 precio
                FROM restobar.detalle_compras
                WHERE producto_id = {placeholder}
                ORDER BY id DESC
            """

        for insumo_id, cantidad_base, unidad in insumos:

            cantidad_real = convertir_cantidad(cantidad_base, unidad)

            cursor.execute(query_precio, (insumo_id,))
            compra = cursor.fetchone()

            if not compra:
                continue

            precio = Decimal(compra[0] or 0)
            costo_total += cantidad_real * precio

        # =============================
        # 🔥 PRECIO VENTA
        # =============================
        cursor.execute(f"""
            SELECT precio_venta
            FROM restobar.productos
            WHERE id = {placeholder}
        """, (producto_id,))

        result = cursor.fetchone()

        precio_venta = Decimal(result[0] or 0) if result else Decimal("0")

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