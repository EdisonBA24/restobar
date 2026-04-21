from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from services.ventas_service import crear_venta


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
# 📦 VALIDAR STOCK (SOLO VALIDAR)
# =============================
def validar_stock_pedido(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        for item in data["detalles"]:

            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")

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
                    return {
                        "ok": False,
                        "message": f"Stock insuficiente: {nombre}"
                    }

        return {"ok": True}

    finally:
        conn.close()


# =============================
# 🧾 CREAR PEDIDO
# =============================
def crear_pedido(data):

    conn = get_connection()
    cursor = conn.cursor()
    usuario_id = session.get("user_id")

    try:
        detalles = data.get("detalles", [])

        if not detalles:
            raise Exception("No hay productos en el pedido")

        total = Decimal("0")

        # =============================
        # 🔥 CALCULAR TOTAL (SIN COSTO)
        # =============================
        for item in detalles:
            cantidad = to_decimal(item["cantidad"], "Cantidad")
            precio = to_decimal(item["precio"], "Precio")

            total += cantidad * precio

        # =============================
        # INSERT PEDIDO
        # =============================
        cursor.execute("""
            INSERT INTO pedidos (mesa, tipo, cliente, cliente_id, estado, usuario_id, total)
            OUTPUT INSERTED.id
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("mesa"),
            data.get("tipo"),
            data.get("cliente"),
            data.get("cliente_id"),
            data.get("estado"),
            usuario_id,
            total
        ))

        pedido_id = cursor.fetchone()[0]

        # =============================
        # DETALLE PEDIDO (SIN STOCK)
        # =============================
        for item in detalles:

            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")
            precio = to_decimal(item["precio"], "Precio")

            cursor.execute("""
                INSERT INTO detalle_pedidos (pedido_id, producto_id, cantidad, precio)
                VALUES (?, ?, ?, ?)
            """, (pedido_id, producto_id, cantidad, precio))

        conn.commit()

        return {
            "message": "Pedido registrado correctamente",
            "total": float(total),
            "pedido_id": pedido_id
        }

    except Exception as e:
        conn.rollback()
        print("❌ ERROR PEDIDO:", e)
        raise e

    finally:
        conn.close()


# =============================
# 📄 CONSULTAR PEDIDOS
# =============================
def get_pedidos():

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.id, p.mesa, p.tipo, p.cliente, p.total, p.fecha, p.estado, u.nombre AS usuario
        FROM pedidos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.id DESC
    """)

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data


# =============================
# 📄 DETALLE PEDIDO
# =============================
def get_pedido_detalle(pedido_id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT pe.mesa, dp.producto_id, p.nombre, dp.cantidad, dp.precio
        FROM detalle_pedidos dp
        JOIN pedidos pe ON dp.pedido_id = pe.id
        JOIN productos p ON dp.producto_id = p.id
        WHERE dp.pedido_id = ?
    """, (pedido_id,))

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data


# =============================
# 🧾 FACTURAR PEDIDO → VENTA
# =============================
def facturar_pedido(pedido_id, metodo_pago="Efectivo"):

    conn = get_connection()
    cursor = conn.cursor()
    

    try:
        cursor.execute("""
            SELECT id, estado, mesa, cliente, cliente_id
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if not pedido:
            raise Exception("Pedido no existe")

        if pedido[1] == "facturado":
            raise Exception("El pedido ya fue facturado")

        # =============================
        # DETALLE
        # =============================
        cursor.execute("""
            SELECT producto_id, cantidad, precio
            FROM detalle_pedidos
            WHERE pedido_id = ?
        """, (pedido_id,))

        detalles_db = cursor.fetchall()

        if not detalles_db:
            raise Exception("Pedido sin productos")

        # =============================
        # DATA VENTA
        # =============================
        data_venta = {
            "cliente": pedido[3] or f"Mesa {pedido[2]}",
            "cliente_id": pedido[4],  # 🔥 NUEVO
            "mesa": pedido[2],          # 🔥 NUEVO
           ## "tipo": pedido[1],          # 🔥 NUEVO
            "metodo_pago": metodo_pago,
            "usuario": session.get("nombreUsuario", "admin"),  # 🔥 CORRECTO
            "detalles": []
        }

        for producto_id, cantidad, precio in detalles_db:
            data_venta["detalles"].append({
                "producto_id": producto_id,
                "cantidad": float(cantidad),
                "precio": float(precio)
            })

        # =============================
        # CREAR VENTA
        # =============================
        resultado = crear_venta(data_venta)

        # =============================
        # ACTUALIZAR PEDIDO
        # =============================
        cursor.execute("""
            UPDATE pedidos
            SET estado = 'facturado'
            WHERE id = ?
        """, (pedido_id,))

        conn.commit()

        return {
            "message": "Pedido facturado correctamente",
            "venta": resultado
        }

    except Exception as e:
        conn.rollback()
        print("❌ ERROR FACTURAR PEDIDO:", e)
        raise e

    finally:
        conn.close()