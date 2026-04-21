from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation


# =============================
# 🔧 VALIDAR DECIMAL
# =============================
def to_decimal(value, field):
    try:
        if value is None or str(value).strip() == "":
            raise Exception(f"{field} vacío")

        return Decimal(str(value))

    except (InvalidOperation, Exception):
        raise Exception(f"{field} inválido: {value}")


# =============================
# 🛒 CREAR COMPRA
# =============================
def crear_compra(data):
    conn = get_connection()
    cursor = conn.cursor()
    usuario_id = session.get("user_id")

    try:
        proveedor = data.get("proveedor")

        if not proveedor:
            raise Exception("Proveedor requerido")

        detalles = data.get("detalles", [])

        if not detalles:
            raise Exception("No hay productos en la compra")

        total = Decimal("0")

        # =========================
        # INSERT COMPRA
        # =========================
        cursor.execute("""
            INSERT INTO compras (proveedor, total, usuario_id)
            OUTPUT INSERTED.id
            VALUES (?, 0, ?)
        """, (proveedor, usuario_id))

        compra_id = cursor.fetchone()[0]

        # =========================
        # DETALLE + STOCK + COSTO
        # =========================
        for item in detalles:

            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")
            precio = to_decimal(item["precio"], "Precio")

            subtotal = cantidad * precio
            total += subtotal

            # =========================
            # INSERT DETALLE
            # =========================
            cursor.execute("""
                INSERT INTO detalle_compras (compra_id, producto_id, cantidad, precio)
                VALUES (?, ?, ?, ?)
            """, (compra_id, producto_id, cantidad, precio))

            # =========================
            # 🔥 OBTENER STOCK Y COSTO ACTUAL
            # =========================
            cursor.execute("""
                SELECT stock, costo
                FROM productos
                WHERE id = ?
            """, (producto_id,))

            row = cursor.fetchone()

            stock_actual = Decimal(row[0] or 0)
            costo_actual = Decimal(row[1] or 0)

            cantidad_compra = cantidad
            costo_compra = precio

            # =========================
            # 🔥 CALCULAR COSTO PROMEDIO
            # =========================
            if (stock_actual + cantidad_compra) > 0:
                nuevo_costo = (
                    (stock_actual * costo_actual) +
                    (cantidad_compra * costo_compra)
                ) / (stock_actual + cantidad_compra)
            else:
                nuevo_costo = costo_compra

            # =========================
            # 🔥 ACTUALIZAR PRODUCTO
            # =========================
            cursor.execute("""
                UPDATE productos
                SET 
                    stock = ISNULL(stock, 0) + ?,
                    costo = ?
                WHERE id = ?
            """, (cantidad_compra, nuevo_costo, producto_id))

        # =========================
        # ACTUALIZAR TOTAL COMPRA
        # =========================
        cursor.execute("""
            UPDATE compras
            SET total = ?
            WHERE id = ?
        """, (total, compra_id))

        conn.commit()

        return {
            "message": "Compra registrada correctamente",
            "total": float(total)
        }

    except Exception as e:
        conn.rollback()
        print("❌ ERROR COMPRA:", e)
        raise e

    finally:
        conn.close()


# =============================
# 📄 CONSULTAR COMPRAS
# =============================
def get_compras():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, proveedor, total, fecha
        FROM compras
        ORDER BY id DESC
    """)

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data


# =============================
# 📄 DETALLE COMPRA
# =============================
def get_detalle_compra(compra_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT dc.producto_id, p.nombre, dc.cantidad, dc.precio
        FROM detalle_compras dc
        JOIN productos p ON dc.producto_id = p.id
        WHERE dc.compra_id = ?
    """, (compra_id,))

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data