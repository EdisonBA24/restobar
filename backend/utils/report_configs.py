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