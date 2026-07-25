from config import Config

IS_POSTGRES = getattr(Config, "DB_ENGINE", "sqlserver") == "postgres"

def _tbl(nombre):
    return f"restobar.{nombre}" if IS_POSTGRES else f"[restobar.{nombre}]"

CLIENTES = _tbl("clientes")
CLIENTES_DIRECCIONES = _tbl("clientes_direcciones")
COMPRAS = _tbl("compras")
DETALLE_COMPRAS = _tbl("detalle_compras")
DETALLE_PEDIDOS = _tbl("detalle_pedidos")
DETALLE_PEDIDO_COMPONENTES = _tbl("detalle_pedido_componentes")
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








