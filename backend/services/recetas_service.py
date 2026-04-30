from database.connection import get_connection
from config import Config


def crear_receta(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        producto_id = data.get("producto_id")
        detalle = data.get("detalle", [])

        if not producto_id:
            raise Exception("producto_id requerido")

        if not detalle:
            raise Exception("Detalle vacío")

        # 🔥 MOTOR
        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        print(f"🧪 CREAR RECETA producto_id={producto_id} | items={len(detalle)}")

        # =============================
        # 🔍 VERIFICAR SI EXISTE
        # =============================
        cursor.execute(f"""
            SELECT id
            FROM restobar.recetas
            WHERE producto_id = {placeholder}
        """, (producto_id,))

        receta = cursor.fetchone()

        if receta:
            receta_id = receta[0]

            print(f"♻️ RECETA EXISTENTE id={receta_id} → limpiando detalle")

            # =============================
            # 🧹 BORRAR DETALLE
            # =============================
            cursor.execute(f"""
                DELETE FROM restobar.recetas_detalle
                WHERE receta_id = {placeholder}
            """, (receta_id,))

        else:
            # =============================
            # 🆕 CREAR RECETA
            # =============================
            print("🆕 CREANDO NUEVA RECETA")

            if is_postgres:
                cursor.execute(f"""
                    INSERT INTO restobar.recetas (producto_id, activo)
                    VALUES ({placeholder}, 1)
                    RETURNING id
                """, (producto_id,))
            else:
                cursor.execute(f"""
                    INSERT INTO restobar.recetas (producto_id, activo)
                    OUTPUT INSERTED.id
                    VALUES ({placeholder}, 1)
                """, (producto_id,))

            row = cursor.fetchone()
            if not row:
                raise Exception("Error creando receta")

            receta_id = row[0]

        # =============================
        # 📦 INSERTAR DETALLE
        # =============================
        for item in detalle:

            if not item.get("insumo_id"):
                raise Exception("insumo_id requerido")

            cursor.execute(f"""
                INSERT INTO restobar.recetas_detalle (receta_id, insumo_id, cantidad, unidad)
                VALUES ({placeholder}, {placeholder}, {placeholder}, {placeholder})
            """, (
                receta_id,
                item.get("insumo_id"),
                item.get("cantidad") or 0,
                item.get("unidad")
            ))

        conn.commit()

        print(f"✅ RECETA GUARDADA id={receta_id}")

        return {"message": "Receta guardada correctamente"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR RECETA:", e)
        raise e

    finally:
        conn.close()


def obtener_receta(producto_id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        # 🔥 validación defensiva
        if not producto_id:
            return {"detalle": []}

        is_postgres = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"
        placeholder = "%s" if is_postgres else "?"

        # =============================
        # 🔍 BUSCAR RECETA (solo activa)
        # =============================
        cursor.execute(f"""
            SELECT r.id
            FROM restobar.recetas r
            WHERE r.producto_id = {placeholder}
            AND r.activo = 1
        """, (producto_id,))

        receta = cursor.fetchone()

        print(f"📦 RECETA BUSCADA producto_id={producto_id} → receta={receta}")

        if not receta:
            return {"detalle": []}

        receta_id = receta[0]

        # =============================
        # 📄 DETALLE ORDENADO
        # =============================
        cursor.execute(f"""
            SELECT insumo_id, cantidad, unidad
            FROM restobar.recetas_detalle
            WHERE receta_id = {placeholder}
            ORDER BY id
        """, (receta_id,))

        data = []
        for row in cursor.fetchall():
            data.append({
                "insumo_id": int(row[0]) if row[0] is not None else None,
                "cantidad": float(row[1] or 0),
                "unidad": row[2]
            })

        print(f"📄 DETALLE RECETA ({receta_id}) → {len(data)} items")

        return {"detalle": data}

    finally:
        conn.close()