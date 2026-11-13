/**
 * ===========================================================
 * Modelo de Almuerzo / Artículo comercial
 * ===========================================================
 */

export class Almuerzo {

    constructor() {

        this.id =
            (window.crypto &&
                typeof window.crypto.randomUUID === "function")
                ? window.crypto.randomUUID()
                : `ALM-${Date.now()}-${Math.random().toString(36).substring(2, 10)}`;

        this.modo = "ADICION";

        this.tipo = "ADICION";

        this.nombre = "Adición";

        this.precioBase = 0;

        this.precio = 0;

        this.cantidad = 1;

        // =====================================
        // DATOS DEL CATÁLOGO
        // =====================================

        this.catalogoItemId = null;

        this.codigoCatalogo = null;

        this.lineaCodigo = null;

        this.tipoCatalogo = null;

        this.configuracionMenu = null;

        this.categoriasMenu = [];

        this.componentesSeleccionados = [];

        // =====================================
        // COMPONENTES LEGACY: ADICIONES
        // =====================================

        this.sopa = null;

        this.proteina = null;

        this.seco = null;

        this.ensalada = null;

        this.jugo = null;

        // =====================================
        // OBSERVACIONES
        // =====================================

        this.observaciones = "";

    }

    limpiar() {

        this.modo = "ADICION";

        this.tipo = "ADICION";

        this.nombre = "Adición";

        this.precioBase = 0;

        this.precio = 0;

        this.cantidad = 1;

        this.catalogoItemId = null;

        this.codigoCatalogo = null;

        this.lineaCodigo = null;

        this.tipoCatalogo = null;

        this.configuracionMenu = null;

        this.categoriasMenu = [];

        this.componentesSeleccionados = [];

        this.sopa = null;

        this.proteina = null;

        this.seco = null;

        this.ensalada = null;

        this.jugo = null;

        this.observaciones = "";

    }

    calcularPrecio() {

        // =====================================
        // ARTÍCULO DEL CATÁLOGO
        // =====================================

        if (this.catalogoItemId) {

            const adicionales =
                (this.componentesSeleccionados || [])
                    .reduce((total, componente) => {

                        const precio =
                            Number(
                                componente.precio_adicional_unitario || 0
                            );

                        const cantidad =
                            Number(componente.cantidad || 1);

                        return total + (precio * cantidad);

                    }, 0);

            this.precio = Number(
                (
                    Number(this.precioBase || 0) + adicionales
                ).toFixed(2)
            );

            return this.precio;

        }

        // =====================================
        // MENÚ LEGACY
        // =====================================

        if (this.modo === "MENU") {

            this.precio =
                Number(this.precioBase || 0);

            return this.precio;

        }

        // =====================================
        // ADICIONES
        // =====================================

        let total = 0;

        if (this.sopa)
            total += Number(this.sopa.precio_venta || 0);

        if (this.proteina)
            total += Number(this.proteina.precio_venta || 0);

        if (this.seco)
            total += Number(this.seco.precio_venta || 0);

        if (this.ensalada)
            total += Number(this.ensalada.precio_venta || 0);

        if (this.jugo)
            total += Number(this.jugo.precio_venta || 0);

        this.precio = total;

        return total;

    }

    esValido() {

        if (this.catalogoItemId) {

            return this.componentesSeleccionados.length > 0;

        }

        return (
            this.sopa &&
            this.proteina &&
            this.seco &&
            this.ensalada &&
            this.jugo
        );

    }

    duplicar() {

        const copia = new Almuerzo();

        copia.modo = this.modo;

        copia.tipo = this.tipo;

        copia.nombre = this.nombre;

        copia.precioBase = this.precioBase;

        copia.precio = this.precio;

        copia.cantidad = Number(this.cantidad || 1);

        copia.catalogoItemId = this.catalogoItemId;

        copia.codigoCatalogo = this.codigoCatalogo;

        copia.lineaCodigo = this.lineaCodigo;

        copia.tipoCatalogo = this.tipoCatalogo;

        copia.configuracionMenu = this.configuracionMenu
            ? { ...this.configuracionMenu }
            : null;

        copia.categoriasMenu = (
            this.categoriasMenu || []
        ).map(categoria => ({
            ...categoria,
            productos: (categoria.productos || []).map(
                producto => ({ ...producto })
            )
        }));

        copia.componentesSeleccionados = (
            this.componentesSeleccionados || []
        ).map(componente => ({ ...componente }));

        copia.sopa = this.sopa ? { ...this.sopa } : null;

        copia.proteina = this.proteina
            ? { ...this.proteina }
            : null;

        copia.seco = this.seco ? { ...this.seco } : null;

        copia.ensalada = this.ensalada
            ? { ...this.ensalada }
            : null;

        copia.jugo = this.jugo ? { ...this.jugo } : null;

        copia.observaciones = this.observaciones;

        return copia;

    }

}


/**
 * ===========================================================
 * Pedido de Almuerzos
 * ===========================================================
 */

export class PedidoAlmuerzo {

    constructor() {
        this.items = [];
    }

    agregar(almuerzo) {
        this.items.push(almuerzo);
    }

    eliminar(id) {
        this.items = this.items.filter(x => x.id !== id);
    }

    buscar(id) {
        return this.items.find(x => x.id === id);
    }

    reemplazar(id, almuerzo) {

        const index = this.items.findIndex(x => x.id === id);

        if (index >= 0)
            this.items[index] = almuerzo;

    }

    duplicar(id) {

        const almuerzo = this.buscar(id);

        if (!almuerzo)
            return;

        this.agregar(almuerzo.duplicar());

    }

    limpiar() {
        this.items = [];
    }

    getCantidad() {
        return this.items.length;
    }

    getTotal() {

        return this.items.reduce(
            (total, item) => total + Number(item.precio || 0),
            0
        );

    }

}