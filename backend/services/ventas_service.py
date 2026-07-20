from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from config import Config
from database.db_objects import PRODUCTOS, USUARIOS, VENTAS, DETALLE_VENTAS


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
# 🧠 CALCULAR COSTO
# =============================
#def calcular_costo_producto(cursor, producto_id, cantidad):

#    is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
#    placeholder = "%s" if is_postgres else "?"

#    cursor.execute(f"SELECT tipo, costo FROM restobar.productos WHERE id = {placeholder}", (producto_id,))
#    result = cursor.fetchone()

#    if not result:
#        return Decimal("0")

#    tipo = result[0]
#    costo_directo = Decimal(result[1] or 0)

    # 🥃 LICOR / BEBIDA
#    if tipo in ["LICORES", "BEBIDAS"]:
#        return costo_directo * cantidad

    # 🍔 RECETA
#    cursor.execute(f"""
#        SELECT rd.insumo_id, rd.cantidad, rd.unidad
#        FROM restobar.recetas r
#        JOIN restobar.recetas_detalle rd ON r.id = rd.receta_id
#        WHERE r.producto_id = {placeholder}
#    """, (producto_id,))

#    insumos = cursor.fetchall()

#    if not insumos:
#        return Decimal("0")

#    costo_total = Decimal("0")

#    for insumo_id, cantidad_base, unidad in insumos:

#        cantidad_total = Decimal(cantidad_base or 0) * cantidad
#        cantidad_real = convertir_cantidad(cantidad_total, unidad)

#        cursor.execute(f"SELECT costo FROM restobar.productos WHERE id = {placeholder}", (insumo_id,))
#        result = cursor.fetchone()

#        costo_unitario = Decimal(result[0] or 0) if result else Decimal("0")

#        costo_total += costo_unitario * cantidad_real

#    return costo_total


# =============================
# 📦 VALIDAR STOCK
# =============================
#def validar_stock(data):
#    conn = get_connection()
#    cursor = conn.cursor()

#    try:
#        if not data or "detalles" not in data:
#            return {"ok": False, "message": "Datos inválidos"}

#        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
#        placeholder = "%s" if is_postgres else "?"

#        for item in data["detalles"]:

#            producto_id = item.get("producto_id")
#            cantidad = to_decimal(item.get("cantidad"), "Cantidad")

#            cursor.execute(f"SELECT tipo FROM restobar.productos WHERE id = {placeholder}", (producto_id,))
#            row = cursor.fetchone()

#            if not row:
#                return {"ok": False, "message": "Producto no existe"}

#            tipo = row[0]

#            # 🥃 DIRECTO
#            if tipo in ["LICORES", "BEBIDAS"]:

#                cursor.execute(f"SELECT stock, nombre FROM restobar.productos WHERE id={placeholder}", (producto_id,))
#                result = cursor.fetchone()

#                stock = Decimal(result[0] or 0)
#                nombre = result[1]

#                if stock < cantidad:
#                    return {"ok": False, "message": f"Stock insuficiente: {nombre}"}

            # 🍔 RECETA
#            else:

#               cursor.execute(f"""
#                    SELECT rd.insumo_id, rd.cantidad, rd.unidad
#                    FROM restobar.recetas r
#                    JOIN restobar.recetas_detalle rd ON r.id = rd.receta_id
#                    WHERE r.producto_id = {placeholder}
#                """, (producto_id,))

#                insumos = cursor.fetchall()

#                for insumo_id, cantidad_base, unidad in insumos:

#                    cantidad_total = Decimal(cantidad_base or 0) * cantidad
#                    cantidad_real = convertir_cantidad(cantidad_total, unidad)

#                    cursor.execute(f"SELECT stock, nombre FROM restobar.productos WHERE id={placeholder}", (insumo_id,))
#                    result = cursor.fetchone()

#                    stock = Decimal(result[0] or 0)
#                    nombre = result[1]

#                    if stock < cantidad_real:
#                        return {"ok": False, "message": f"Stock insuficiente: {nombre}"}

#        return {"ok": True}

#    finally:
#        conn.close()


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

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"
        null_fn = "COALESCE" if is_postgres else "ISNULL"

        # 🔥 VALIDAR STOCK
        #validacion = validar_stock(data)
        #if not validacion.get("ok"):
        #    raise Exception(validacion.get("message"))

        total = Decimal("0")
        #costo_total = Decimal("0")

        # =============================
        # CALCULAR TOTAL
        # =============================
        for item in detalles:
            producto_id = item.get("producto_id")
            cantidad = to_decimal(item.get("cantidad"), "Cantidad")
            precio = to_decimal(item.get("precio"), "Precio")

            total += cantidad * precio
        #    costo_total += calcular_costo_producto(cursor, producto_id, cantidad)

        #utilidad = total - costo_total

        # =============================
        # INSERT VENTA
        # =============================
        if is_postgres:
            cursor.execute(f"""
                INSERT INTO {VENTAS} (mesa, cliente, cliente_id, total, metodo_pago, usuario, usuario_id, categoria)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
                RETURNING id
            """, (
                data.get("mesa"),
                data.get("cliente"),
                data.get("cliente_id"),
                total,
                data.get("metodo_pago", "Efectivo"),
                data.get("usuario", "admin"),
                #costo_total,
                #utilidad,
                usuario_id,
                data.get("categoria")
            ))
        else:
            cursor.execute(f"""
                INSERT INTO {VENTAS} (mesa, cliente, cliente_id, total, metodo_pago, usuario, usuario_id, categoria)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data.get("mesa"),
                data.get("cliente"),
                data.get("cliente_id"),
                total,
                data.get("metodo_pago", "Efectivo"),
                data.get("usuario", "admin"),
                #costo_total,
                #utilidad,
                usuario_id,
                data.get("categoria")
            ))  
            

        venta_id = cursor.fetchone()[0]

        # =============================
        # DETALLE + STOCK
        # =============================
        for item in detalles:

            producto_id = item.get("producto_id")
            cantidad = to_decimal(item.get("cantidad"), "Cantidad")
            precio = to_decimal(item.get("precio"), "Precio")

            cursor.execute(f"""
                INSERT INTO {DETALLE_VENTAS} (venta_id, producto_id, cantidad, precio)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (venta_id, producto_id, cantidad, precio))

            #cursor.execute(f"SELECT tipo FROM restobar.productos WHERE id = {placeholder}", (producto_id,))
            #tipo_row = cursor.fetchone()

            #if not tipo_row:
            #    raise Exception("Producto no encontrado")

            #tipo = tipo_row[0]

            #if tipo in ["LICORES", "BEBIDAS"]:

            #    cursor.execute(f"SELECT stock, nombre FROM restobar.productos WHERE id={placeholder}", (producto_id,))
            #    result = cursor.fetchone()

            #    stock = Decimal(result[0] or 0)
            #    nombre = result[1]

            #    if stock < cantidad:
            #        raise Exception(f"Stock insuficiente: {nombre}")

            #    cursor.execute(f"""
            #        UPDATE restobar.productos
            #        SET stock = {null_fn}(stock, 0) - {placeholder}
            #        WHERE id = {placeholder}
            #    """, (cantidad, producto_id))

            #else:

            #    cursor.execute(f"""
            #        SELECT rd.insumo_id, rd.cantidad, rd.unidad
            #        FROM restobar.recetas r
            #        JOIN restobar.recetas_detalle rd ON r.id = rd.receta_id
            #        WHERE r.producto_id = {placeholder}
            #    """, (producto_id,))

            #    insumos = cursor.fetchall()

            #    for insumo_id, cantidad_base, unidad in insumos:

            #        cantidad_total = Decimal(cantidad_base or 0) * cantidad
            #        cantidad_real = convertir_cantidad(cantidad_total, unidad)

            #        cursor.execute(f"SELECT stock FROM restobar.productos WHERE id={placeholder}", (insumo_id,))
            #        stock_row = cursor.fetchone()

            #        stock = Decimal(stock_row[0] or 0) if stock_row else Decimal("0")

            #        if stock < cantidad_real:
            #            raise Exception("Stock insuficiente")

            #        cursor.execute(f"""
            #            UPDATE restobar.productos
            #            SET stock = {null_fn}(stock, 0) - {placeholder}
            #            WHERE id = {placeholder}
            #        """, (cantidad_real, insumo_id))

        conn.commit()

        return {
            "message": "Venta registrada correctamente",
            "venta_id": venta_id,
            "total": float(total),
            #"costo_total": float(costo_total),
            #"utilidad": float(utilidad)
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
#v.costo_total, v.utilidad, 
def get_ventas():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT v.id, v.cliente, v.total, v.fecha, u.nombre AS usuario
            FROM {VENTAS} v
            LEFT JOIN {USUARIOS} u ON v.usuario_id = u.id
            ORDER BY v.id DESC
        """)

        columns = [c[0] for c in cursor.description]
        data = []

        for r in cursor.fetchall():
            row = dict(zip(columns, r))
            row["total"] = float(row.get("total") or 0)
            #row["costo_total"] = float(row.get("costo_total") or 0)
            #row["utilidad"] = float(row.get("utilidad") or 0)
            data.append(row)

        return data

    finally:
        conn.close()


# =============================
# 📄 DETALLE VENTA
# =============================
def get_venta_detalle(venta_id):
    conn = get_connection()
    cursor = conn.cursor()

    try:
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        cursor.execute(f"""
            SELECT dv.producto_id, p.nombre, dv.cantidad, dv.precio
            FROM {DETALLE_VENTAS} dv
            JOIN {PRODUCTOS} p ON dv.producto_id = p.id
            WHERE dv.venta_id = {placeholder}
        """, (venta_id,))

        columns = [c[0] for c in cursor.description]
        data = []

        for r in cursor.fetchall():
            row = dict(zip(columns, r))
            row["cantidad"] = float(row.get("cantidad") or 0)
            row["precio"] = float(row.get("precio") or 0)
            data.append(row)

        return data

    finally:
        conn.close()