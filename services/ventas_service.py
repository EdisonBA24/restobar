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
# 🔁 CONVERSIÓN UNIDADES
# =============================
def convertir_cantidad(cantidad, unidad):

    cantidad = Decimal(cantidad)

    if not unidad:
        return cantidad

    unidad = unidad.lower()

    if unidad in ["g", "gr", "gramos"]:
        return cantidad / Decimal(1000)

    if unidad in ["kg", "kilogramo", "kilogramos"]:
        return cantidad

    return cantidad


# =============================
# 🧠 CALCULAR COSTO
# =============================
def calcular_costo_producto(cursor, producto_id, cantidad):

    cursor.execute("SELECT tipo, costo FROM productos WHERE id = ?", (producto_id,))
    result = cursor.fetchone()

    tipo = result[0]
    costo_directo = Decimal(result[1] or 0)

    # 🥃 LICOR / BEBIDA
    if tipo in ["LICORES", "BEBIDAS"]:
        return costo_directo * cantidad

    # 🍔 RECETA
    cursor.execute("""
        SELECT rd.insumo_id, rd.cantidad, rd.unidad
        FROM recetas r
        JOIN recetas_detalle rd ON r.id = rd.receta_id
        WHERE r.producto_id = ?
    """, (producto_id,))

    insumos = cursor.fetchall()

    if not insumos:
        return Decimal("0")

    costo_total = Decimal("0")

    for insumo_id, cantidad_base, unidad in insumos:

        cantidad_total = Decimal(cantidad_base) * cantidad
        cantidad_real = convertir_cantidad(cantidad_total, unidad)

        cursor.execute("SELECT costo FROM productos WHERE id = ?", (insumo_id,))
        result = cursor.fetchone()

        costo_unitario = Decimal(result[0] or 0)
        costo_total += costo_unitario * cantidad_real

    return costo_total


# =============================
# 📦 VALIDAR STOCK
# =============================
def validar_stock(data):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        for item in data["detalles"]:

            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")

            cursor.execute("SELECT tipo FROM productos WHERE id = ?", (producto_id,))
            tipo = cursor.fetchone()[0]

            # 🥃 LICOR / BEBIDA
            if tipo in ["LICORES", "BEBIDAS"]:

                cursor.execute("SELECT stock, nombre FROM productos WHERE id=?", (producto_id,))
                result = cursor.fetchone()

                stock = Decimal(result[0] or 0)
                nombre = result[1]

                if stock < cantidad:
                    return {"ok": False, "message": f"Stock insuficiente: {nombre}"}

            # 🍔 RECETA
            else:

                cursor.execute("""
                    SELECT rd.insumo_id, rd.cantidad, rd.unidad
                    FROM recetas r
                    JOIN recetas_detalle rd ON r.id = rd.receta_id
                    WHERE r.producto_id = ?
                """, (producto_id,))

                insumos = cursor.fetchall()

                for insumo_id, cantidad_base, unidad in insumos:

                    cantidad_total = Decimal(cantidad_base) * cantidad
                    cantidad_real = convertir_cantidad(cantidad_total, unidad)

                    cursor.execute("SELECT stock, nombre FROM productos WHERE id=?", (insumo_id,))
                    result = cursor.fetchone()

                    stock = Decimal(result[0] or 0)
                    nombre = result[1]

                    if stock < cantidad_real:
                        return {"ok": False, "message": f"Stock insuficiente: {nombre}"}

        return {"ok": True}

    finally:
        conn.close()


# =============================
# 💰 CREAR VENTA
# =============================
def crear_venta(data):
    conn = get_connection()
    cursor = conn.cursor()
    usuario_id = session.get("user_id")

    try:
        detalles = data.get("detalles", [])

        if not detalles:
            raise Exception("No hay productos en la venta")

        # 🔥 VALIDAR STOCK
        validacion = validar_stock(data)
        if not validacion.get("ok"):
            raise Exception(validacion.get("message"))

        total = Decimal("0")
        costo_total = Decimal("0")

        # =============================
        # CALCULAR TOTAL
        # =============================
        for item in detalles:
            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")
            precio = to_decimal(item["precio"], "Precio")

            total += cantidad * precio
            costo_total += calcular_costo_producto(cursor, producto_id, cantidad)

        utilidad = total - costo_total

        # =============================
        # INSERT VENTA
        # =============================
        cursor.execute("""
            INSERT INTO ventas (mesa, cliente, cliente_id, total, metodo_pago, usuario, costo_total, utilidad, usuario_id)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("mesa"),
            data.get("cliente"),
            data.get("cliente_id"),
            total,
            data.get("metodo_pago", "Efectivo"),
            data.get("usuario", "admin"),
            costo_total,
            utilidad,
            usuario_id
        ))

        venta_id = cursor.fetchone()[0]

        # =============================
        # DETALLE + STOCK
        # =============================
        for item in detalles:

            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")
            precio = to_decimal(item["precio"], "Precio")

            cursor.execute("""
                INSERT INTO detalle_ventas (venta_id, producto_id, cantidad, precio)
                VALUES (?, ?, ?, ?)
            """, (venta_id, producto_id, cantidad, precio))

            cursor.execute("SELECT tipo FROM productos WHERE id = ?", (producto_id,))
            tipo = cursor.fetchone()[0]

            # 🥃 LICOR / BEBIDA
            if tipo in ["LICORES", "BEBIDAS"]:

                cursor.execute("SELECT stock, nombre FROM productos WHERE id=?", (producto_id,))
                result = cursor.fetchone()

                stock = Decimal(result[0] or 0)
                nombre = result[1]

                if stock < cantidad:
                    raise Exception(f"Stock insuficiente: {nombre}")

                cursor.execute("""
                    UPDATE productos
                    SET stock = ISNULL(stock, 0) - ?
                    WHERE id = ?
                """, (cantidad, producto_id))

            # 🍔 RECETA
            else:

                cursor.execute("""
                    SELECT rd.insumo_id, rd.cantidad, rd.unidad
                    FROM recetas r
                    JOIN recetas_detalle rd ON r.id = rd.receta_id
                    WHERE r.producto_id = ?
                """, (producto_id,))

                insumos = cursor.fetchall()

                for insumo_id, cantidad_base, unidad in insumos:

                    cantidad_total = Decimal(cantidad_base) * cantidad
                    cantidad_real = convertir_cantidad(cantidad_total, unidad)

                    cursor.execute("SELECT stock FROM productos WHERE id=?", (insumo_id,))
                    stock = Decimal(cursor.fetchone()[0] or 0)

                    if stock < cantidad_real:
                        raise Exception("Stock insuficiente")

                    cursor.execute("""
                        UPDATE productos
                        SET stock = ISNULL(stock, 0) - ?
                        WHERE id = ?
                    """, (cantidad_real, insumo_id))

        conn.commit()

        return {
            "message": "Venta registrada correctamente",
            "venta_id": venta_id,
            "total": float(total),
            "costo_total": float(costo_total),
            "utilidad": float(utilidad)
        }

    except Exception as e:
        conn.rollback()
        print("❌ ERROR VENTA:", e)
        raise e

    finally:
        conn.close()


# =============================
# 📄 CONSULTAR VENTAS
# =============================
def get_ventas():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT v.id, v.cliente, v.total, v.costo_total, v.utilidad, v.fecha, u.nombre AS usuario
        FROM ventas v
        LEFT JOIN usuarios u ON v.usuario_id = u.id
        ORDER BY v.id DESC
    """)

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data


# =============================
# 📄 DETALLE VENTA
# =============================
def get_venta_detalle(venta_id):
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT dv.producto_id, p.nombre, dv.cantidad, dv.precio
        FROM detalle_ventas dv
        JOIN productos p ON dv.producto_id = p.id
        WHERE dv.venta_id = ?
    """, (venta_id,))

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data