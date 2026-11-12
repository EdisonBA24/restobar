
from config import Config


# =====================================================
# MOTOR DE BASE DE DATOS
# =====================================================

IS_POSTGRES = (
    str(
        getattr(Config, "DB_ENGINE", "sqlserver")
    ).strip().lower() == "postgres"
)


# =====================================================
# CONSTRUCTOR DE NOMBRES DE TABLAS
# =====================================================

def _tbl(nombre):

    return (
        f"restobar.{nombre}"
        if IS_POSTGRES
        else f"[restobar.{nombre}]"
    )


# =====================================================
# TABLAS EXISTENTES
# =====================================================

CLIENTES = _tbl("clientes")

CLIENTES_DIRECCIONES = _tbl("clientes_direcciones")

COMPRAS = _tbl("compras")

DETALLE_COMPRAS = _tbl("detalle_compras")

DETALLE_PEDIDOS = _tbl("detalle_pedidos")

DETALLE_PEDIDO_COMPONENTES = _tbl("detalle_pedido_componentes")

DETALLE_PEDIDO_CATALOGO_SNAPSHOT = _tbl("detalle_pedido_catalogo_snapshot")

DETALLE_PEDIDO_COMPONENTES_SNAPSHOT = _tbl("detalle_pedido_componentes_snapshot")

DETALLE_VENTAS = _tbl("detalle_ventas")

PAGOS = _tbl("pagos")

PEDIDOS = _tbl("pedidos")

PRODUCTOS = _tbl("productos")

PROVEEDORES = _tbl("proveedores")

RECETAS = _tbl("recetas")

RECETAS_DETALLE = _tbl("recetas_detalle")

UNIDADES_MEDIDA = _tbl("unidades_medida")

USUARIOS = _tbl("usuarios")

VENTAS = _tbl("ventas")

TIPOS_IVA = _tbl("tipos_iva")


# =====================================================
# CATALOGO COMERCIAL
# =====================================================

CATALOGO_LINEAS = _tbl("catalogo_lineas")

CATALOGO_CATEGORIAS = _tbl("catalogo_categorias")

CATALOGO_ITEMS = _tbl("catalogo_items")


# =====================================================
# PRECIOS
# =====================================================

CATALOGO_PRECIOS = _tbl("catalogo_precios")

CATALOGO_PRECIOS_HISTORIAL = _tbl(
    "catalogo_precios_historial"
)


# =====================================================
# CONFIGURACION DE MENUS
# =====================================================

MENU_CONFIGURACIONES = _tbl("menu_configuraciones")

MENU_CATEGORIAS = _tbl("menu_categorias")

MENU_CATEGORIA_PRODUCTOS = _tbl(
    "menu_categoria_productos"
)
