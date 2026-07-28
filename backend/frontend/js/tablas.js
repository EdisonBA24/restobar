/**
 * ============================================================
 * TABLA UI
 * ============================================================
 * Componente reutilizable para todos los listados del ERP.
 *
 * Responsabilidades:
 *  - Paginación
 *  - Ordenamiento
 *  - Page Size
 *  - Persistencia
 *  - Indicadores visuales
 *
 * No contiene lógica de negocio.
 * ============================================================
 */

export class TablaUI {

    constructor(config = {}) {

        // Configuración general
        this.nombre = config.nombre ?? "";

        this.callback = config.callback ?? null;

        // Selectores HTML
        this.selectores = {

            tabla: config.tabla ?? null,

            pageSize: config.pageSize ?? null,

            btnAnterior: config.btnAnterior ?? null,

            btnSiguiente: config.btnSiguiente ?? null,

            numeros: config.numeros ?? null,

            resumen: config.resumen ?? null,

            info: config.info ?? null

        };

        // Estado interno de la tabla
        this.estado = {

            page: 1,

            page_size: 10,

            total: 0,

            total_pages: 1,

            sort_by: "id",

            sort_order: "desc"

        };

    }

    /**
    * ==========================================
    * Retorna una copia del estado actual
    * ==========================================
    */
    getEstado() {

        return { ...this.estado };

    }

    /**
    * ==========================================
    * Actualiza una o varias propiedades
    * del estado.
    * ==========================================
    */
    setEstado(nuevoEstado = {}) {

        this.estado = {

            ...this.estado,

            ...nuevoEstado

        };

    }

    /**
     * ==========================================
     * Getters del estado
     * ==========================================
     */

    get page() {

        return this.estado.page;

    }

    get pageSize() {

        return this.estado.page_size;

    }

    get total() {

        return this.estado.total;

    }

    get totalPages() {

        return this.estado.total_pages;

    }

    get sortBy() {

        return this.estado.sort_by;

    }

    get sortOrder() {

        return this.estado.sort_order;

    }

    /**
     * ==========================================
     * Obtiene un elemento configurado
     * ==========================================
     */
    getElemento(nombre) {

        const selector = this.selectores[nombre];

        if (!selector) {

            console.warn(
                `[TablaUI] No existe el selector "${nombre}".`
            );

            return null;

        }

        const elemento =
            document.querySelector(selector);

        if (!elemento) {

            console.warn(
                `[TablaUI] No se encontró el elemento: ${selector}`
            );

        }

        return elemento;

    }

}