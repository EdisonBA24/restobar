REPORTE_COMPRAS = {

    "nombre_hoja": "Compras",

    "titulo": "REPORTE DE COMPRAS",

    "encabezados": [

        "Compra",
        "Fecha",
        "Proveedor",
        "Usuario",
        "Subtotal",
        "IVA",
        "Total"

    ],

    "columnas": [

        "id",
        "fecha",
        "proveedor",
        "usuario",
        "subtotal",
        "iva_total",
        "total"

    ],

    "columnas_width": {

        1: 10,
        2: 22,
        3: 30,
        4: 20,
        5: 18,
        6: 18,
        7: 18

    },

    "columnas_moneda": [5, 6, 7],

    "columnas_totales": {

        "subtotal": 5,
        "iva_total": 6,
        "total": 7

    }

}

REPORTE_DETALLE_COMPRAS = {

    "nombre_hoja":"Detalle Compras",

    "titulo":"DETALLE DE COMPRAS",

    "encabezados":[

        "Compra",

        "Fecha",

        "Proveedor",

        "Código",

        "Producto",

        "Cantidad",

        "Precio Unitario",

        "IVA %",

        "Subtotal",

        "Valor IVA",

        "Total"

    ],

    "columnas":[

        "compra_id",

        "fecha",

        "proveedor",

        "codigo",

        "producto",

        "cantidad",

        "precio_unitario",

        "iva",

        "subtotal",

        "valor_iva",

        "total"

    ],

    "columnas_width": {

        1: 10,
        2: 22,
        3: 30,
        4: 18,
        5: 35,
        6: 12,
        7: 18,
        8: 10,
        9: 18,
        10: 18,
        11: 18

    },

    "columnas_moneda":[

        7,

        9,

        10,

        11

    ],

    "columnas_decimal":[

        6,

        8

    ]

}

# ==========================================
# RESUMEN REPORTE COMPRAS
# ==========================================

def construir_resumen_compras(filtros):

    return [

        (
            "Período",
            filtros.get("periodo")
        ),

        (
            "Fecha Inicio",
            filtros.get("fecha_inicio")
        ),

        (
            "Fecha Final",
            filtros.get("fecha_fin")
        ),

        (
            "Proveedor",
            "Todos"
        ),

        (
            "Buscar",
            filtros.get("buscar")
        )

    ]


# ==========================================
# HOJA COMPRAS
# ==========================================

def crear_hoja_compras(
    compras,
    resumen
):

    return {

        **REPORTE_COMPRAS,

        "resumen": resumen,

        "datos": compras

    }


# ==========================================
# HOJA DETALLE COMPRAS
# ==========================================

def crear_hoja_detalle_compras(
    detalles,
    resumen
):

    return {

        **REPORTE_DETALLE_COMPRAS,

        "resumen": resumen,

        "datos": detalles

    }


# ==========================================
# HOJAS REPORTE COMPRAS
# ==========================================

def obtener_hojas_compras(
    data,
    resumen
):

    return [

        crear_hoja_compras(

            data.get(
                "compras",
                []
            ),

            resumen

        ),

        crear_hoja_detalle_compras(

            data.get(
                "detalles",
                []
            ),

            resumen

        )

    ]

# ==========================================
# REPORTE PEDIDOS
# ==========================================

REPORTE_PEDIDOS = {

    "nombre_hoja": "Pedidos",

    "titulo": "REPORTE DE PEDIDOS",

    "encabezados": [

        "Pedido",
        "Fecha",
        "Cliente",
        "Servicio",
        "Mesa",
        "Estado",
        "Usuario",
        "Total"

    ],

    "columnas": [

        "id",
        "fecha",
        "cliente",
        "tipo",
        "mesa",
        "estado",
        "usuario",
        "total"

    ],

    "columnas_width": {

        1: 10,
        2: 22,
        3: 30,
        4: 20,
        5: 12,
        6: 18,
        7: 20,
        8: 18

    },

    "columnas_moneda": [

        8

    ],

    "columnas_totales": {

        "total": 8

    }

}


# ==========================================
# REPORTE DETALLE PEDIDOS
# ==========================================

REPORTE_DETALLE_PEDIDOS = {

    "nombre_hoja": "Detalle Pedidos",

    "titulo": "DETALLE DE PEDIDOS",

    "encabezados": [

        "Pedido",
        "Fecha",
        "Cliente",
        "Servicio",
        "Mesa",
        "Estado",
        "Usuario",
        "Tipo",
        "Producto",
        "Cantidad",
        "Precio Unitario",
        "Subtotal",
        "Componentes"

    ],

    "columnas": [

        "pedido_id",
        "fecha",
        "cliente",
        "servicio",
        "mesa",
        "estado",
        "usuario",
        "tipo_item",
        "producto",
        "cantidad",
        "precio",
        "subtotal",
        "componentes"

    ],

    "columnas_width": {

        1: 10,
        2: 22,
        3: 30,
        4: 20,
        5: 12,
        6: 18,
        7: 20,
        8: 22,
        9: 30,
        10: 12,
        11: 18,
        12: 18,
        13: 60

    },

    "columnas_moneda": [

        11,
        12

    ],

    "columnas_decimal": [

        10

    ]

}

# ==========================================
# RESUMEN REPORTE PEDIDOS
# ==========================================

def construir_resumen_pedidos(filtros):

    return [

        (
            "Período",
            filtros.get("periodo")
        ),

        (
            "Fecha Inicio",
            filtros.get("fecha_inicio")
        ),

        (
            "Fecha Final",
            filtros.get("fecha_fin")
        ),

        (
            "Estado",
            filtros.get("estado")
            or "Todos"
        ),

        (
            "Servicio",
            filtros.get("servicio")
            or "Todos"
        ),

        (
            "Buscar",
            filtros.get("buscar")
            or "Todos"
        )

    ]

# ==========================================================
# 📑 HOJA PEDIDOS
# ==========================================================

def crear_hoja_pedidos(
    pedidos,
    resumen
):

    return {

        **REPORTE_PEDIDOS,

        "resumen":
            resumen,

        "datos":
            pedidos

    }


# ==========================================================
# 📑 HOJA DETALLE PEDIDOS
# ==========================================================

def crear_hoja_detalle_pedidos(
    detalles,
    resumen
):

    return {

        **REPORTE_DETALLE_PEDIDOS,

        "resumen":
            resumen,

        "datos":
            detalles

    }


# ==========================================================
# 📑 HOJAS REPORTE PEDIDOS
# ==========================================================

def obtener_hojas_pedidos(
    data,
    resumen
):

    return [

        crear_hoja_pedidos(

            data.get(
                "pedidos",
                []
            ),

            resumen

        ),

        crear_hoja_detalle_pedidos(

            data.get(
                "detalles",
                []
            ),

            resumen

        )

    ]