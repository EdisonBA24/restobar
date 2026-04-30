from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from config import Config


# =============================
# 🔧 VALIDAR DECIMAL
# =============================
def to_decimal(value, field="valor"):
    try:
        if value is None or str(value).strip() == "":
            raise Exception(f"{field} vacío")

        return Decimal(str(value))

    except (InvalidOperation, Exception):
        raise Exception(f"{field} inválido: {value}")


# =============================
# 💾 CREAR PAGO
# =============================
def crear_pago(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        empleado = data.get("empleado")
        concepto = data.get("concepto")
        fecha = data.get("fecha")

        monto = to_decimal(data.get("monto", 0), "Monto")

        usuario_id = session.get("user_id")

        # 🔥 VALIDACIONES MÁS ROBUSTAS
        if not empleado or not str(empleado).strip():
            raise Exception("Empleado requerido")

        if not concepto or not str(concepto).strip():
            raise Exception("Concepto requerido")

        if monto <= 0:
            raise Exception("Monto inválido")

        # 🔥 MOTOR DINÁMICO
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        query = f"""
            INSERT INTO restobar.pagos (
                empleado,
                monto,
                concepto,
                fecha,
                usuario_id
            )
            VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder}, {placeholder})
        """

        cursor.execute(query, (
            empleado,
            monto,
            concepto,
            fecha,
            usuario_id
        ))

        conn.commit()

        return "Pago registrado correctamente"

    except Exception as e:
        conn.rollback()
        print("❌ ERROR PAGO:", e)
        raise e

    finally:
        conn.close()


# =============================
# 📄 CONSULTAR PAGOS
# =============================
def get_pagos():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute("""
            SELECT 
                p.id,
                p.empleado,
                p.monto,
                p.concepto,
                p.fecha,
                u.nombre AS usuario
            FROM restobar.pagos p
            LEFT JOIN restobar.usuarios u ON p.usuario_id = u.id
            ORDER BY p.id DESC
        """)

        columns = [c[0] for c in cursor.description]

        data = []
        for r in cursor.fetchall():
            row = dict(zip(columns, r))

            # 🔥 NORMALIZACIÓN SEGURA
            row["monto"] = float(row.get("monto") or 0)

            data.append(row)

        return data

    except Exception as e:
        print("❌ ERROR GET PAGOS:", e)
        raise e

    finally:
        conn.close()