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

        // this.callback = config.callback ?? null;
        this.callback = config.callback ?? (() => { });

        // Selectores HTML
        this.selectores = {

            tabla: config.tabla,

            pageSize: config.pageSize,

            btnAnterior: config.btnAnterior,

            btnSiguiente: config.btnSiguiente,

            numeros: config.numeros,

            resumen: config.resumen,

            info: config.info,

            encabezados: config.encabezados

        };


        this.elementos = {};

        // Elementos obligatorios del componente
        this.elementosRequeridos = [
            "tabla"
        ];

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
     * Actualiza el estado desde una respuesta
     * del backend.
     * ==========================================
     */
    actualizarDesdeBackend(resultado = {}) {

        this.estado = {

            ...this.estado,

            page: resultado.page ?? this.page,

            page_size: resultado.page_size ?? this.pageSize,

            total: resultado.total ?? 0,

            total_pages: resultado.total_pages ?? 1,

            sort_by: resultado.sort_by ?? this.sortBy,

            sort_order: resultado.sort_order ?? this.sortOrder

        };

        this.renderizar();

    }

    /**
     * ==========================================
     * Renderiza todos los componentes visuales
     * ==========================================
     */
    renderizar() {

        this.actualizarBotones();

        this.actualizarPageSize();

        this.actualizarResumen();

        this.actualizarInfo();

        this.actualizarNumeros();

        this.actualizarIndicadoresOrden();

    }

    /**
     * ==========================================
     * Actualiza los botones de navegación
     * ==========================================
     */
    actualizarBotones() {

        const btnAnterior = this.getElemento("btnAnterior");
        const btnSiguiente = this.getElemento("btnSiguiente");

        if (btnAnterior) {
            btnAnterior.disabled = this.page <= 1;
        }

        if (btnSiguiente) {
            btnSiguiente.disabled = this.page >= this.totalPages;
        }

    }

    /**
     * ==========================================
     * Sincroniza el selector de Page Size
     * ==========================================
     */
    actualizarPageSize() {

        const pageSize = this.getElemento("pageSize");

        if (!pageSize) return;

        pageSize.value = String(this.pageSize);

    }

    /**
     * ==========================================
     * Compatibilidad temporal
     * ==========================================
     */
    actualizarControles() {

        this.renderizar();

    }

    actualizarInfo() {

        const info = this.getElemento("info");

        if (!info) return;

        info.textContent =
            `Página ${this.page} de ${this.totalPages}`;

    }

    actualizarResumen() {

        const resumen = this.getElemento("resumen");

        if (!resumen) return;

        if (this.total === 0) {

            resumen.textContent =
                "Mostrando 0 de 0 registros";

            return;
        }

        const inicio =
            ((this.page - 1) * this.pageSize) + 1;

        const fin =
            Math.min(
                this.page * this.pageSize,
                this.total
            );

        resumen.textContent =
            `Mostrando ${inicio} - ${fin} de ${this.total} registros`;

    }

    /**
     * ==========================================
     * Renderiza los números de la paginación
     * ==========================================
     */
    actualizarNumeros() {

        const contenedor = this.getElemento("numeros");

        if (!contenedor) return;

        contenedor.innerHTML = "";

        if (this.totalPages <= 1) return;

        const paginas = this._obtenerPaginasVisibles();

        paginas.forEach(item => {

            if (item === "...") {

                this._crearSeparadorPaginas(contenedor);

                return;

            }

            this._crearBotonPagina(
                contenedor,
                item,
                this.page
            );

        });

    }

    /**
     * ==========================================
     * Crea un botón de paginación
     * ==========================================
     */
    _crearBotonPagina(contenedor, pagina, actual) {

        const boton = document.createElement("button");

        boton.type = "button";
        boton.className = "pg-btn";
        boton.textContent = pagina;

        if (pagina === actual) {
            boton.classList.add("pg-btn-active");
        }

        boton.addEventListener("click", () => {

            if (pagina === actual) return;

            this.irAPagina(pagina);

        });

        contenedor.appendChild(boton);

    }

    /**
     * ==========================================
     * Crea el separador (...)
     * ==========================================
     */
    _crearSeparadorPaginas(contenedor) {

        const span = document.createElement("span");

        span.className = "pg-dots";
        span.textContent = "...";

        contenedor.appendChild(span);

    }


    /**
     * ==========================================
     * Obtiene las páginas visibles
     * ==========================================
     */
    _obtenerPaginasVisibles() {

        const paginas = [];

        const total = this.totalPages;
        const actual = this.page;

        if (total <= 7) {

            for (let i = 1; i <= total; i++) {
                paginas.push(i);
            }

            return paginas;

        }

        // Inicio

        if (actual <= 4) {

            paginas.push(1, 2, 3, 4, 5, "...", total);

            return paginas;

        }

        // Final

        if (actual >= total - 3) {

            paginas.push(
                1,
                "...",
                total - 4,
                total - 3,
                total - 2,
                total - 1,
                total
            );

            return paginas;

        }

        // Centro

        paginas.push(
            1,
            "...",
            actual - 1,
            actual,
            actual + 1,
            "...",
            total
        );

        return paginas;

    }


    inicializarEventos() {

        const btnAnterior = this.getElemento("btnAnterior");
        const btnSiguiente = this.getElemento("btnSiguiente");
        const pageSize = this.getElemento("pageSize");

        if (btnAnterior) {
            btnAnterior.addEventListener("click", () => {
                this.paginaAnterior();
            });
        }

        if (btnSiguiente) {
            btnSiguiente.addEventListener("click", () => {
                this.paginaSiguiente();
            });
        }

        if (pageSize) {
            pageSize.addEventListener("change", (e) => {
                this.cambiarPageSize(e.target.value);
            });
        }

    }


    /**
     * ==========================================
     * Inicializa el ordenamiento por columnas
     * ==========================================
     */
    inicializarOrdenamiento() {

        const tabla = this.getElemento("tabla");

        if (!tabla) return;

        const encabezados = tabla.querySelectorAll("th[data-sort]");

        encabezados.forEach(th => {

            th.style.cursor = "pointer";

            th.addEventListener("click", () => {

                const columna = th.dataset.sort;

                if (!columna) return;

                this.toggleOrden(columna);

            });

        });

    }


    /**
     * ==========================================
     * Actualiza los indicadores visuales
     * del ordenamiento
     * ==========================================
     */
    actualizarIndicadoresOrden() {

        const tabla = this.getElemento("tabla");

        if (!tabla) return;

        const encabezados = tabla.querySelectorAll("th[data-sort]");

        encabezados.forEach(th => {

            const columna = th.dataset.sort;

            const texto = th.textContent
                .replace(" ▲", "")
                .replace(" ▼", "")
                .trim();

            th.textContent = texto;

            if (columna !== this.sortBy) return;

            th.textContent +=
                this.sortOrder === "asc"
                    ? " ▲"
                    : " ▼";

        });

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
     * Alterna el orden de una columna
     * ==========================================
     */
    toggleOrden(columna) {

        let orden = "asc";

        if (this.sortBy === columna) {

            orden =
                this.sortOrder === "asc"
                    ? "desc"
                    : "asc";

        }

        this._actualizarEstado({

            sort_by: columna,

            sort_order: orden,

            page: 1

        });

    }

    /**
     * ==========================================
     * Actualiza el estado y notifica cambios
     * ==========================================
     */
    _actualizarEstado(nuevoEstado = {}) {

        this.estado = {

            ...this.estado,

            ...nuevoEstado

        };

        this._notificarCambio();

    }


    /**
     * ==========================================
     * Notifica cambios al consumidor
     * ==========================================
     */
    _notificarCambio() {

        if (typeof this.callback === "function") {

            this.callback();

        }

    }

    /**
     * ==========================================
     * Ir a una página específica
     * ==========================================
     */
    irAPagina(page) {

        this._actualizarEstado({
            page: Number(page)
        });

    }

    /**
     * ==========================================
     * Página siguiente
     * ==========================================
     */
    paginaSiguiente() {

        if (this.page >= this.totalPages) return;

        this._actualizarEstado({
            page: this.page + 1
        });

    }

    /**
     * ==========================================
     * Página anterior
     * ==========================================
     */
    paginaAnterior() {

        if (this.page <= 1) return;

        this._actualizarEstado({
            page: this.page - 1
        });

    }

    /**
     * ==========================================
     * Reinicia la paginación
     * ==========================================
     */
    reiniciarPaginacion() {

        this.estado.page = 1;

    }

    /**
     * ==========================================
     * Cambia el tamaño de página
     * ==========================================
     */
    cambiarPageSize(pageSize) {

        this._actualizarEstado({

            page_size: Number(pageSize),

            page: 1

        });

    }

    /**
     * ==========================================
     * Obtiene un elemento cacheado
     * ==========================================
     */
    getElemento(nombre) {

        if (this.elementos[nombre]) {

            return this.elementos[nombre];

        }

        console.warn(
            `[TablaUI] El elemento "${nombre}" no fue cacheado.`
        );

        return null;

    }


    /**
     * ==========================================
     * Cachea los elementos configurados
     * ==========================================
     */
    cachearElementos() {

        Object.entries(this.selectores).forEach(([nombre, selector]) => {

            if (!selector) {

                if (this.elementosRequeridos.includes(nombre)) {

                    console.error(
                        `[TablaUI] El selector obligatorio "${nombre}" no fue configurado.`
                    );

                }

                return;

            }

            const elemento = document.querySelector(selector);

            if (!elemento) {

                const mensaje = `[TablaUI] No se encontró el elemento: ${selector}`;

                if (this.elementosRequeridos.includes(nombre)) {

                    console.error(mensaje);

                } else {

                    console.warn(mensaje);

                }

                return;

            }

            this.elementos[nombre] = elemento;

        });

    }

    /**
     * ==========================================
     * Inicializa el componente
     * ==========================================
     */
    init() {

        this.cachearElementos();

        this.inicializarEventos();

        this.inicializarOrdenamiento();

        this.renderizar();

        return this;

    }

}

