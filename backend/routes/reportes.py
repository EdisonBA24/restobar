from flask import Blueprint, request, jsonify, send_file, session
import pandas as pd
import io
from config import Config
from database.connection import get_connection

reportes_bp = Blueprint("reportes", __name__)


# =============================
# 🔐 HELPERS
# =============================
def validar_sesion():
    return "user_id" in session

def get_placeholder():
    return "?" if Config.DB_ENGINE == "sqlserver" else "%s"


# ==========================
# 📦 INVENTARIO
# ==========================
@reportes_bp.route("/reportes/inventario", methods=["GET"])
def reporte_inventario():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT 
                p.nombre,
                p.stock,
                um.nombre AS unidad,
                p.costo,
                (p.stock * p.costo) AS valor_inventario
            FROM productos p
            JOIN unidades_medida um ON p.unidad_id = um.id
            WHERE tipo = 'INSUMO'
        """)

        rows = cursor.fetchall()

        data = [{
            "Producto": r[0],
            "Stock": float(r[1] or 0),
            "Unidad": r[2],
            "Costo Unitario": float(r[3] or 0),
            "Valor Inventario": float(r[4] or 0)
        } for r in rows]

        return jsonify(data)

    except Exception as e:
        print("❌ ERROR INVENTARIO:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if conn:
            conn.close()


# ==========================
# 💰 VENTAS
# ==========================
@reportes_bp.route("/reportes/ventas", methods=["GET"])
def reporte_ventas():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    conn = None
    try:
        inicio = request.args.get("inicio")
        fin = request.args.get("fin")

        conn = get_connection()
        cursor = conn.cursor()

        placeholder = get_placeholder()

        query = """
            SELECT fecha, total, utilidad
            FROM ventas
        """

        params = []

        if inicio and fin:
            query += f" WHERE cast(fecha as date) between {placeholder} and {placeholder}"
            params = [inicio, fin]

        query += " ORDER BY fecha"

        cursor.execute(query, params)
        rows = cursor.fetchall()

        data = [{
            "Fecha": r[0].strftime("%Y-%m-%d") if r[0] else "",
            "Total": float(r[1] or 0),
            "Utilidad": float(r[2] or 0)
        } for r in rows]

        return jsonify(data)

    except Exception as e:
        print("❌ ERROR VENTAS:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if conn:
            conn.close()


# ==========================
# 📊 COSTOS
# ==========================
@reportes_bp.route("/reportes/costos", methods=["GET"])
def reporte_costos():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()

        placeholder = get_placeholder()

        cursor.execute("""
            SELECT id, nombre, precio_venta
            FROM productos
            WHERE tipo = 'RECETA'
        """)

        productos = cursor.fetchall()
        data = []

        for p in productos:
            producto_id, nombre, precio_venta = p
            precio_venta = float(precio_venta or 0)

            cursor.execute(f"""
                SELECT rd.insumo_id, rd.cantidad, rd.unidad
                FROM recetas r
                JOIN recetas_detalle rd ON r.id = rd.receta_id
                WHERE r.producto_id = {placeholder}
            """, (producto_id,))

            insumos = cursor.fetchall()
            costo_total = 0

            for insumo_id, cantidad, unidad in insumos:
                cantidad = float(cantidad or 0)

                if unidad and str(unidad).lower() in ["g", "gr", "gramos"]:
                    cantidad = cantidad / 1000

                cursor.execute(f"""
                    SELECT costo
                    FROM productos
                    WHERE id = {placeholder}
                """, (insumo_id,))

                row = cursor.fetchone()
                costo_unitario = float(row[0] or 0) if row else 0

                costo_total += costo_unitario * cantidad

            utilidad = precio_venta - costo_total
            margen = (utilidad / precio_venta * 100) if precio_venta > 0 else 0

            data.append({
                "Producto": nombre,
                "Precio": precio_venta,
                "Costo": round(costo_total, 2),
                "Utilidad": round(utilidad, 2),
                "Margen": round(margen, 2)
            })

        return jsonify(data)

    except Exception as e:
        print("❌ ERROR COSTOS:", e)
        return jsonify({"status": "error", "message": str(e)}), 500

    finally:
        if conn:
            conn.close()


# ==========================
# 📥 EXPORTAR EXCEL
# ==========================
@reportes_bp.route("/reportes/exportar", methods=["POST"])
def exportar_excel():

    if not validar_sesion():
        return jsonify({"status": "unauthorized"}), 401

    try:
        data = request.json.get("data", [])
        nombre = request.json.get("nombre", "reporte")

        if not data:
            return jsonify({
                "status": "error",
                "message": "No hay datos para exportar"
            }), 400

        df = pd.DataFrame(data)
        df = df.fillna(0)

        output = io.BytesIO()
        df.to_excel(output, index=False, engine="openpyxl")
        output.seek(0)

        return send_file(
            output,
            download_name=f"{nombre}.xlsx",
            as_attachment=True,
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print("❌ ERROR EXPORTAR:", e)
        return jsonify({"status": "error", "message": str(e)}), 500