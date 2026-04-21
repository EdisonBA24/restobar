from flask import Blueprint, request, jsonify, send_file, session
import pyodbc
import pandas as pd
import io
from config import Config

reportes_bp = Blueprint("reportes", __name__)


def get_connection():
    return pyodbc.connect(Config.get_connection_string())


# ==========================
# 📦 INVENTARIO
# ==========================
@reportes_bp.route("/reportes/inventario", methods=["GET"])
def reporte_inventario():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
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

        data = []
        for r in rows:
            data.append({
                "Producto": r[0],
                "Stock": float(r[1] or 0),
                "Unidad": r[2],
                "Costo Unitario": float(r[3] or 0),
                "Valor Inventario": float(r[4] or 0)
            })

        return jsonify(data)

    except Exception as e:
        print("❌ ERROR INVENTARIO:", e)
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================
# 💰 VENTAS
# ==========================
@reportes_bp.route("/reportes/ventas", methods=["GET"])
def reporte_ventas():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        inicio = request.args.get("inicio")
        fin = request.args.get("fin")

        conn = get_connection()
        cursor = conn.cursor()

        query = """
            SELECT fecha, total, utilidad
            FROM ventas
        """

        params = []

        if inicio and fin:
            query += " WHERE cast(fecha as date) between ? and ?"
            params = [inicio, fin]

        query += " ORDER BY fecha"

        cursor.execute(query, params)

        rows = cursor.fetchall()

        data = []
        for r in rows:
            data.append({
                "Fecha": r[0].strftime("%Y-%m-%d"),
                "Total": float(r[1]),
                "Utilidad": float(r[2])
            })

        return jsonify(data)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


# ==========================
# 📊 COSTOS
# ==========================
@reportes_bp.route("/reportes/costos", methods=["GET"])
def reporte_costos():

    if "user_id" not in session:
        return jsonify({"status": "unauthorized"}), 401
    
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, nombre, precio_venta
            FROM productos
            WHERE tipo = 'RECETA'
        """)

        productos = cursor.fetchall()
        data = []

        for p in productos:
            producto_id = p[0]
            nombre = p[1]
            precio_venta = float(p[2] or 0)

            cursor.execute("""
                SELECT rd.insumo_id, rd.cantidad, rd.unidad
                FROM recetas r
                JOIN recetas_detalle rd ON r.id = rd.receta_id
                WHERE r.producto_id = ?
            """, (producto_id,))

            insumos = cursor.fetchall()
            costo_total = 0

            for insumo_id, cantidad, unidad in insumos:
                cantidad = float(cantidad or 0)

                if unidad and str(unidad).lower() in ["g", "gr", "gramos"]:
                    cantidad = cantidad / 1000

                cursor.execute("""
                    SELECT costo
                    FROM productos
                    WHERE id = ?
                """, (insumo_id,))

                row = cursor.fetchone()

                if not row:
                    costo_unitario = 0
                else:
                    costo_unitario = float(row[0] or 0)

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


# ==========================
# 📥 EXPORTAR EXCEL
# ==========================
@reportes_bp.route("/reportes/exportar", methods=["POST"])
def exportar_excel():
    try:
        data = request.json.get("data", [])
        nombre = request.json.get("nombre", "reporte")

        df = pd.DataFrame(data)

        # 🔥 FIX CLAVE
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