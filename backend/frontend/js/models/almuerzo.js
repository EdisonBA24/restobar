/**
 * ===========================================================
 * Modelo de Almuerzo
 * ===========================================================
 */

export class Almuerzo {

    constructor() {

        this.id = crypto.randomUUID();

        this.sopa = null;

        this.proteina = null;

        this.seco = null;

        this.ensalada = null;

        this.jugo = null;

        this.observaciones = "";

        this.subtotal = 0;

    }

    limpiar() {

        this.sopa = null;

        this.proteina = null;

        this.seco = null;

        this.ensalada = null;

        this.jugo = null;

        this.observaciones = "";

        this.subtotal = 0;

    }

    calcularSubtotal() {

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

        this.subtotal = total;

        return total;

    }

    esValido() {

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

        copia.sopa = this.sopa;

        copia.proteina = this.proteina;

        copia.seco = this.seco;

        copia.ensalada = this.ensalada;

        copia.jugo = this.jugo;

        copia.observaciones = this.observaciones;

        copia.subtotal = this.subtotal;

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

            (total, item) => total + item.subtotal,

            0

        );

    }

}