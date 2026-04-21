from database.connection import get_connection


def crear_receta(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        producto_id = data["producto_id"]
        detalle = data["detalle"]

        # 🔥 1. VERIFICAR SI YA EXISTE
        cursor.execute("""
            SELECT id
            FROM recetas
            WHERE producto_id = ?
        """, (producto_id,))

        receta = cursor.fetchone()

        if receta:
            receta_id = receta[0]

            # 🔥 2. BORRAR DETALLE ANTERIOR
            cursor.execute("""
                DELETE FROM recetas_detalle
                WHERE receta_id = ?
            """, (receta_id,))

        else:
            # 🔥 3. CREAR NUEVA RECETA
            cursor.execute("""
                INSERT INTO recetas (producto_id, activo)
                OUTPUT INSERTED.id
                VALUES (?, 1)
            """, (producto_id,))

            receta_id = cursor.fetchone()[0]

        # 🔥 4. INSERTAR NUEVO DETALLE
        for item in detalle:
            cursor.execute("""
                INSERT INTO recetas_detalle (receta_id, insumo_id, cantidad, unidad)
                VALUES (?, ?, ?, ?)
            """, (
                receta_id,
                item["insumo_id"],
                item["cantidad"],
                item["unidad"]
            ))

        conn.commit()

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

    cursor.execute("""
        SELECT r.id
        FROM recetas r
        WHERE r.producto_id = ?
    """, (producto_id,))

    receta = cursor.fetchone()

    if not receta:
        return {"detalle": []}

    receta_id = receta[0]

    cursor.execute("""
        SELECT insumo_id, cantidad, unidad
        FROM recetas_detalle
        WHERE receta_id = ?
    """, (receta_id,))

    data = [
        {"insumo_id": row[0], "cantidad": float(row[1]), "unidad": row[2]}
        for row in cursor.fetchall()
    ]

    conn.close()

    return {"detalle": data}