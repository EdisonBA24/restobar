from database.connection import get_connection
from flask import session
from decimal import Decimal


# =============================
# 💾 CREAR PAGO
# =============================
def crear_pago(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        empleado = data.get("empleado")
        monto = Decimal(str(data.get("monto", 0)))
        concepto = data.get("concepto")
        fecha = data.get("fecha")

        usuario_id = session.get("user_id")

        if not empleado or not concepto:
            raise Exception("Datos incompletos")

        if monto <= 0:
            raise Exception("Monto inválido")

        cursor.execute("""
            INSERT INTO pagos (
                empleado,
                monto,
                concepto,
                fecha,
                usuario_id
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
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

    cursor.execute("""
        SELECT 
            p.id,
            p.empleado,
            p.monto,
            p.concepto,
            p.fecha,
            u.nombre AS usuario
        FROM pagos p
        LEFT JOIN usuarios u ON p.usuario_id = u.id
        ORDER BY p.id DESC
    """)

    columns = [c[0] for c in cursor.description]
    data = [dict(zip(columns, r)) for r in cursor.fetchall()]

    conn.close()
    return data