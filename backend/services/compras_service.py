from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from config import Config


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

        if not usuario_id:
            raise Exception("Usuario no autenticado")

        # 🔥 MOTOR DINÁMICO
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"
        null_fn = "COALESCE" if is_postgres else "ISNULL"

        total = Decimal("0")

        # =========================
        # INSERT COMPRA
        # =========================
        if is_postgres:
            cursor.execute(f"""
                INSERT INTO restobar.compras (proveedor, total, usuario_id)
                VALUES ({placeholder}, 0, {placeholder})
                RETURNING id
            """, (proveedor, usuario_id))
        else:
            cursor.execute(f"""
                INSERT INTO restobar.compras (proveedor, total, usuario_id)
                OUTPUT INSERTED.id
                VALUES ({placeholder}, 0, {placeholder})
            """, (proveedor, usuario_id))

        compra_id = cursor.fetchone()[0]

        # =========================
        # DETALLE + STOCK + COSTO
        # =========================
        for item in detalles:

            producto_id = item.get("producto_id")

            if not producto_id:
                raise Exception("Producto inválido")

            cantidad = to_decimal(item.get("cantidad"), "Cantidad")
            precio = to_decimal(item.get("precio"), "Precio")

            if cantidad <= 0 or precio <= 0:
                raise Exception("Cantidad o precio inválido")

            subtotal = cantidad * precio
            total += subtotal

            # =========================
            # INSERT DETALLE
            # =========================
            cursor.execute(f"""
                INSERT INTO restobar.detalle_compras (compra_id, producto_id, cantidad, precio)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (compra_id, producto_id, cantidad, precio))

            # =========================
            # 🔥 OBTENER STOCK Y COSTO ACTUAL
            # =========================
            cursor.execute(f"""
                SELECT stock, costo
                FROM restobar.productos
                WHERE id = {placeholder}
            """, (producto_id,))

            row = cursor.fetchone()

            if not row:
                raise Exception(f"Producto no existe: {producto_id}")

            stock_actual = Decimal(row[0] or 0)
            costo_actual = Decimal(row[1] or 0)

            # =========================
            # 🔥 COSTO PROMEDIO
            # =========================
            if (stock_actual + cantidad) > 0:
                nuevo_costo = (
                    (stock_actual * costo_actual) +
                    (cantidad * precio)
                ) / (stock_actual + cantidad)
            else:
                nuevo_costo = precio

            # 🔥 redondeo controlado (evita decimales infinitos en DB)
            nuevo_costo = nuevo_costo.quantize(Decimal("0.0001"))

            # =========================
            # 🔥 ACTUALIZAR PRODUCTO
            # =========================
            cursor.execute(f"""
                UPDATE restobar.productos
                SET 
                    stock = {null_fn}(stock, 0) + {placeholder},
                    costo = {placeholder}
                WHERE id = {placeholder}
            """, (cantidad, nuevo_costo, producto_id))

        # =========================
        # ACTUALIZAR TOTAL COMPRA
        # =========================
        cursor.execute(f"""
            UPDATE restobar.compras
            SET total = {placeholder}
            WHERE id = {placeholder}
        """, (total, compra_id))

        conn.commit()

        return {
            "message": "Compra registrada correctamente",
            "total": float(round(total, 2))
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

    try:
        cursor.execute("""
            SELECT id, proveedor, total, fecha
            FROM restobar.compras
            ORDER BY id DESC
        """)

        columns = [c[0] for c in cursor.description]

        data = []
        for r in cursor.fetchall():
            row = dict(zip(columns, r))

            # 🔥 normalización frontend
            row["total"] = float(row.get("total") or 0)

            data.append(row)

        return data

    except Exception as e:
        print("❌ ERROR GET COMPRAS:", e)
        return []

    finally:
        conn.close()


# =============================
# 📄 DETALLE COMPRA
# =============================
def get_detalle_compra(compra_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        cursor.execute(f"""
            SELECT dc.producto_id, p.nombre, dc.cantidad, dc.precio
            FROM restobar.detalle_compras dc
            JOIN restobar.productos p ON dc.producto_id = p.id
            WHERE dc.compra_id = {placeholder}
        """, (compra_id,))

        columns = [c[0] for c in cursor.description]

        data = []
        for r in cursor.fetchall():
            row = dict(zip(columns, r))

            # 🔥 normalización
            row["cantidad"] = float(row.get("cantidad") or 0)
            row["precio"] = float(row.get("precio") or 0)

            data.append(row)

        return data

    except Exception as e:
        print("❌ ERROR DETALLE COMPRA:", e)
        return []

    finally:
        conn.close()