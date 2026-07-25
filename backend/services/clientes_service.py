from database.connection import get_connection
from config import Config
from database.db_objects import CLIENTES, CLIENTES_DIRECCIONES
import re


def _get_db_settings():
    db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
    is_postgres = db_engine == "postgres"
    placeholder = "%s" if is_postgres else "?"
    return is_postgres, placeholder


def _normalizar_valor(valor):
    valor = (valor or "").strip()
    return valor or None

def _normalizar_direccion(valor):

    valor = _normalizar_valor(valor)

    if not valor:
        return None

    # Mayúsculas
    valor = valor.upper()

    # Eliminar espacios repetidos
    valor = re.sub(r"\s+", " ", valor)

    # Eliminar espacios antes y después del #
    valor = re.sub(r"\s*#\s*", "#", valor)

    # Eliminar espacios alrededor de guiones
    valor = re.sub(r"\s*-\s*", "-", valor)

    return valor.strip()


def _buscar_cliente_duplicado(cursor, campo, valor, placeholder, is_postgres, excluir_id=None):
    valor = _normalizar_valor(valor)

    if not valor:
        return None

    campo_expr = (
        f"LOWER(TRIM(COALESCE({campo}, '')))"
        if is_postgres
        else f"LOWER(LTRIM(RTRIM(ISNULL({campo}, ''))))"
    )

    query = f"""
        SELECT c.id, c.nombre
        FROM {CLIENTES} c
        WHERE {campo_expr} = LOWER({placeholder})
    """
    params = [valor]

    if excluir_id is not None:
        query += f" AND c.id <> {placeholder}"
        params.append(excluir_id)

    cursor.execute(query, params)
    return cursor.fetchone()


def _validar_cliente_unico(cursor, data, placeholder, is_postgres, excluir_id=None):
    for campo in ["documento", "telefono"]:
        duplicado = _buscar_cliente_duplicado(
            cursor,
            campo,
            data.get(campo),
            placeholder,
            is_postgres,
            excluir_id
        )

        if duplicado:
            return {
                "status": "error",
                "message": f"Ya existe un cliente registrado con ese {campo}",
                "status_code": 409
            }

    return None

def _buscar_direccion_duplicada(
    cursor,
    cliente_id,
    nombre,
    direccion,
    placeholder,
    is_postgres,
    excluir_id=None
):

    nombre = _normalizar_valor(nombre)
    direccion = _normalizar_direccion(direccion)
    
    nombre_expr = (
        "LOWER(TRIM(COALESCE(nombre,'')))"
        if is_postgres
        else "LOWER(LTRIM(RTRIM(ISNULL(nombre,''))))"
    )

    direccion_expr = (
        "LOWER(TRIM(COALESCE(direccion,'')))"
        if is_postgres
        else "LOWER(LTRIM(RTRIM(ISNULL(direccion,''))))"
    )

    # =============================
    # VALIDAR NOMBRE
    # =============================

    if nombre:

        query = f"""
            SELECT id
            FROM {CLIENTES_DIRECCIONES}
            WHERE
                cliente_id = {placeholder}
                AND activo = 1
                AND {nombre_expr}=LOWER({placeholder})
        """

        params = [cliente_id, nombre]

        if excluir_id:

            query += f" AND id <> {placeholder}"

            params.append(excluir_id)

        cursor.execute(query, params)

        if cursor.fetchone():

            return "nombre"

    # =============================
    # VALIDAR DIRECCION
    # =============================

    if direccion:

        query = f"""
            SELECT id
            FROM {CLIENTES_DIRECCIONES}
            WHERE
                cliente_id = {placeholder}
                AND activo = 1
                AND {direccion_expr}=LOWER({placeholder})
        """

        params = [cliente_id, direccion]

        if excluir_id:

            query += f" AND id <> {placeholder}"

            params.append(excluir_id)

        cursor.execute(query, params)

        if cursor.fetchone():

            return "direccion"

    return None


def _validar_direcciones(
    cursor,
    cliente_id,
    direcciones,
    placeholder,
    is_postgres
):

    for direccion in direcciones or []:

        conflicto = _buscar_direccion_duplicada(

            cursor,

            cliente_id,

            direccion.get("nombre"),

            direccion.get("direccion"),

            placeholder,

            is_postgres,

            direccion.get("id")

        )

        if conflicto == "nombre":

            return {

                "status":"error",

                "message":f"La dirección '{direccion.get('nombre')}' ya existe para este cliente.",

                "status_code":409

            }

        if conflicto == "direccion":

            return {

                "status":"error",

                "message":"Esta dirección ya está registrada para este cliente.",

                "status_code":409

            }

    return None

# =============================
# DIRECCIONES
# =============================

def _guardar_direcciones(cursor, cliente_id, direcciones, placeholder):

    if not direcciones:
        return

    for direccion in direcciones:

        cursor.execute(f"""
            INSERT INTO {CLIENTES_DIRECCIONES}
            (
                cliente_id,
                nombre,
                direccion,
                barrio,
                referencia,
                principal,
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
                {placeholder}
            )
        """, (

            cliente_id,

            _normalizar_valor(direccion.get("nombre")),

            _normalizar_direccion(direccion.get("direccion")),

            _normalizar_valor(direccion.get("barrio")),

            _normalizar_valor(direccion.get("referencia")),

            1 if direccion.get("principal") else 0,

            1 if direccion.get("activo", True) else 0

        ))

def _obtener_direcciones(cursor, cliente_id, placeholder):

    cursor.execute(f"""
        SELECT
            id,
            nombre,
            direccion,
            barrio,
            referencia,
            principal,
            activo
        FROM {CLIENTES_DIRECCIONES}
        WHERE cliente_id = {placeholder}
        ORDER BY principal DESC, id
    """, (cliente_id,))

    columnas = [col[0] for col in cursor.description]

    return [

        dict(zip(columnas, fila))

        for fila in cursor.fetchall()

    ]

# =============================
# GET CLIENTE POR ID
# =============================
def get_cliente_por_id(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:

        is_postgres, placeholder = _get_db_settings()

        cursor.execute(f"""
            SELECT
                id,
                nombre,
                documento,
                telefono,
                email,
                activo
            FROM {CLIENTES}
            WHERE id = {placeholder}
              AND activo = 1
        """, (id,))

        row = cursor.fetchone()

        if not row:
            return None

        columnas = [c[0] for c in cursor.description]

        cliente = dict(zip(columnas, row))

        cliente["direcciones"] = _obtener_direcciones(
            cursor,
            id,
            placeholder
        )

        return cliente

    finally:

        conn.close()


def _actualizar_direcciones(cursor, cliente_id, direcciones, placeholder):

    direcciones = direcciones or []

    # IDs que vienen desde el frontend (direcciones existentes)
    ids_frontend = [
        int(d["id"])
        for d in direcciones
        if d.get("id")
    ]

    # Obtener IDs activos actuales en BD
    cursor.execute(
        f"""
        SELECT id
        FROM {CLIENTES_DIRECCIONES}
        WHERE cliente_id = {placeholder}
          AND activo = 1
        """,
        (cliente_id,)
    )

    ids_bd = [fila[0] for fila in cursor.fetchall()]

    # ==========================
    # INSERT / UPDATE
    # ==========================
    for direccion in direcciones:

        nombre = _normalizar_valor(direccion.get("nombre"))
        direccion_txt = _normalizar_direccion(direccion.get("direccion"))
        barrio = _normalizar_valor(direccion.get("barrio"))
        referencia = _normalizar_valor(direccion.get("referencia"))
        principal = 1 if direccion.get("principal") else 0
        activo = 1 if direccion.get("activo", True) else 0

        if direccion.get("id"):

            cursor.execute(
                f"""
                UPDATE {CLIENTES_DIRECCIONES}
                SET
                    nombre={placeholder},
                    direccion={placeholder},
                    barrio={placeholder},
                    referencia={placeholder},
                    principal={placeholder},
                    activo={placeholder}
                WHERE
                    id={placeholder}
                """,
                (
                    nombre,
                    direccion_txt,
                    barrio,
                    referencia,
                    principal,
                    activo,
                    direccion["id"]
                )
            )

        else:

            cursor.execute(
                f"""
                INSERT INTO {CLIENTES_DIRECCIONES}
                (
                    cliente_id,
                    nombre,
                    direccion,
                    barrio,
                    referencia,
                    principal,
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
                    {placeholder}
                )
                """,
                (
                    cliente_id,
                    nombre,
                    direccion_txt,
                    barrio,
                    referencia,
                    principal,
                    activo
                )
            )

    # ==========================
    # DESACTIVAR ELIMINADAS
    # ==========================
    ids_eliminar = [
        id_bd
        for id_bd in ids_bd
        if id_bd not in ids_frontend
    ]

    for id_direccion in ids_eliminar:

        cursor.execute(
            f"""
            UPDATE {CLIENTES_DIRECCIONES}
            SET activo = 0
            WHERE id = {placeholder}
            """,
            (id_direccion,)
        )

def get_all_clientes(page=1, limit=10, solo_inactivos=False, search=None):

    offset = (page - 1) * limit

    conn = get_connection()
    cursor = conn.cursor()

    try:
        estado = 0 if solo_inactivos else 1

        # 🔥 FIX CLAVE: evitar error si no existe DB_ENGINE
        db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
        is_postgres = db_engine == "postgres"

        # 🔥 funciones compatibles
        null_fn = "COALESCE" if is_postgres else "ISNULL"
        placeholder = "%s" if is_postgres else "?"

        query = f"""
        SELECT 
            c.*,
            cd.nombre as nombre_direccion_principal, 
            cd.direccion as direccion_principal
        FROM {CLIENTES} c
        LEFT JOIN {CLIENTES_DIRECCIONES} cd
        ON cd.cliente_id = c.id
        AND cd.principal = 1
        AND cd.activo = 1
        WHERE c.activo = {placeholder}
        """

        params = [estado]

        if search and str(search).strip() != "":
            like = f"%{search.lower()}%"

            query += f"""
            AND (
                LOWER({null_fn}(c.nombre, '')) LIKE {placeholder} OR
                LOWER({null_fn}(c.documento, '')) LIKE {placeholder} OR
                LOWER({null_fn}(c.telefono, '')) LIKE {placeholder}
            )
            """

            params.extend([like, like, like])

        # 🔥 paginación compatible
        if is_postgres:
            query += f"""
            ORDER BY c.id DESC
            LIMIT {placeholder} OFFSET {placeholder}
            """
            params.extend([limit, offset])
        else:
            query += f"""
            ORDER BY c.id DESC
            OFFSET {placeholder} ROWS FETCH NEXT {placeholder} ROWS ONLY
            """
            params.extend([offset, limit])

        cursor.execute(query, params)

        columns = [column[0] for column in cursor.description]

        data = []
        for row in cursor.fetchall():
            r = dict(zip(columns, row))

            # 🔥 NORMALIZACIÓN (evita errores en frontend)
            r["id"] = int(r.get("id") or 0)

            data.append(r)

        return data

    except Exception as e:
        print("❌ ERROR GET CLIENTES:", e)
        return []

    finally:
        conn.close()


# =============================
# CREATE
# =============================
def create_cliente(data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        print("📥 DATA CLIENTE:", data)

        is_postgres, placeholder = _get_db_settings()

        data["documento"] = _normalizar_valor(data.get("documento"))
        data["telefono"] = _normalizar_valor(data.get("telefono"))

        duplicado = _validar_cliente_unico(cursor, data, placeholder, is_postgres)
        if duplicado:
            return duplicado

        if is_postgres:

            cursor.execute(f"""
                INSERT INTO {CLIENTES}
                (
                    nombre,
                    documento,
                    telefono,
                    usuario_id,
                    activo
                )
                VALUES
                (
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    1
                )
                RETURNING id
            """, (

                data.get("nombre"),

                data.get("documento"),

                data.get("telefono"),

                data.get("usuario_id") or 1

            ))

            cliente_id = cursor.fetchone()[0]

        else:

            cursor.execute(f"""
                INSERT INTO {CLIENTES}
                (
                    nombre,
                    documento,
                    telefono,
                    usuario_id,
                    activo
                )
                VALUES
                (
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    {placeholder},
                    1
                )
            """, (

                data.get("nombre"),

                data.get("documento"),

                data.get("telefono"),

                data.get("usuario_id") or 1

            ))

            cursor.execute("SELECT SCOPE_IDENTITY()")

            cliente_id = int(cursor.fetchone()[0])

        # =====================================
        # VALIDAR DIRECCIONES
        # =====================================

        validacion = _validar_direcciones(

            cursor,

            cliente_id,

            data.get("direcciones", []),

            placeholder,

            is_postgres

        )

        if validacion:

            conn.rollback()

            return validacion


        # =====================================
        # GUARDAR DIRECCIONES
        # =====================================

        _guardar_direcciones(

            cursor,

            cliente_id,

            data.get("direcciones", []),

            placeholder

        )

        conn.commit()

        print("✅ CLIENTE INSERTADO")

        return {"status": "success", "message": "Cliente creado", "cliente_id": cliente_id}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR CREATE CLIENTE:", e)

        return {"status": "error", "message": str(e)}

    finally:
        conn.close()


# =============================
# UPDATE
# =============================
def update_cliente(id, data):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        is_postgres, placeholder = _get_db_settings()

        data["documento"] = _normalizar_valor(data.get("documento"))
        data["telefono"] = _normalizar_valor(data.get("telefono"))

        duplicado = _validar_cliente_unico(cursor, data, placeholder, is_postgres, excluir_id=id)
        if duplicado:
            return duplicado

        cursor.execute(f"""
            UPDATE {CLIENTES}
            SET nombre={placeholder}, documento={placeholder}, telefono={placeholder}
            WHERE id={placeholder} AND activo=1
        """, (
            data.get("nombre"),
            data.get("documento"),
            data.get("telefono"),
            id
        ))

        # =====================================
        # VALIDAR DIRECCIONES
        # =====================================

        validacion = _validar_direcciones(

            cursor,

            id,

            data.get("direcciones", []),

            placeholder,

            is_postgres

        )

        if validacion:

            conn.rollback()

            return validacion


        # =====================================
        # ACTUALIZAR DIRECCIONES
        # =====================================

        _actualizar_direcciones(

            cursor,

            id,

            data.get("direcciones", []),

            placeholder

        )

        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ UPDATE CLIENTE: sin cambios")

        return {"status": "success", "message": "Cliente actualizado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR UPDATE CLIENTE:", e)

        return {"status": "error", "message": str(e)}

    finally:
        conn.close()


# =============================
# DELETE
# =============================
def delete_cliente(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        db_engine = getattr(Config, "DB_ENGINE", "sqlserver")
        placeholder = "%s" if db_engine == "postgres" else "?"

        cursor.execute(f"UPDATE {CLIENTES} SET activo = 0 WHERE id = {placeholder}", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ DELETE CLIENTE: no encontrado")

        return {"status": "success", "message": "Cliente desactivado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR DELETE CLIENTE:", e)

        return {"status": "error", "message": str(e)}

    finally:
        conn.close()


# =============================
# ACTIVATE
# =============================
def activar_cliente(id):

    conn = get_connection()
    cursor = conn.cursor()

    try:
        is_postgres, placeholder = _get_db_settings()

        cursor.execute(
            f"SELECT documento, telefono FROM {CLIENTES} WHERE id = {placeholder}",
            (id,)
        )
        cliente = cursor.fetchone()

        if not cliente:
            return {"status": "error", "message": "Cliente no encontrado", "status_code": 404}

        duplicado = _validar_cliente_unico(
            cursor,
            {"documento": cliente[0], "telefono": cliente[1]},
            placeholder,
            is_postgres,
            excluir_id=id
        )
        if duplicado:
            return duplicado

        cursor.execute(f"UPDATE {CLIENTES} SET activo = 1 WHERE id = {placeholder}", (id,))
        conn.commit()

        if cursor.rowcount == 0:
            print("⚠️ ACTIVATE CLIENTE: no encontrado")

        return {"status": "success", "message": "Cliente activado"}

    except Exception as e:
        conn.rollback()
        print("❌ ERROR ACTIVATE CLIENTE:", e)

        return {"status": "error", "message": str(e)}

    finally:
        conn.close()
