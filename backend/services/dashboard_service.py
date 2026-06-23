from database.connection import get_connection
from decimal import Decimal
from config import Config


def convertir_cantidad(cantidad, unidad):
    cantidad = Decimal(cantidad or 0)

    if not unidad:
        return cantidad

    unidad = str(unidad).lower()

    # 🔥 CORRECCIÓN: gramos → kg
    if unidad in ["g", "gr", "gramos"]:
        return cantidad / Decimal(1000)

    # kg queda igual
    if unidad in ["kg", "kilogramo", "kilogramos"]:
        return cantidad

    return cantidad


# =============================
# COSTO POR PRODUCTO
# =============================
def calcular_costo_producto(cursor, producto_id):

    is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
    placeholder = "%s" if is_postgres else "?"

    query_insumos = f"""
        SELECT rd.insumo_id, rd.cantidad, u.abreviatura
        FROM restobar.recetas r
        JOIN restobar.recetas_detalle rd ON r.id = rd.receta_id
        JOIN restobar.productos p ON rd.insumo_id = p.id
        LEFT JOIN restobar.unidades_medida u ON p.unidad_id = u.id
        WHERE r.producto_id = {placeholder}
    """

    cursor.execute(query_insumos, (producto_id,))
    insumos = cursor.fetchall()

    costo_total = Decimal("0")

    query_precio = f"""
        SELECT precio
        FROM restobar.detalle_compras
        WHERE producto_id = {placeholder}
        ORDER BY id DESC
    """

    # 🔥 LIMIT / TOP dinámico
    if is_postgres:
        query_precio += " LIMIT 1"
    else:
        query_precio = query_precio.replace("SELECT precio", "SELECT TOP 1 precio")

    for insumo_id, cantidad_base, unidad in insumos:

        cantidad_real = convertir_cantidad(cantidad_base, unidad)

        cursor.execute(query_precio, (insumo_id,))
        compra = cursor.fetchone()

        if not compra:
            continue

        precio = Decimal(compra[0] or 0)
        costo_total += cantidad_real * precio

    return costo_total


# =============================
# 🔥 UTILIDAD POR PRODUCTO REAL
# =============================
def get_utilidad_por_producto(cursor):

    is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"

    fecha_condition = "CURRENT_DATE" if is_postgres else "CAST(GETDATE() AS DATE)"

    query = f"""
        SELECT
            dv.producto_id,
            p.nombre,
            SUM(dv.cantidad) as cantidad,
            AVG(dv.precio) as precio
        FROM restobar.detalle_ventas dv
        JOIN restobar.productos p
            ON dv.producto_id = p.id
        JOIN restobar.ventas v
            ON dv.venta_id = v.id
        WHERE CAST(v.fecha AS DATE) = {fecha_condition}
        GROUP BY dv.producto_id, p.nombre
    """

    cursor.execute(query)

    data = cursor.fetchall()

    resultado = []

    for producto_id, nombre, cantidad, precio in data:

        cantidad = Decimal(cantidad or 0)
        precio = Decimal(precio or 0)

        costo = calcular_costo_producto(
            cursor,
            producto_id
        )

        utilidad = (precio - costo) * cantidad

        resultado.append({
            "producto": nombre,
            "cantidad": int(cantidad),
            "utilidad": float(round(utilidad, 2))
        })

    resultado.sort(
        key=lambda x: x["utilidad"],
        reverse=True
    )

    return resultado


# =============================
# DASHBOARD
# =============================
def get_dashboard():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        fecha_condition = "CURRENT_DATE" if is_postgres else "CAST(GETDATE() AS DATE)"

        query_ventas = f"""
            SELECT id, total
            FROM restobar.ventas
            WHERE CAST(fecha AS DATE) = {fecha_condition}
        """

        cursor.execute(query_ventas)
        ventas = cursor.fetchall()

        total_ventas = Decimal("0")
        utilidad_total = Decimal("0")

        productos = {}

        for venta_id, total in ventas:

            total_ventas += Decimal(total or 0)

            # 🔥 utilidad desde BD
            cursor.execute(f"""
                SELECT utilidad
                FROM restobar.ventas
                WHERE id = {placeholder}
            """, (venta_id,))

            utilidad_bd = cursor.fetchone()
            utilidad_total += Decimal(utilidad_bd[0] or 0) if utilidad_bd else Decimal("0")

            # 🔥 detalle
            cursor.execute(f"""
                SELECT producto_id, cantidad, precio
                FROM restobar.detalle_ventas
                WHERE venta_id = {placeholder}
            """, (venta_id,))

            detalles = cursor.fetchall()

            for producto_id, cantidad, precio in detalles:

                cantidad = Decimal(cantidad or 0)
                precio = Decimal(precio or 0)

                # 🔥 se mantiene lógica original
                costo = calcular_costo_producto(cursor, producto_id)

                utilidad = (precio - costo) * cantidad

                if producto_id not in productos:
                    productos[producto_id] = {
                        "cantidad": 0,
                        "utilidad": Decimal("0")
                    }

                productos[producto_id]["cantidad"] += int(cantidad)
                productos[producto_id]["utilidad"] += utilidad

        # 🔥 TOP PRODUCTOS
        top = get_utilidad_por_producto(cursor)

        return {
            "ventas_dia": float(total_ventas),
            "utilidad_dia": float(round(utilidad_total, 2)),
            "top_productos": top[:5]
        }

    except Exception as e:
        print("❌ ERROR DASHBOARD:", e)
        raise e

    finally:
        conn.close()