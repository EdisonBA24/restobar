from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from services.ventas_service import crear_venta
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
# 🔁 CONVERSIÓN UNIDADES
# =============================
def convertir_cantidad(cantidad, unidad):

    cantidad = Decimal(cantidad or 0)

    if not unidad:
        return cantidad

    unidad = str(unidad).lower()

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
        detalles = data.get("detalles", [])

        if not detalles:
            return {"ok": True}  # 🔥 evita error innecesario

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        for item in detalles:

            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")

            cursor.execute(f"""
                SELECT rd.insumo_id, rd.cantidad, rd.unidad
                FROM restobar.recetas r
                JOIN restobar.recetas_detalle rd ON r.id = rd.receta_id
                WHERE r.producto_id = {placeholder}
            """, (producto_id,))

            insumos = cursor.fetchall()

            for insumo_id, cantidad_base, unidad in insumos:

                cantidad_total = Decimal(cantidad_base or 0) * cantidad
                cantidad_real = convertir_cantidad(cantidad_total, unidad)

                cursor.execute(f"""
                    SELECT stock, nombre 
                    FROM restobar.productos 
                    WHERE id = {placeholder}
                """, (insumo_id,))

                result = cursor.fetchone()

                if not result:
                    continue

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

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        total = Decimal("0")

        for item in detalles:
            cantidad = to_decimal(item["cantidad"], "Cantidad")
            precio = to_decimal(item["precio"], "Precio")
            total += cantidad * precio

        # =============================
        # INSERT PEDIDO
        # =============================
        if is_postgres:
            cursor.execute(f"""
                INSERT INTO restobar.pedidos (mesa, tipo, cliente, cliente_id, estado, usuario_id, total, categoria)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING id
            """, (
                data.get("mesa"),
                data.get("tipo"),
                data.get("cliente"),
                data.get("cliente_id"),
                data.get("estado"),
                usuario_id,
                total,
                data.get("categoria")
            ))
        else:
            cursor.execute(f"""
                INSERT INTO restobar.pedidos (mesa, tipo, cliente, cliente_id, estado, usuario_id, total, categoria)
                OUTPUT INSERTED.id
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (
                data.get("mesa"),
                data.get("tipo"),
                data.get("cliente"),
                data.get("cliente_id"),
                data.get("estado"),
                usuario_id,
                total,
                data.get("categoria")
            ))

        pedido_row = cursor.fetchone()
        if not pedido_row:
            raise Exception("Error creando pedido")

        pedido_id = pedido_row[0]

        # =============================
        # DETALLE PEDIDO
        # =============================
        for item in detalles:

            producto_id = item["producto_id"]
            cantidad = to_decimal(item["cantidad"], "Cantidad")
            precio = to_decimal(item["precio"], "Precio")

            cursor.execute(f"""
                INSERT INTO restobar.detalle_pedidos (pedido_id, producto_id, cantidad, precio)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
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

    try:
        cursor.execute("""
            SELECT p.id, p.mesa, p.tipo, p.cliente, p.total, p.fecha, p.estado, u.nombre AS usuario, p.categoria
            FROM restobar.pedidos p
            LEFT JOIN restobar.usuarios u ON p.usuario_id = u.id
            ORDER BY p.id DESC
        """)

        columns = [c[0] for c in cursor.description]

        data = []
        for r in cursor.fetchall():
            row = dict(zip(columns, r))
            row["total"] = float(row.get("total") or 0)
            data.append(row)

        return data

    finally:
        conn.close()


# =============================
# 📄 DETALLE PEDIDO
# =============================
def get_pedido_detalle(pedido_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        # =============================
        # CABECERA PEDIDO
        # =============================
        cursor.execute(f"""
            SELECT
                id,
                mesa,
                tipo,
                cliente,
                categoria,
                estado,
                fecha
            FROM restobar.pedidos
            WHERE id = {placeholder}
        """, (pedido_id,))

        pedido_row = cursor.fetchone()

        if not pedido_row:
            return None

        pedido = {
            "id": pedido_row[0],
            "mesa": pedido_row[1],
            "tipo": pedido_row[2],
            "cliente": pedido_row[3],
            "categoria": pedido_row[4],
            "estado": pedido_row[5],
            "fecha": str(pedido_row[6]) if pedido_row[6] else ""
        }

        # =============================
        # DETALLE
        # =============================
        cursor.execute(f"""
            SELECT
                dp.producto_id,
                p.nombre,
                dp.cantidad,
                dp.precio
            FROM restobar.detalle_pedidos dp
            JOIN restobar.productos p
                ON dp.producto_id = p.id
            WHERE dp.pedido_id = {placeholder}
        """, (pedido_id,))

        columns = [c[0] for c in cursor.description]

        detalle = []

        for r in cursor.fetchall():

            row = dict(zip(columns, r))

            row["cantidad"] = float(row.get("cantidad") or 0)
            row["precio"] = float(row.get("precio") or 0)

            detalle.append(row)

        return {
            "pedido": pedido,
            "detalle": detalle
        }

    finally:
        conn.close()


# =============================
# 🧾 FACTURAR PEDIDO → VENTA
# =============================
def facturar_pedido(pedido_id, metodo_pago="Efectivo", usuario_id=None, *args, **kwargs):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        usuario_id = usuario_id or session.get("user_id") or 1

        print(f"🧾 FACTURAR PEDIDO | id={pedido_id} | metodo={metodo_pago} | usuario_id={usuario_id}")

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        cursor.execute(f"""
            SELECT id, estado, mesa, cliente, cliente_id
            FROM restobar.pedidos
            WHERE id = {placeholder}
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if not pedido:
            raise Exception("Pedido no existe")

        if str(pedido[1]).lower() == "facturado":
            raise Exception("El pedido ya fue facturado")

        cursor.execute(f"""
            SELECT producto_id, cantidad, precio
            FROM restobar.detalle_pedidos
            WHERE pedido_id = {placeholder}
        """, (pedido_id,))

        detalles_db = cursor.fetchall()

        if not detalles_db:
            raise Exception("Pedido sin productos")

        data_venta = {
            "cliente": pedido[3] or f"Mesa {pedido[2]}",
            "cliente_id": pedido[4],
            "mesa": pedido[2],
            "metodo_pago": metodo_pago,
            "usuario": session.get("nombreUsuario") or f"user_{usuario_id}",
            "usuario_id": usuario_id,  # 🔥 clave
            "detalles": []
        }

        for producto_id, cantidad, precio in detalles_db:
            data_venta["detalles"].append({
                "producto_id": producto_id,
                "cantidad": float(cantidad),
                "precio": float(precio)
            })

        resultado = crear_venta(data_venta)

        cursor.execute(f"""
            UPDATE restobar.pedidos
            SET estado = 'facturado'
            WHERE id = {placeholder}
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