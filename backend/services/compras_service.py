from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from config import Config
from database.db_objects import COMPRAS, DETALLE_COMPRAS, PRODUCTOS, USUARIOS, PROVEEDORES, TIPOS_IVA
import traceback, math
from datetime import datetime


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
    fecha = data.get("fecha")

    try:
        proveedor_id = data.get("proveedor_id")

        if not proveedor_id:
            raise Exception("Proveedor requerido")

        detalles = data.get("detalles", [])

        if not detalles:
            raise Exception("No hay productos en la compra")

        if not usuario_id:
            raise Exception("Usuario no autenticado")

        if not fecha:
            raise Exception("La fecha de la compra es obligatoria")

        # ==========================================
        # Combinar la fecha seleccionada con la hora
        # actual del servidor
        # ==========================================

        try:

            fecha_compra = datetime.strptime(fecha, "%Y-%m-%d")

            ahora = datetime.now()

            fecha = fecha_compra.replace(

            hour=ahora.hour,

            minute=ahora.minute,

            second=ahora.second,

            microsecond=0

        )

        except ValueError:

            raise Exception(
                "Formato de fecha inválido."
            )

        # 🔥 MOTOR DINÁMICO
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"
        null_fn = "COALESCE" if is_postgres else "ISNULL"

        subtotal_compra = Decimal("0")
        iva_total = Decimal("0")
        total_compra = Decimal("0")

        # =========================
        # INSERT COMPRA
        # =========================
        if is_postgres:
            cursor.execute(f"""
                INSERT INTO {COMPRAS} (proveedor_id, subtotal, iva_total, total, usuario_id, fecha, fecha_registro)
                VALUES ({placeholder}, 0, 0, 0, {placeholder}, {placeholder}, CURRENT_TIMESTAMP)
                RETURNING id
            """, (proveedor_id, usuario_id, fecha))
        else:
            cursor.execute(f"""
                INSERT INTO {COMPRAS} (proveedor_id, subtotal, iva_total, total, usuario_id, fecha, fecha_registro)
                OUTPUT INSERTED.id
                VALUES ({placeholder}, 0, 0, 0, {placeholder}, {placeholder}, GETDATE())
            """, (proveedor_id, usuario_id, fecha))

        compra_id = cursor.fetchone()[0]

        # =========================
        # DETALLE + STOCK + COSTO
        # =========================
        for item in detalles:

            producto_id = item.get("producto_id")

            if not producto_id:
                raise Exception("Producto inválido")

            cantidad = to_decimal(item.get("cantidad"), "Cantidad")

            precio_unitario = to_decimal(
                item.get("precio_unitario"),
                "Precio Unitario"
            )

            tipo_iva_id = item.get("tipo_iva_id")

            if not tipo_iva_id:
                raise Exception("Debe seleccionar el tipo de IVA")
            
            cursor.execute(f"""
                SELECT porcentaje
                FROM {TIPOS_IVA}
                WHERE id = {placeholder}
                AND activo = 1
            """, (tipo_iva_id,))

            row = cursor.fetchone()

            if not row:
                raise Exception("Tipo de IVA no válido")

            iva_porcentaje = Decimal(str(row[0]))

            if cantidad <= 0:
                raise Exception("Cantidad inválida")

            if precio_unitario <= 0:
                raise Exception("Precio Unitario inválido")

            if iva_porcentaje < 0:
                raise Exception("IVA inválido")


            subtotal = cantidad * precio_unitario

            valor_iva = (
                subtotal * iva_porcentaje / Decimal("100")
            )

            total_item = subtotal + valor_iva
            subtotal_compra += subtotal
            iva_total += valor_iva
            total_compra += total_item

            # =========================
            # INSERT DETALLE
            # =========================
            cursor.execute(f"""
                INSERT INTO {DETALLE_COMPRAS}
                (
                    compra_id,
                    producto_id,
                    cantidad,
                    precio_unitario,
                    tipo_iva_id,
                    iva,
                    subtotal,
                    valor_iva,
                    total
                )
                VALUES
                (
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder}
                )
            """, (
                    compra_id,
                    producto_id,
                    cantidad,
                    precio_unitario,
                    tipo_iva_id,
                    iva_porcentaje,
                    subtotal,
                    valor_iva,
                    total_item
            ))

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
                precio_compra=precio_unitario
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
            SET
                subtotal = {placeholder},
                iva_total = {placeholder},
                total = {placeholder}
            WHERE id = {placeholder}
        """, (
                subtotal_compra,
                iva_total,
                total_compra,
                compra_id
        ))

        conn.commit()

        return {
            "id": compra_id,
            "message": "Compra registrada correctamente",
            "subtotal": float(round(subtotal_compra, 2)),
            "iva_total": float(round(iva_total, 2)),
            "total": float(round(total_compra, 2))
        }

    #except Exception as e:
    #    conn.rollback()
    #    print("❌ ERROR COMPRA:", e)
    #    raise e
    except Exception as e:
        conn.rollback()
        print("\n========== ERROR COMPLETO ==========")
        traceback.print_exc()
        raise

    finally:
        conn.close()


# =============================
# 📄 CONSULTAR COMPRAS
# =============================
def get_compras(filtros=None):
    conn = get_connection()
    cursor = conn.cursor()

    if filtros is None:
        filtros = {}

    is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"

    placeholder = "%s" if is_postgres else "?"

    cast_text = "TEXT" if is_postgres else "VARCHAR(20)"

    print("==== FILTROS SERVICE ====")
    print(f"Motor BD: {'PostgreSQL' if is_postgres else 'SQL Server'}")
    print(filtros)

    fecha_inicio = filtros.get("fecha_inicio")
    fecha_fin = filtros.get("fecha_fin")
    proveedor_id = filtros.get("proveedor_id")
    buscar = (filtros.get("buscar") or "").strip()

    page = max(int(filtros.get("page", 1)), 1)
    page_size = max(int(filtros.get("page_size", 10)), 1)

    offset = (page - 1) * page_size

    parametros = []
    where = []

    if fecha_inicio:
        where.append(f"CAST(co.fecha AS DATE) >= {placeholder}")
        parametros.append(fecha_inicio)

    if fecha_fin:
        where.append(f"CAST(co.fecha AS DATE) <= {placeholder}")
        parametros.append(fecha_fin)

    if proveedor_id:
        where.append(f"co.proveedor_id = {placeholder}")
        parametros.append(proveedor_id)

    if buscar:
        where.append(f"""
            (
                p.nombre LIKE {placeholder}
                OR u.nombre LIKE {placeholder}
                OR CAST(co.id as {cast_text}) LIKE {placeholder}
            )
        """)

        texto = f"%{buscar}%"

        parametros.extend([
            texto,
            texto,
            texto
        ])

    where_sql = ""

    if where:
        where_sql = "WHERE " + "\nAND ".join(where) 

    if is_postgres:
        paginacion_sql = f"""
            LIMIT {placeholder}
            OFFSET {placeholder}
        """

    else:
        paginacion_sql = f"""
            OFFSET {placeholder} ROWS
            FETCH NEXT {placeholder} ROWS ONLY
        """    

    parametros_consulta = parametros.copy()

    if is_postgres:
        parametros_consulta.extend([
            page_size,
            offset
        ]) 

    else:
        parametros_consulta.extend([
        offset,
        page_size
    ])

    try:

        # ======================
        # TOTAL REGISTROS
        # ======================
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {COMPRAS} co
            INNER JOIN {PROVEEDORES} p
                ON co.proveedor_id = p.id
            INNER JOIN {USUARIOS} u
                ON co.usuario_id = u.id

            {where_sql}
        """, parametros)

        total_registros = cursor.fetchone()[0]

        cursor.execute(f"""
            SELECT
                co.id,
                p.nombre AS proveedor,
                co.subtotal,
                co.iva_total,
                co.total,
                co.fecha,
                u.nombre AS usuario
            FROM {COMPRAS} co
            INNER JOIN {PROVEEDORES} p
                ON co.proveedor_id = p.id
            INNER JOIN {USUARIOS} u
                ON co.usuario_id = u.id

            {where_sql}
                    
            ORDER BY co.id DESC

            {paginacion_sql}

        """, parametros_consulta)

        total_paginas = math.ceil(total_registros / page_size) if total_registros else 1

        columns = [c[0] for c in cursor.description]

        data = []
        for r in cursor.fetchall():
            row = dict(zip(columns, r))

            # 🔥 normalización frontend
            row["subtotal"] = float(row.get("subtotal") or 0)
            row["iva_total"] = float(row.get("iva_total") or 0)
            row["total"] = float(row.get("total") or 0)

            data.append(row)

        #return data
        return {
            "items": data,
            "page": page,
            "page_size": page_size,
            "total": total_registros,
            "total_pages": total_paginas
        }

    except Exception as e:
        print("\n ======= ❌ ERROR GET COMPRAS ========")
        traceback.print_exc()

        return {
            "items": [],
            "page": page,
            "page_size": page_size,
            "total": 0,
            "total_pages": 0
        }

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
            SELECT
                dc.producto_id,
                p.nombre,
                dc.cantidad,
                dc.precio_unitario,
                dc.tipo_iva_id,
                ti.descripcion AS tipo_iva,
                dc.iva,
                dc.subtotal,
                dc.valor_iva,
                dc.total
            FROM {DETALLE_COMPRAS} dc
            INNER JOIN {PRODUCTOS} p
                ON dc.producto_id = p.id
            INNER JOIN {TIPOS_IVA} ti
                ON dc.tipo_iva_id = ti.id
            WHERE dc.compra_id = {placeholder}
        """, (compra_id,))

        columns = [c[0] for c in cursor.description]

        data = []
        for r in cursor.fetchall():
            row = dict(zip(columns, r))

            # 🔥 normalización
            row["cantidad"] = float(row.get("cantidad") or 0)

            row["precio_unitario"] = float(
                row.get("precio_unitario") or 0
            )

            row["iva"] = float(
                row.get("iva") or 0
            )

            row["subtotal"] = float(
                row.get("subtotal") or 0
            )

            row["valor_iva"] = float(
                row.get("valor_iva") or 0
            )

            row["total"] = float(
                row.get("total") or 0
            )

            data.append(row)

        return data

    except Exception as e:
        print("❌ ERROR DETALLE COMPRA:", e)
        return []

    finally:
        conn.close()


def get_tipos_iva():
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cursor.execute(f"""
            SELECT
                id,
                porcentaje,
                descripcion
            FROM {TIPOS_IVA}
            WHERE activo = 1
            ORDER BY porcentaje
        """)

        columns = [c[0] for c in cursor.description]

        data = []

        for r in cursor.fetchall():
            row = dict(zip(columns, r))
            row["porcentaje"] = float(row["porcentaje"])
            data.append(row)

        return data

    except Exception as e:
        print("❌ ERROR GET TIPOS IVA:", e)
        return []

    finally:
        conn.close()