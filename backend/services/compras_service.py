from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from config import Config
from database.db_objects import COMPRAS, DETALLE_COMPRAS, PRODUCTOS, USUARIOS


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
# 💰 CALCULAR COSTO PROMEDIO
# =============================
def calcular_costo_promedio_compra(
    stock_actual,
    costo_actual,
    cantidad_compra,
    precio_compra
):
    """
    Calcula el nuevo costo promedio ponderado del producto.

    Este método es utilizado únicamente por el módulo Compras,
    ya que las compras representan la entrada oficial de inventario.

    Fórmula:
        ((Stock Actual × Costo Actual) +
         (Cantidad Comprada × Precio Compra))
        /
        (Stock Actual + Cantidad Comprada)
    """

    if (stock_actual + cantidad_compra) <= 0:
        return precio_compra.quantize(Decimal("0.0001"))

    nuevo_costo = (
        (stock_actual * costo_actual) +
        (cantidad_compra * precio_compra)
    ) / (stock_actual + cantidad_compra)

    return nuevo_costo.quantize(Decimal("0.0001"))


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
                INSERT INTO {COMPRAS} (proveedor, total, usuario_id, fecha)
                VALUES ({placeholder}, 0, {placeholder}, CURRENT_TIMESTAMP)
                RETURNING id
            """, (proveedor, usuario_id))
        else:
            cursor.execute(f"""
                INSERT INTO {COMPRAS} (proveedor, total, usuario_id, fecha)
                OUTPUT INSERTED.id
                VALUES ({placeholder}, 0, {placeholder}, GETDATE())
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
                INSERT INTO {DETALLE_COMPRAS} (compra_id, producto_id, cantidad, precio)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (compra_id, producto_id, cantidad, precio))

            # =========================
            # 🔥 OBTENER STOCK Y COSTO ACTUAL
            # =========================
            cursor.execute(f"""
                SELECT stock, costo
                FROM {PRODUCTOS}
                WHERE id = {placeholder}
            """, (producto_id,))

            row = cursor.fetchone()

            if not row:
                raise Exception(f"Producto no existe: {producto_id}")

            stock_actual = Decimal(row[0] or 0)
            costo_actual = Decimal(row[1] or 0)

            # =========================
            # 💰 CALCULAR COSTO PROMEDIO
            # =========================
            nuevo_costo = calcular_costo_promedio_compra(
                stock_actual=stock_actual,
                costo_actual=costo_actual,
                cantidad_compra=cantidad,
                precio_compra=precio
            )

            # =========================
            # 🔥 ACTUALIZAR PRODUCTO
            # =========================
            cursor.execute(f"""
                UPDATE {PRODUCTOS}
                SET 
                    stock = {null_fn}(stock, 0) + {placeholder},
                    costo = {placeholder}
                WHERE id = {placeholder}
            """, (cantidad, nuevo_costo, producto_id))

        # =========================
        # ACTUALIZAR TOTAL COMPRA
        # =========================
        cursor.execute(f"""
            UPDATE {COMPRAS}
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
        cursor.execute(f"""
            SELECT co.id, co.proveedor, co.total, co.fecha, u.nombre AS usuario
            FROM {COMPRAS} co
            INNER JOIN {USUARIOS} u ON co.usuario_id = u.id
            ORDER BY co.id DESC
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
            FROM {DETALLE_COMPRAS} dc
            INNER JOIN {PRODUCTOS} p ON dc.producto_id = p.id
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