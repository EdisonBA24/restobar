from database.connection import get_connection
from flask import session
from decimal import Decimal, InvalidOperation
from config import Config
from database.db_objects import PAGOS, USUARIOS


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

        usuario_id = data.get("usuario_id")
        concepto = data.get("concepto")
        fecha = data.get("fecha")
        monto = to_decimal(data.get("monto", 0), "Monto")

        # VALIDACIONES
        if not usuario_id:
            raise Exception("Debe seleccionar un empleado")

        if not concepto or not str(concepto).strip():
            raise Exception("Concepto requerido")

        if monto <= 0:
            raise Exception("Monto inválido")

        # MOTOR DINÁMICO
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        # =============================
        # OBTENER NOMBRE DEL EMPLEADO
        # =============================
        query_usuario = f"""
            SELECT nombre
            FROM {USUARIOS}
            WHERE id = {placeholder}
              AND activo = 1
        """

        cursor.execute(query_usuario, (usuario_id,))
        row = cursor.fetchone()

        if not row:
            raise Exception("El empleado seleccionado no existe o está inactivo")

        empleado = row[0]

        # =============================
        # INSERTAR PAGO
        # =============================
        query = f"""
            INSERT INTO {PAGOS} (
                empleado,
                monto,
                concepto,
                fecha,
                usuario_id
            )
            VALUES (
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder},
                {placeholder}
            )
        """

        cursor.execute(
            query,
            (
                empleado,
                monto,
                concepto,
                fecha,
                usuario_id
            )
        )

        conn.commit()

        return "Pago registrado correctamente"

    except Exception as e:
        conn.rollback()
        print("❌ ERROR PAGO:", e)
        raise

    finally:
        conn.close()


# =============================
# 📄 CONSULTAR PAGOS
# =============================
def get_pagos():

    conn = get_connection()
    cursor = conn.cursor()

    try:

        cursor.execute(f"""
            SELECT
                p.id,
                u.nombre AS empleado,
                p.monto,
                p.concepto,
                p.fecha
            FROM {PAGOS} p
            INNER JOIN {USUARIOS} u
                ON p.usuario_id = u.id
            ORDER BY p.id DESC
        """)

        columns = [c[0] for c in cursor.description]

        data = []

        for r in cursor.fetchall():
            row = dict(zip(columns, r))
            row["monto"] = float(row.get("monto") or 0)
            data.append(row)

        return data

    except Exception as e:
        print("❌ ERROR GET PAGOS:", e)
        raise

    finally:
        conn.close()