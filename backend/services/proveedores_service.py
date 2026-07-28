from database.connection import get_connection
from config import Config
from database.db_objects import PROVEEDORES
import re

def _get_db_settings():
    db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
    is_postgres = db_engine == "postgres"
    placeholder = "%s" if is_postgres else "?"
    return is_postgres, placeholder

def _normalizar_valor(valor):
    valor = (valor or "").strip()
    return valor or None

def _normalizar_nombre(valor):
    valor = _normalizar_valor(valor)

    if not valor:
        return None

    valor = valor.upper()

    # Elimina espacios repetidos
    valor = re.sub(r"\s+", " ", valor)

    return valor.strip()

def _normalizar_proveedor(data):

    nombre = _normalizar_nombre(data.get("nombre"))

    campos = [
        "nit",
        "contacto",
        "telefono",
        "email",
        "direccion",
        "ciudad",
        "observaciones"
    ]

    proveedor = {
        "nombre": nombre
    }

    for campo in campos:
        proveedor[campo] = _normalizar_valor(data.get(campo))

    return proveedor

def _obtener_por_id(
    cursor,
    tabla,
    id,
    placeholder,
    columnas=None
):
    if columnas:

        select = ",\n                ".join(columnas)

    else:

        select = "*"

    cursor.execute(
        f"""
        SELECT
            {select}
        FROM {tabla}
        WHERE id = {placeholder}
        """,
        (id,)
    )

    row = cursor.fetchone()

    if not row:
        return None

    nombres = [c[0] for c in cursor.description]

    return dict(zip(nombres, row))

def _buscar_proveedor_duplicado(
    cursor,
    campo,
    valor,
    placeholder,
    is_postgres,
    excluir_id=None
):
    if campo == "nombre":
        valor = _normalizar_nombre(valor)
    else:
        valor = _normalizar_valor(valor)

    if not valor:
        return None

    campo_expr = (
        f"LOWER(TRIM(COALESCE({campo}, '')))"
        if is_postgres
        else f"LOWER(LTRIM(RTRIM(ISNULL({campo}, ''))))"
    )

    query = f"""
        SELECT id, nombre
        FROM {PROVEEDORES}
        WHERE {campo_expr} = LOWER({placeholder})
    """

    params = [valor]

    if excluir_id is not None:
        query += f" AND id <> {placeholder}"
        params.append(excluir_id)

    cursor.execute(query, params)

    return cursor.fetchone()

def _validar_proveedor_unico(
    cursor,
    data,
    placeholder,
    is_postgres,
    excluir_id=None
):
    duplicado = _buscar_proveedor_duplicado(
        cursor,
        "nombre",
        data.get("nombre"),
        placeholder,
        is_postgres,
        excluir_id
    )

    if duplicado:
        return {
            "status": "error",
            "message": "Ya existe un proveedor registrado con ese nombre.",
            "status_code": 409
        }

    return None

def get_all_proveedores(page=1, limit=10, solo_inactivos=False, search=None):

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:

        estado = 0 if solo_inactivos else 1

        is_postgres, placeholder = _get_db_settings()

        null_fn = "COALESCE" if is_postgres else "ISNULL"

        query = f"""
            SELECT
                id,
                nombre,
                nit,
                contacto,
                telefono,
                email,
                direccion,
                ciudad,
                observaciones,
                activo
            FROM {PROVEEDORES}
            WHERE activo = {placeholder}
        """

        params = [estado]

        if search and str(search).strip():

            like = f"%{search.lower()}%"

            query += f"""
                AND (
                    LOWER({null_fn}(nombre,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(nit,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(contacto,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(telefono,'')) LIKE {placeholder}
                    OR LOWER({null_fn}(ciudad,'')) LIKE {placeholder}
                )
            """

            params.extend([
                like,
                like,
                like,
                like,
                like
            ])

        if is_postgres:

            query += f"""
                ORDER BY id DESC
                LIMIT {placeholder}
                OFFSET {placeholder}
            """

            params.extend([limit, offset])

        else:

            query += f"""
                ORDER BY id DESC
                OFFSET {placeholder} ROWS
                FETCH NEXT {placeholder} ROWS ONLY
            """

            params.extend([offset, limit])

        cursor.execute(query, params)

        columnas = [c[0] for c in cursor.description]

        data = []

        for fila in cursor.fetchall():

            proveedor = dict(zip(columnas, fila))

            proveedor["id"] = int(proveedor["id"])

            data.append(proveedor)

        return data

    except Exception as e:

        print("❌ ERROR GET PROVEEDORES:", e)

        return []

    finally:

        conn.close()

def get_proveedor_por_id(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        _, placeholder = _get_db_settings()

        proveedor = _obtener_por_id(
            cursor,
            PROVEEDORES,
            id,
            placeholder,
            columnas=[
                "id",
                "nombre",
                "nit",
                "contacto",
                "telefono",
                "email",
                "direccion",
                "ciudad",
                "observaciones",
                "activo"
            ]
        )

        if not proveedor or not proveedor["activo"]:
            return None

        return proveedor

    finally:

        conn.close()

def create_proveedor(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres, placeholder = _get_db_settings()

        proveedor = _normalizar_proveedor(data)
    
        if not proveedor["nombre"]:

            return {
                "status": "error",
                "message": "El nombre del proveedor es obligatorio.",
                "status_code": 400
            }

        duplicado = _validar_proveedor_unico(
            cursor,
            data,
            placeholder,
            is_postgres
        )

        if duplicado:
            return duplicado
        
        if is_postgres:

            cursor.execute(f"""
                INSERT INTO {PROVEEDORES}
                (
                    nombre,
                    nit,
                    contacto,
                    telefono,
                    email,
                    direccion,
                    ciudad,
                    observaciones,
                    activo
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
                    1
                )
                RETURNING id
            """, (
                    proveedor["nombre"],
                    proveedor["nit"],
                    proveedor["contacto"],
                    proveedor["telefono"],
                    proveedor["email"],
                    proveedor["direccion"],
                    proveedor["ciudad"],
                    proveedor["observaciones"]
            ))

            proveedor_id = cursor.fetchone()[0]

            conn.commit()

        else:

            cursor.execute(f"""
                INSERT INTO {PROVEEDORES}
                (
                    nombre,
                    nit,
                    contacto,
                    telefono,
                    email,
                    direccion,
                    ciudad,
                    observaciones,
                    activo
                )
                OUTPUT INSERTED.id
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
                    1
                )
            """, (
                    proveedor["nombre"],
                    proveedor["nit"],
                    proveedor["contacto"],
                    proveedor["telefono"],
                    proveedor["email"],
                    proveedor["direccion"],
                    proveedor["ciudad"],
                    proveedor["observaciones"]
            ))

            proveedor_id = cursor.fetchone()[0]

            conn.commit()

        return {
            "status": "success",
            "message": "Proveedor creado correctamente.",
            "proveedor_id": proveedor_id
        }

    except Exception as e:

        conn.rollback()

        print("❌ ERROR CREATE PROVEEDOR:", e)

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        conn.close()

def update_proveedor(id, data):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres, placeholder = _get_db_settings()

        proveedor = _normalizar_proveedor(data)

        if not proveedor["nombre"]:
            return {
                "status": "error",
                "message": "El nombre del proveedor es obligatorio.",
                "status_code": 400
            }

        duplicado = _validar_proveedor_unico(
            cursor,
            proveedor,
            placeholder,
            is_postgres,
            excluir_id=id
        )

        if duplicado:
            return duplicado
        
        cursor.execute(f"""
            UPDATE {PROVEEDORES}
            SET
                nombre={placeholder},
                nit={placeholder},
                contacto={placeholder},
                telefono={placeholder},
                email={placeholder},
                direccion={placeholder},
                ciudad={placeholder},
                observaciones={placeholder}
            WHERE
                id={placeholder}
                AND activo=1
        """, (
                proveedor["nombre"],
                proveedor["nit"],
                proveedor["contacto"],
                proveedor["telefono"],
                proveedor["email"],
                proveedor["direccion"],
                proveedor["ciudad"],
                proveedor["observaciones"],
                id
        ))

        conn.commit()

        if cursor.rowcount == 0:

            return {
                "status": "error",
                "message": "Proveedor no encontrado.",
                "status_code": 404
            }

        return {
            "status": "success",
            "message": "Proveedor actualizado correctamente."
        }

    except Exception as e:

        conn.rollback()

        print("❌ ERROR UPDATE PROVEEDOR:", e)

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        conn.close()

def delete_proveedor(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        _, placeholder = _get_db_settings()

        proveedor = _obtener_por_id(
            cursor,
            PROVEEDORES,
            id,
            placeholder,
            columnas=[
                "id",
                "activo"
            ]
        )

        if not proveedor:

            return {
                "status": "error",
                "message": "Proveedor no encontrado.",
                "status_code": 404
            }

        if not proveedor["activo"]:

            return {
                "status": "error",
                "message": "El proveedor ya se encuentra desactivado.",
                "status_code": 400
            }

        cursor.execute(
            f"""
            UPDATE {PROVEEDORES}
            SET activo = 0
            WHERE id = {placeholder}
            """,
            (id,)
        )

        conn.commit()

        return {
            "status": "success",
            "message": "Proveedor desactivado correctamente."
        }

    except Exception as e:

        conn.rollback()

        print("❌ ERROR DELETE PROVEEDOR:", e)

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        conn.close()

def activar_proveedor(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres, placeholder = _get_db_settings()

        proveedor = _obtener_por_id(
            cursor,
            PROVEEDORES,
            id,
            placeholder,
            columnas=[
                "id",
                "nombre",
                "activo"
            ]
        )

        if not proveedor:

            return {
                "status": "error",
                "message": "Proveedor no encontrado.",
                "status_code": 404
            }

        if proveedor["activo"]:

            return {
                "status": "error",
                "message": "El proveedor ya se encuentra activo.",
                "status_code": 400
            }

        duplicado = _validar_proveedor_unico(
            cursor,
            proveedor,
            placeholder,
            is_postgres,
            excluir_id=id
        )

        if duplicado:
            return duplicado

        cursor.execute(
            f"""
            UPDATE {PROVEEDORES}
            SET activo = 1
            WHERE id = {placeholder}
            """,
            (id,)
        )

        conn.commit()

        return {
            "status": "success",
            "message": "Proveedor activado correctamente."
        }

    except Exception as e:

        conn.rollback()

        print("❌ ERROR ACTIVATE PROVEEDOR:", e)

        return {
            "status": "error",
            "message": str(e)
        }

    finally:

        conn.close()