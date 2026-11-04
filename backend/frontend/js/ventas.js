
import { apiFetch, API_URL } from "./api.js";
import { TablaUI } from "./tablas.js";

// =====================================================
// ESTADO DEL MODULO
// =====================================================

const STORAGE_PAGE_SIZE = "ventas_page_size";

let productos = [];
let modo = ""; // crear | consultar
let tablaVentasUI = null;
let timeoutBusquedaVentas = null;
let solicitudListado = 0;
let solicitudKpis = 0;


// =====================================================
// ESTADO DEL MODAL DE DETALLE DE VENTAS
// =====================================================

let ventasPorId = new Map();

let ventaActualModal = null;

let detalleVentaActual = [];



// =====================================================
// HELPERS GENERALES
// =====================================================

function getEl(id) {
    return document.getElementById(id);
}

function escaparHTML(valor) {
    return String(valor ?? "").replace(/[&<>"']/g, caracter => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[caracter]);
}

function formatoMoneda(valor) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0
    }).format(Number(valor) || 0);
}

function formatoNumero(valor) {
    return new Intl.NumberFormat("es-CO", {
        maximumFractionDigits: 0
    }).format(Number(valor) || 0);
}

function formatoCantidad(valor) {
    return new Intl.NumberFormat("es-CO", {
        maximumFractionDigits: 3
    }).format(Number(valor) || 0);
}

function formatearFechaISO(fecha) {

    const anio = fecha.getFullYear();

    const mes = String(
        fecha.getMonth() + 1
    ).padStart(2, "0");

    const dia = String(
        fecha.getDate()
    ).padStart(2, "0");

    return `${anio}-${mes}-${dia}`;

}

function formatearFecha(fechaValor) {

    if (!fechaValor) return "";

    const texto = String(fechaValor).trim();

    const fechaSolo = texto.match(
        /^(\d{4})-(\d{2})-(\d{2})$/
    );

    if (fechaSolo) {

        return `${fechaSolo[3]}/${fechaSolo[2]}/${fechaSolo[1]}`;

    }

    const fechaNormalizada = texto.includes("T")
        ? texto
        : texto.replace(" ", "T");

    const fecha = new Date(fechaNormalizada);

    if (Number.isNaN(fecha.getTime())) {
        return texto;
    }

    return new Intl.DateTimeFormat("es-CO", {

        timeZone: "America/Bogota",

        year: "numeric",

        month: "2-digit",

        day: "2-digit",

        hour: "2-digit",

        minute: "2-digit",

        hour12: false

    }).format(fecha);

}


// =====================================================
// INICIALIZACION
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {

    // Pantallas para crear ventas.

    if (getEl("productosVenta")) {

        modo = "crear";

        await cargarProductos();

    }

    // Historial de ventas.

    if (getEl("tablaVentas")) {

        modo = "consultar";

        inicializarTablaVentas();

        inicializarFiltrosVentas();

        inicializarExportacionVentas();

        inicializarModalVentas();

        await recargarHistorialVentas();

    }

});


// =====================================================
// CREACION DE VENTAS
// SE CONSERVA LA LOGICA EXISTENTE
// =====================================================

async function cargarProductos() {

    try {

        const categoria = document.body.dataset.categoria;

        const res = await apiFetch(
            "/productos?page=1&limit=100&inactivos=false"
        );

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible cargar los productos."
            );

        }

        productos = (res.data || []).filter(producto =>
            producto.tipo === "RECETA" &&
            (!categoria || producto.categoria === categoria)
        );

    } catch (error) {

        console.error(
            "Error cargando productos:",
            error
        );

        mostrarMensaje(
            "Error cargando productos.",
            "error"
        );

    }

}


// =====================================================
// AGREGAR PRODUCTO
// =====================================================

window.agregarProducto = function () {

    const container = getEl("productosVenta");

    const mensaje = getEl("mensajeVacio");

    if (!container) return;

    if (!productos.length) {

        mostrarMensaje(
            "No hay productos disponibles para esta venta.",
            "warning"
        );

        return;

    }

    if (mensaje) {
        mensaje.style.display = "none";
    }

    const row = document.createElement("div");

    row.className = "compra-item";

    row.innerHTML = `
        <select class="producto">

            ${productos.map(producto => `

                <option
                    value="${escaparHTML(producto.id)}"
                    data-precio="${Number(producto.precio_venta) || 0}"
                >
                    ${escaparHTML(producto.nombre)}
                </option>

            `).join("")}

        </select>

        <input
            type="number"
            class="cantidad"
            placeholder="0"
            min="0"
            step="0.001"
        >

        <input
            type="number"
            class="precio"
            readonly
        >

        <div class="subtotal">$0</div>

        <button
            type="button"
            class="btn-remove"
            aria-label="Quitar producto"
        >
            ✖
        </button>
    `;

    const select = row.querySelector(".producto");

    const precioInput = row.querySelector(".precio");

    const cantidadInput = row.querySelector(".cantidad");

    const actualizar = () => {

        const option = select.options[select.selectedIndex];

        const precio = Number(
            option?.dataset?.precio || 0
        );

        const cantidad = Number(
            cantidadInput.value
        ) || 0;

        precioInput.value = precio;

        row.querySelector(".subtotal").textContent =
            formatoMoneda(precio * cantidad);

        calcularTotal();

    };

    select.addEventListener(
        "change",
        actualizar
    );

    cantidadInput.addEventListener(
        "input",
        actualizar
    );

    row.querySelector(".btn-remove").addEventListener(
        "click",
        () => {

            row.remove();

            calcularTotal();

            if (
                container.children.length === 0 &&
                mensaje
            ) {

                mensaje.style.display = "block";

            }

        }
    );

    actualizar();

    container.appendChild(row);

};


// =====================================================
// CALCULAR TOTAL DE VENTA
// =====================================================

function calcularTotal() {

    let total = 0;

    document
        .querySelectorAll("#productosVenta .compra-item")
        .forEach(row => {

            const cantidad = Number(
                row.querySelector(".cantidad")?.value
            ) || 0;

            const precio = Number(
                row.querySelector(".precio")?.value
            ) || 0;

            total += cantidad * precio;

        });

    const totalEl = getEl("totalVenta");

    if (totalEl) {
        totalEl.textContent = formatoMoneda(total);
    }

}


// =====================================================
// GUARDAR VENTA
// =====================================================

window.guardarVenta = async function () {

    const filas = document.querySelectorAll(
        "#productosVenta .compra-item"
    );

    if (!filas.length) {

        mostrarMensaje(
            "Agrega productos.",
            "warning"
        );

        return;

    }

    const detalles = [];

    for (const fila of filas) {

        const cantidad = Number(
            fila.querySelector(".cantidad")?.value
        );

        const precio = Number(
            fila.querySelector(".precio")?.value
        );

        const productoId = fila.querySelector(".producto")?.value;

        if (
            !productoId ||
            !Number.isFinite(cantidad) ||
            cantidad <= 0 ||
            !Number.isFinite(precio) ||
            precio <= 0
        ) {

            mostrarMensaje(
                "Verifica el producto, la cantidad y el precio.",
                "warning"
            );

            return;

        }

        detalles.push({

            producto_id: productoId,

            cantidad,

            precio

        });

    }

    try {

        const res = await apiFetch(
            "/ventas",
            "POST",
            {

                cliente: getEl("cliente")?.value || "General",

                metodo_pago: getEl("metodo_pago")?.value || "Efectivo",

                usuario: "admin",

                detalles

            }
        );

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible registrar la venta."
            );

        }

        mostrarMensaje(
            res.data?.message || "Venta registrada correctamente.",
            "success"
        );

        const contenedor = getEl("productosVenta");

        if (contenedor) {
            contenedor.innerHTML = "";
        }

        const total = getEl("totalVenta");

        if (total) {
            total.textContent = formatoMoneda(0);
        }

        const mensaje = getEl("mensajeVacio");

        if (mensaje) {
            mensaje.style.display = "block";
        }

    } catch (error) {

        console.error(
            "Error registrando venta:",
            error
        );

        mostrarMensaje(
            error.message || "Error registrando la venta.",
            "error"
        );

    }

};


// =====================================================
// TABLA Y PAGINACION DEL HISTORIAL
// =====================================================

function inicializarTablaVentas() {

    tablaVentasUI = new TablaUI({

        nombre: "ventas",

        callback: () => cargarVentas(),

        tabla: "#tablaVentasTabla",

        pageSize: "#pageSizeVentas",

        btnAnterior: "#btnPaginaAnteriorVentas",

        btnSiguiente: "#btnPaginaSiguienteVentas",

        numeros: "#numerosPaginacionVentas",

        resumen: "#resumenPaginacionVentas",

        info: "#infoPaginacionVentas"

    }).init();


    const tamanosPermitidos = [10, 20, 50, 100];

    const guardado = Number(
        localStorage.getItem(STORAGE_PAGE_SIZE)
    );

    const pageSizeInicial = tamanosPermitidos.includes(guardado)
        ? guardado
        : 20;

    tablaVentasUI.actualizarDesdeBackend({

        page: 1,

        page_size: pageSizeInicial,

        total: 0,

        total_pages: 1,

        sort_by: "id",

        sort_order: "desc"

    });


    getEl("pageSizeVentas")?.addEventListener(
        "change",
        event => {

            localStorage.setItem(
                STORAGE_PAGE_SIZE,
                event.target.value
            );

        }
    );

}


// =====================================================
// FILTROS Y PERIODOS
// =====================================================

function inicializarFiltrosVentas() {

    getEl("filtroPeriodoVentas")?.addEventListener(
        "change",
        actualizarPeriodoVentas
    );

    getEl("fechaInicioVentas")?.addEventListener(
        "change",
        actualizarConsultaVentas
    );

    getEl("fechaFinVentas")?.addEventListener(
        "change",
        actualizarConsultaVentas
    );


    getEl("filtroMetodoPago")?.addEventListener(
        "change",
        actualizarConsultaVentas
    );


    getEl("buscarVenta")?.addEventListener(
        "input",
        () => {

            clearTimeout(timeoutBusquedaVentas);

            timeoutBusquedaVentas = setTimeout(
                actualizarConsultaVentas,
                350
            );

        }
    );

    getEl("btnLimpiarFiltrosVentas")?.addEventListener(
        "click",
        limpiarFiltrosVentas
    );

    configurarFechasPersonalizadas(false);

    calcularFechasPeriodo("mes_actual");

}


// =====================================================
// FUNCIONES DE CALENDARIO
// =====================================================

function obtenerPrimerDiaMes(fecha) {

    return new Date(
        fecha.getFullYear(),
        fecha.getMonth(),
        1
    );

}


function obtenerUltimoDiaMes(fecha) {

    return new Date(
        fecha.getFullYear(),
        fecha.getMonth() + 1,
        0
    );

}


function obtenerPrimerDiaSemana(fecha) {

    const copia = new Date(fecha);

    const dia = copia.getDay();

    const diferencia = dia === 0
        ? -6
        : 1 - dia;

    copia.setDate(
        copia.getDate() + diferencia
    );

    copia.setHours(0, 0, 0, 0);

    return copia;

}


function obtenerUltimoDiaSemana(fecha) {

    const ultimo = obtenerPrimerDiaSemana(fecha);

    ultimo.setDate(
        ultimo.getDate() + 6
    );

    return ultimo;

}


// =====================================================
// FECHAS PERSONALIZADAS
// =====================================================

function configurarFechasPersonalizadas(limpiar = true) {

    const periodo = getEl("filtroPeriodoVentas");

    const fechaInicio = getEl("fechaInicioVentas");

    const fechaFin = getEl("fechaFinVentas");

    const contenedor = getEl("customDateFiltersVentas");

    if (
        !periodo ||
        !fechaInicio ||
        !fechaFin ||
        !contenedor
    ) {
        return false;
    }

    const personalizado = periodo.value === "personalizado";

    contenedor.classList.toggle(
        "hidden",
        !personalizado
    );

    fechaInicio.disabled = !personalizado;

    fechaFin.disabled = !personalizado;

    if (personalizado && limpiar) {

        fechaInicio.value = "";

        fechaFin.value = "";

    }

    return personalizado;

}


// =====================================================
// CALCULAR RANGO SEGUN PERIODO
// =====================================================

function calcularFechasPeriodo(periodo) {

    const hoy = new Date();

    hoy.setHours(0, 0, 0, 0);

    let inicio;

    let fin;

    switch (periodo) {

        case "hoy":

            inicio = new Date(hoy);

            fin = new Date(hoy);

            break;


        case "ayer":

            inicio = new Date(hoy);

            inicio.setDate(
                inicio.getDate() - 1
            );

            fin = new Date(inicio);

            break;


        case "esta_semana":

            inicio = obtenerPrimerDiaSemana(hoy);

            fin = obtenerUltimoDiaSemana(hoy);

            break;


        case "semana_pasada": {

            const lunesSemanaAnterior =
                obtenerPrimerDiaSemana(hoy);

            lunesSemanaAnterior.setDate(
                lunesSemanaAnterior.getDate() - 7
            );

            inicio = lunesSemanaAnterior;

            fin = obtenerUltimoDiaSemana(
                lunesSemanaAnterior
            );

            break;

        }


        case "mes_actual":

            inicio = obtenerPrimerDiaMes(hoy);

            fin = obtenerUltimoDiaMes(hoy);

            break;


        case "mes_anterior": {

            const mesAnterior = new Date(
                hoy.getFullYear(),
                hoy.getMonth() - 1,
                1
            );

            inicio = obtenerPrimerDiaMes(mesAnterior);

            fin = obtenerUltimoDiaMes(mesAnterior);

            break;

        }


        case "ultimos30":

            fin = new Date(hoy);

            inicio = new Date(hoy);

            inicio.setDate(
                inicio.getDate() - 29
            );

            break;


        default:

            return;

    }

    getEl("fechaInicioVentas").value =
        formatearFechaISO(inicio);

    getEl("fechaFinVentas").value =
        formatearFechaISO(fin);

}


// =====================================================
// CAMBIO DE PERIODO
// =====================================================

function actualizarPeriodoVentas() {

    const personalizado =
        configurarFechasPersonalizadas(true);

    if (personalizado) {

        mostrarMensaje(
            "Selecciona una fecha inicial o final para consultar el período personalizado.",
            "info"
        );

        return;

    }

    calcularFechasPeriodo(
        getEl("filtroPeriodoVentas")?.value || "mes_actual"
    );

    actualizarConsultaVentas();

}


// =====================================================
// OBTENER FILTROS
// =====================================================

function obtenerFiltrosVentas() {

    return {

        buscar: getEl("buscarVenta")?.value.trim() || "",

        metodo_pago: getEl("filtroMetodoPago")?.value.trim() || "",

        fecha_inicio: getEl("fechaInicioVentas")?.value || "",

        fecha_fin: getEl("fechaFinVentas")?.value || ""

    };

}


// =====================================================
// VALIDAR FECHAS
// =====================================================

function validarFechasVentas(mostrarAviso = true) {

    const {
        fecha_inicio,
        fecha_fin
    } = obtenerFiltrosVentas();

    if (
        getEl("filtroPeriodoVentas")?.value === "personalizado" &&
        !fecha_inicio &&
        !fecha_fin
    ) {

        if (mostrarAviso) {

            mostrarMensaje(
                "Selecciona al menos una fecha para aplicar el período personalizado.",
                "warning"
            );

        }

        return false;

    }

    if (
        fecha_inicio &&
        fecha_fin &&
        fecha_fin < fecha_inicio
    ) {

        if (mostrarAviso) {

            mostrarMensaje(
                "La fecha final no puede ser anterior a la fecha inicial.",
                "warning"
            );

        }

        return false;

    }

    return true;

}


// =====================================================
// ACTUALIZAR CONSULTA
// =====================================================

function actualizarConsultaVentas() {

    if (!validarFechasVentas()) {
        return;
    }

    tablaVentasUI?.reiniciarPaginacion();

    recargarHistorialVentas();

}


// =====================================================
// LIMPIAR FILTROS
// =====================================================

function limpiarFiltrosVentas() {

    if (getEl("filtroPeriodoVentas")) {
        getEl("filtroPeriodoVentas").value = "mes_actual";
    }

    if (getEl("filtroMetodoPago")) {
        getEl("filtroMetodoPago").value = "";
    }

    if (getEl("buscarVenta")) {
        getEl("buscarVenta").value = "";
    }

    configurarFechasPersonalizadas(false);

    calcularFechasPeriodo("mes_actual");

    actualizarConsultaVentas();

}


// =====================================================
// RECARGA COORDINADA
// TABLA + INDICADORES
// =====================================================

async function recargarHistorialVentas() {

    if (!validarFechasVentas(false)) {
        return;
    }

    await Promise.all([

        cargarVentas(),

        cargarKpisVentas()

    ]);

}


// =====================================================
// CONSTRUIR PARAMETROS
// =====================================================

function crearParametrosVentas(incluirPaginacion = false) {

    const filtros = obtenerFiltrosVentas();

    const params = new URLSearchParams();

    if (filtros.buscar) {

        params.set(
            "buscar",
            filtros.buscar
        );

    }

    if (filtros.metodo_pago) {

        params.set(
            "metodo_pago",
            filtros.metodo_pago
        );

    }

    if (filtros.fecha_inicio) {

        params.set(
            "fecha_inicio",
            filtros.fecha_inicio
        );

    }

    if (filtros.fecha_fin) {

        params.set(
            "fecha_fin",
            filtros.fecha_fin
        );

    }

    if (incluirPaginacion && tablaVentasUI) {

        const estado = tablaVentasUI.getEstado();

        params.set("page", String(estado.page));

        params.set("page_size", String(estado.page_size));

        params.set("sort_by", estado.sort_by);

        params.set("sort_order", estado.sort_order);

    }

    return params;

}


// =====================================================
// CARGAR HISTORIAL PAGINADO
// =====================================================


async function cargarVentas() {

    if (!tablaVentasUI || !validarFechasVentas(false)) {
        return;
    }

    const idSolicitud = ++solicitudListado;

    const params = crearParametrosVentas(true);

    const tbody = getEl("tablaVentas");

    if (tbody) {

        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align:center;">
                    Cargando ventas...
                </td>
            </tr>
        `;

    }

    try {

        const res = await apiFetch(
            `/ventas?${params.toString()}`
        );

        // Evitar que una consulta anterior
        // sobrescriba una consulta más reciente.

        if (idSolicitud !== solicitudListado) {
            return;
        }

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible consultar las ventas."
            );

        }

        // =============================================
        // EXTRAER RESPUESTA DEL BACKEND
        // =============================================

        const resultado = res.data || {};

        if (!Array.isArray(resultado.items)) {

            throw new Error(
                "La respuesta del historial no contiene una lista válida de ventas."
            );

        }

        const ventas = resultado.items;

        const paginacion = resultado.pagination || {};

        // =============================================
        // GUARDAR CABECERAS PARA EL MODAL
        // =============================================

        ventasPorId = new Map(
            ventas.map(venta => [
                Number(venta.id),
                venta
            ])
        );

        // =============================================
        // RENDERIZAR TABLA
        // =============================================

        if (tbody) {

            if (!ventas.length) {

                tbody.innerHTML = `
                    <tr>
                        <td colspan="7" style="text-align:center;">
                            No se encontraron ventas para los filtros seleccionados.
                        </td>
                    </tr>
                `;

            } else {

                tbody.innerHTML = ventas
                    .map(crearFilaVenta)
                    .join("");

            }

        }

        // =============================================
        // ACTUALIZAR PAGINACION
        // =============================================

        tablaVentasUI.actualizarDesdeBackend({

            page: paginacion.page ?? 1,

            page_size: paginacion.page_size ?? tablaVentasUI.pageSize,

            total: paginacion.total ?? 0,

            total_pages: paginacion.total_pages ?? 1,

            sort_by: tablaVentasUI.sortBy,

            sort_order: tablaVentasUI.sortOrder

        });

    } catch (error) {

        if (idSolicitud !== solicitudListado) {
            return;
        }

        console.error(
            "Error cargando historial de ventas:",
            error
        );

        ventasPorId.clear();

        if (tbody) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="7" style="text-align:center;">
                        No fue posible cargar el historial de ventas.
                    </td>
                </tr>
            `;

        }

        mostrarMensaje(
            error.message || "Error cargando ventas.",
            "error"
        );

    }

}


// =====================================================
// CREAR FILA DE VENTA
// =====================================================

function crearFilaVenta(venta) {

    const id = Number(venta.id) || 0;

    const cliente = escaparHTML(
        venta.cliente || "Consumidor final"
    );

    const fecha = escaparHTML(
        formatearFecha(venta.fecha)
    );

    const metodoPago = escaparHTML(
        venta.metodo_pago || "No especificado"
    );

    const total = formatoMoneda(
        venta.total
    );

    const usuario = escaparHTML(
        venta.usuario || "Usuario no disponible"
    );

    return `
        <tr>

            <td data-label="Venta">
                ${id}
            </td>

            <td data-label="Cliente">
                ${cliente}
            </td>

            <td data-label="Fecha">
                ${fecha}
            </td>

            <td data-label="Método de pago">
                ${metodoPago}
            </td>

            <td data-label="Total">
                ${total}
            </td>

            <td data-label="Usuario">
                ${usuario}
            </td>

            <td data-label="Acción" style="text-align:center;">

                <button
                    type="button"
                    class="btn-table btn-ver-detalle-venta"
                    data-venta-id="${id}"
                    aria-label="Ver detalle de la venta ${id}"
                    title="Ver detalle"
                >
                    👁
                </button>

            </td>

        </tr>
    `;

}


// =====================================================
// KPIS DE VENTAS
// =====================================================

async function cargarKpisVentas() {

    const idSolicitud = ++solicitudKpis;

    const params = crearParametrosVentas(false);

    try {

        const query = params.toString();

        const endpoint = query
            ? `/ventas/kpis?${query}`
            : "/ventas/kpis";

        const res = await apiFetch(endpoint);

        if (idSolicitud !== solicitudKpis) {
            return;
        }

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible consultar los indicadores."
            );

        }

        actualizarKpisVentas(
            res.data || {}
        );

    } catch (error) {

        if (idSolicitud !== solicitudKpis) {
            return;
        }

        console.error(
            "Error consultando KPIs de ventas:",
            error
        );

        actualizarKpisVentas({});

        mostrarMensaje(
            error.message || "No fue posible actualizar los indicadores.",
            "error"
        );

    }

}


// =====================================================
// ACTUALIZAR INDICADORES VISUALES
// =====================================================

function actualizarKpisVentas(kpis) {

    const totalVentas = Number(
        kpis.total_ventas
    ) || 0;

    const totalVendido = Number(
        kpis.total_vendido
    ) || 0;

    const clientes = Number(
        kpis.clientes_identificados
    ) || 0;

    const ticketPromedio = Number(
        kpis.ticket_promedio
    ) || 0;


    if (getEl("kpiTotalVentas")) {

        getEl("kpiTotalVentas").textContent =
            formatoNumero(totalVentas);

    }

    if (getEl("kpiTotalVendido")) {

        getEl("kpiTotalVendido").textContent =
            formatoMoneda(totalVendido);

    }

    if (getEl("kpiClientesIdentificados")) {

        getEl("kpiClientesIdentificados").textContent =
            formatoNumero(clientes);

    }

    if (getEl("kpiTicketPromedio")) {

        getEl("kpiTicketPromedio").textContent =
            formatoMoneda(ticketPromedio);

    }

}


// =====================================================
// INICIALIZAR EXPORTACION
// =====================================================

function inicializarExportacionVentas() {

    getEl("btnExportarExcel")?.addEventListener(
        "click",
        exportarVentasExcel
    );

}


// =====================================================
// NOMBRE DEL ARCHIVO
// =====================================================

function obtenerNombreArchivo(response) {

    const disposition = response.headers.get(
        "Content-Disposition"
    ) || "";

    const utf8 = disposition.match(
        /filename\*=UTF-8''([^;]+)/i
    );

    const normal = disposition.match(
        /filename="?([^";]+)"?/i
    );

    const nombre = utf8?.[1] || normal?.[1];

    if (!nombre) {

        return `Reporte_Ventas_${formatearFechaISO(new Date())}.xlsx`;

    }

    try {

        return decodeURIComponent(
            nombre.replace(/"/g, "").trim()
        );

    } catch (_) {

        return nombre.replace(/"/g, "").trim();

    }

}


// =====================================================
// LEER MENSAJE DE ERROR DE EXPORTACION
// =====================================================

async function obtenerMensajeError(response) {

    const texto = await response.text();

    if (!texto) {

        return `Error ${response.status} al exportar ventas.`;

    }

    try {

        const json = JSON.parse(texto);

        return json.message ||
            `Error ${response.status} al exportar ventas.`;

    } catch (_) {

        return texto;

    }

}


// =====================================================
// EXPORTAR VENTAS A EXCEL
// =====================================================

async function exportarVentasExcel() {

    if (!validarFechasVentas()) {
        return;
    }

    const boton = getEl("btnExportarExcel");

    const textoOriginal = boton?.textContent ||
        "📄 Exportar Excel";

    if (boton) {

        boton.disabled = true;

        boton.textContent = "Generando Excel...";

    }

    try {

        const params = crearParametrosVentas(false);

        const query = params.toString();

        const url = query
            ? `${API_URL}/ventas/exportar?${query}`
            : `${API_URL}/ventas/exportar`;


        // Solicitud binaria autenticada.

        const response = await fetch(url, {

            method: "GET",

            credentials: "include",

            headers: {

                Accept:
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

            }

        });


        // Sesión expirada.

        if (response.status === 401) {

            localStorage.removeItem("usuario");

            window.location.href = "/pages/login.html";

            return;

        }


        if (!response.ok) {

            throw new Error(
                await obtenerMensajeError(response)
            );

        }


        const contentType = response.headers.get(
            "Content-Type"
        ) || "";

        if (
            contentType.includes("application/json") ||
            contentType.includes("text/html")
        ) {

            throw new Error(
                await obtenerMensajeError(response)
            );

        }


        const blob = await response.blob();

        if (!blob.size) {

            throw new Error(
                "El archivo recibido está vacío."
            );

        }


        // Descargar archivo.

        const objectUrl = URL.createObjectURL(blob);

        const enlace = document.createElement("a");

        enlace.href = objectUrl;

        enlace.download = obtenerNombreArchivo(response);

        enlace.style.display = "none";

        document.body.appendChild(enlace);

        enlace.click();

        enlace.remove();


        // Liberar memoria.

        window.setTimeout(() => {

            URL.revokeObjectURL(objectUrl);

        }, 1500);


        mostrarMensaje(
            "Reporte de ventas descargado correctamente.",
            "success"
        );

    } catch (error) {

        console.error(
            "Error exportando ventas:",
            error
        );

        mostrarMensaje(
            error.message || "No fue posible exportar las ventas.",
            "error"
        );

    } finally {

        if (boton) {

            boton.disabled = false;

            boton.textContent = textoOriginal;

        }

    }

}



// =====================================================
// MODAL DETALLE DE VENTA
// MISMA ESTRUCTURA VISUAL DEL MODAL DE PEDIDOS
// =====================================================


// =====================================================
// NORMALIZAR CLAVES DE MENUS Y CATEGORIAS
// =====================================================

function normalizarClaveVenta(valor) {

    return String(valor || "")

        .normalize("NFD")

        .replace(/[\u0300-\u036f]/g, "")

        .trim()

        .toUpperCase()

        .replace(/[\s-]+/g, "_");

}


// =====================================================
// NOMBRES DE LOS MENUS Y TIPOS DE ARTICULO
// =====================================================

function obtenerNombreTipoItemVenta(tipo) {

    const clave = normalizarClaveVenta(tipo);

    const nombres = {

        PRODUCTO: "Producto",

        RECETA: "Receta",

        ALMUERZO: "Almuerzo",

        MENU_EJECUTIVO: "Menú ejecutivo",

        MENU_PREMIUM: "Menú premium",

        MENU_ESPECIAL: "Menú especial",

        ADICION: "Adición",

        DESAYUNO: "Desayuno",

        COMIDA_RAPIDA: "Comida rápida",

        LICOR: "Licor",

        LICORES: "Licores",

        BEBIDA: "Bebida",

        BEBIDAS: "Bebidas"

    };

    if (nombres[clave]) {
        return nombres[clave];
    }

    const texto = String(tipo || "PRODUCTO")
        .replace(/_/g, " ")
        .toLowerCase();

    return texto.charAt(0).toUpperCase() + texto.slice(1);

}


// =====================================================
// NOMBRES DE CATEGORIAS DEL NEGOCIO
// =====================================================

function obtenerNombreCategoriaVenta(categoria) {

    const clave = normalizarClaveVenta(categoria);

    const categorias = {

        DESAYUNO: "Desayunos",

        DESAYUNOS: "Desayunos",

        ALMUERZO: "Almuerzos",

        ALMUERZOS: "Almuerzos",

        COMIDA_RAPIDA: "Comidas rápidas",

        COMIDAS_RAPIDAS: "Comidas rápidas",

        LICORES: "Licores / Bebidas",

        BEBIDAS: "Licores / Bebidas",

        LICORES_BEBIDAS: "Licores / Bebidas",

        MENU_EJECUTIVO: "Menú ejecutivo",

        MENU_PREMIUM: "Menú premium",

        MENU_ESPECIAL: "Menú especial"

    };

    if (categorias[clave]) {
        return categorias[clave];
    }

    if (!categoria) {
        return "No especificada";
    }

    return String(categoria)
        .replace(/_/g, " ")
        .toLowerCase()
        .replace(/\b\p{L}/gu, letra => letra.toUpperCase());

}


// =====================================================
// ACTUALIZAR TEXTO DEL MODAL DE VENTAS
// =====================================================

function establecerTextoModal(id, valor, defecto = "-") {

    const elemento = document.getElementById(id);

    if (!elemento) {
        return;
    }

    const texto = (
        valor !== null &&
        valor !== undefined
    )
        ? String(valor).trim()
        : "";

    elemento.textContent = texto || defecto;

}


// =====================================================
// ACTUALIZAR TEXTO DEL MODAL
// =====================================================

function establecerTextoModalVenta(id, valor, defecto = "-") {

    const elemento = getEl(id);

    if (!elemento) return;

    const texto = String(valor ?? "").trim();

    elemento.textContent = texto || defecto;

}


// =====================================================
// ABRIR MODAL Y CONSULTAR DETALLE
// =====================================================

window.verDetalleVenta = async function (id) {

    const modal = getEl("modalCompra");

    const contenedor = getEl("detalleItemsVenta");

    const botonImprimir = getEl("btnImprimirVenta");

    if (!modal || !contenedor) return;

    const ventaId = Number(id);

    if (!Number.isInteger(ventaId) || ventaId <= 0) {

        mostrarMensaje(
            "El identificador de la venta no es válido.",
            "warning"
        );

        return;

    }


    // =============================================
    // OBTENER CABECERA DESDE EL HISTORIAL
    // =============================================

    ventaActualModal = ventasPorId.get(ventaId) || null;

    detalleVentaActual = [];


    // =============================================
    // MOSTRAR INFORMACION GENERAL
    // =============================================

    establecerTextoModal(
        "tituloDetalleVenta",
        `Detalle de la Venta #${ventaId}`
    );

    establecerTextoModal(
        "detalleVentaNumero",
        `#${ventaId}`
    );

    establecerTextoModal(
        "detalleVentaMetodoPago",
        ventaActualModal?.metodo_pago,
        "No especificado"
    );

    establecerTextoModal(
        "detalleVentaFecha",
        formatearFecha(
            ventaActualModal?.fecha
        )
    );

    establecerTextoModal(
        "detalleVentaCliente",
        ventaActualModal?.cliente,
        "Consumidor final"
    );

    establecerTextoModal(
        "detalleVentaCategoria",
        obtenerNombreCategoriaVenta(
            ventaActualModal?.categoria
        )
    );

    establecerTextoModal(
        "detalleVentaMesa",
        ventaActualModal?.mesa,
        "No aplica"
    );

    establecerTextoModal(
        "detalleVentaUsuario",
        ventaActualModal?.usuario,
        "No disponible"
    );


    // =============================================
    // ESTADO INICIAL
    // =============================================

    contenedor.innerHTML = `

        <div class="pedido-productos-vacio">

            <div class="pedido-productos-vacio-icon">
                ⏳
            </div>

            <strong>
                Consultando productos de la venta
            </strong>

            <span>
                Cargando información del detalle...
            </span>

        </div>

    `;

    establecerTextoModal(
        "detalleTotalVenta",
        formatoMoneda(
            ventaActualModal?.total || 0
        )
    );

    if (botonImprimir) {
        botonImprimir.disabled = true;
    }

    modal.classList.remove("hidden");


    // =============================================
    // CONSULTAR DETALLE EN BACKEND
    // =============================================

    try {

        const res = await apiFetch(
            `/ventas/${ventaId}`
        );

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message ||
                "No fue posible consultar el detalle de la venta."
            );

        }

        const detalles = Array.isArray(res.data)
            ? res.data
            : [];

        detalleVentaActual = detalles;


        // =============================================
        // RENDERIZAR TARJETAS
        // =============================================

        const totalDetalle = renderDetalleVenta(
            detalles
        );


        // =============================================
        // TOTAL GENERAL
        // Se toma el total guardado en la venta.
        // Si no está disponible, se usa la suma
        // del detalle.
        // =============================================

        const totalVenta = ventaActualModal?.total;

        const totalFinal = (
            totalVenta !== null &&
            totalVenta !== undefined &&
            totalVenta !== ""
        )
            ? Number(totalVenta)
            : totalDetalle;

        establecerTextoModal(
            "detalleTotalVenta",
            formatoMoneda(totalFinal)
        );


        // =============================================
        // HABILITAR IMPRESION
        // =============================================

        if (botonImprimir) {

            botonImprimir.disabled = (
                detalles.length === 0
            );

        }

    } catch (error) {

        console.error(
            "ERROR DETALLE VENTA:",
            error
        );

        contenedor.innerHTML = `

            <div class="pedido-productos-vacio">

                <div class="pedido-productos-vacio-icon">
                    ⚠️
                </div>

                <strong>
                    No fue posible cargar el detalle
                </strong>

                <span>
                    ${escaparHTML(
            error.message ||
            "Error consultando los productos de la venta."
        )}
                </span>

            </div>

        `;

        if (botonImprimir) {
            botonImprimir.disabled = true;
        }

        mostrarMensaje(
            error.message || "Error consultando la venta.",
            "error"
        );

    }

};


// =====================================================
// RENDERIZAR PRODUCTOS DE LA VENTA
// MISMO DISEÑO DE TARJETAS DE PEDIDOS
// =====================================================

function renderDetalleVenta(detalles) {

    const contenedor = getEl("detalleItemsVenta");

    if (!contenedor) return 0;

    contenedor.innerHTML = "";


    // =============================================
    // VALIDAR DETALLES
    // =============================================

    if (!Array.isArray(detalles) || detalles.length === 0) {

        contenedor.innerHTML = `

            <div class="pedido-productos-vacio">

                <div class="pedido-productos-vacio-icon">
                    🍽️
                </div>

                <strong>
                    No existen productos en esta venta
                </strong>

                <span>
                    Esta venta no tiene productos registrados.
                </span>

            </div>

        `;

        return 0;

    }


    let total = 0;


    // =============================================
    // CONSTRUIR TARJETAS
    // =============================================

    detalles.forEach((item, index) => {

        const cantidad = Number(
            item.cantidad || 0
        );

        const precio = Number(
            item.precio || 0
        );

        const subtotal = Number(
            item.subtotal ??
            (cantidad * precio)
        );

        total += subtotal;


        const tipo = obtenerNombreTipoItemVenta(
            item.tipo_item || item.tipo
        );

        const nombre = (
            item.nombre_item ||
            item.nombre ||
            tipo
        ).toString();


        // =============================================
        // COMPONENTES (SI EL BACKEND LOS PROPORCIONA)
        // =============================================

        let componentesHTML = "";

        if (
            Array.isArray(item.componentes) &&
            item.componentes.length > 0
        ) {

            componentesHTML = `

                <div class="detalle-componentes">

                    <div class="detalle-componentes-header">

                        <span class="detalle-componentes-icon">
                            🧩
                        </span>

                        <div>

                            <strong>
                                Composición
                            </strong>

                            <small>
                                Componentes del menú o receta
                            </small>

                        </div>

                    </div>

                    <div class="detalle-componentes-list">

                        ${item.componentes.map(componente => `

                            <div class="detalle-componente">

                                <span class="detalle-componente-categoria">
                                    ${escaparHTML(
                componente.categoria || "COMPONENTE"
            )}
                                </span>

                                <strong>
                                    ${escaparHTML(
                componente.nombre || "-"
            )}
                                </strong>

                            </div>

                        `).join("")}

                    </div>

                </div>

            `;

        }


        // =============================================
        // TARJETA DEL PRODUCTO
        // =============================================

        const card = document.createElement("article");

        card.className = "detalle-item-card";

        card.innerHTML = `

            <div class="detalle-item-accent"></div>

            <div class="detalle-item-main">


                <!-- CABECERA DEL PRODUCTO -->

                <div class="detalle-item-header">

                    <div class="detalle-item-identidad">

                        <div class="detalle-item-index">

                            ${index + 1}

                        </div>

                        <div class="detalle-item-title">

                            <div class="detalle-item-name-row">

                                <strong>
                                    ${escaparHTML(nombre)}
                                </strong>

                                <span class="badge-detalle">
                                    ${escaparHTML(tipo)}
                                </span>

                            </div>

                            <span class="detalle-item-description">
                                Artículo incluido en la venta
                            </span>

                        </div>

                    </div>


                    <div class="detalle-item-subtotal">

                        <span>
                            Total
                        </span>

                        <strong>
                            ${formatoMoneda(subtotal)}
                        </strong>

                    </div>

                </div>


                <!-- INFORMACION DEL PRODUCTO -->

                <div class="detalle-item-data">

                    <div class="detalle-item-data-box">

                        <span>
                            📦 Cantidad
                        </span>

                        <strong>
                            ${formatoCantidad(cantidad)}
                        </strong>

                    </div>


                    <div class="detalle-item-data-box">

                        <span>
                            💵 Precio unitario
                        </span>

                        <strong>
                            ${formatoMoneda(precio)}
                        </strong>

                    </div>


                    <div class="detalle-item-data-box detalle-item-data-total">

                        <span>
                            💰 Subtotal
                        </span>

                        <strong>
                            ${formatoMoneda(subtotal)}
                        </strong>

                    </div>

                </div>


                <!-- COMPONENTES -->

                ${componentesHTML}

            </div>

        `;

        contenedor.appendChild(card);

    });


    return total;

}



// =====================================================
// IMPRIMIR COMPROBANTE DE VENTA
// IMPRESORA TERMICA 80 MM
// =====================================================

function imprimirComprobanteVenta() {

    if (!ventaActualModal || !detalleVentaActual.length) {

        mostrarMensaje(
            "No hay información disponible para imprimir.",
            "warning"
        );

        return;

    }

    // =============================================
    // DATOS DE LA VENTA
    // =============================================

    const venta = ventaActualModal;

    const numero = venta.id;

    const fecha = formatearFecha(
        venta.fecha
    );

    const cliente = escaparHTML(
        venta.cliente || "Consumidor final"
    );

    const metodoPago = escaparHTML(
        venta.metodo_pago || "No especificado"
    );

    const categoria = escaparHTML(
        obtenerNombreCategoriaVenta(
            venta.categoria
        )
    );

    const usuario = escaparHTML(
        venta.usuario || "No disponible"
    );

    const servicio = String(
        venta.tipo_servicio || ""
    )
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .trim()
        .toUpperCase();

    const direccionEntrega = String(
        venta.direccion_entrega || ""
    ).trim();

    const esDomicilio = (
        servicio === "DOMICILIO" ||
        Boolean(direccionEntrega)
    );

    const mesa = String(
        venta.mesa || ""
    ).trim();


    // =============================================
    // DETALLE DE PRODUCTOS
    // =============================================

    let productosHTML = "";

    let totalCalculado = 0;

    detalleVentaActual.forEach((item, index) => {

        const nombre = escaparHTML(
            item.nombre_item ||
            item.nombre ||
            obtenerNombreTipoItemVenta(
                item.tipo_item
            )
        );

        const tipo = escaparHTML(
            obtenerNombreTipoItemVenta(
                item.tipo_item
            )
        );

        const cantidad = Number(
            item.cantidad || 0
        );

        const precio = Number(
            item.precio || 0
        );

        const subtotal = Number(
            item.subtotal ??
            cantidad * precio
        );

        totalCalculado += subtotal;

        productosHTML += `

            <div class="producto">

                <div class="producto-header">

                    <span class="producto-cantidad">
                        x${formatoCantidad(cantidad)}
                    </span>

                    <span class="producto-nombre">
                        ${nombre}
                    </span>

                </div>

                <div class="producto-tipo">
                    ${tipo}
                </div>

                <div class="producto-valores">

                    <span>
                        ${formatoMoneda(precio)} c/u
                    </span>

                    <strong>
                        ${formatoMoneda(subtotal)}
                    </strong>

                </div>

            </div>

            ${index < detalleVentaActual.length - 1
                ? '<div class="linea"></div>'
                : ''
            }

        `;

    });


    // =============================================
    // TOTAL
    // =============================================

    const total = (
        venta.total !== null &&
        venta.total !== undefined &&
        venta.total !== ""
    )
        ? Number(venta.total)
        : totalCalculado;


    // =============================================
    // INFORMACION DE SERVICIO
    // =============================================

    const servicioHTML = servicio
        ? `
            <div class="info">
                <strong>SERVICIO:</strong>
                ${escaparHTML(servicio)}
            </div>
        `
        : "";

    const direccionHTML = esDomicilio
        ? `
            <div class="direccion-entrega">

                <div class="direccion-titulo">
                    DIRECCIÓN DE ENTREGA
                </div>

                <div class="direccion-texto">
                    ${escaparHTML(
            direccionEntrega || "DIRECCIÓN NO REGISTRADA"
        )}
                </div>

            </div>
        `
        : "";

    const mesaHTML = (
        !esDomicilio &&
        mesa &&
        servicio === "MESA"
    )
        ? `
            <div class="info">
                <strong>MESA:</strong>
                ${escaparHTML(mesa)}
            </div>
        `
        : "";


    // =============================================
    // HTML TERMICO
    // =============================================

    const html = `

        <!DOCTYPE html>

        <html lang="es">

        <head>

            <meta charset="UTF-8">

            <title>Venta #${numero}</title>

            <style>

                @page {
                    size: 80mm auto;
                    margin: 0;
                }

                * {
                    box-sizing: border-box;
                }

                html,
                body {
                    width: 80mm;
                    margin: 0;
                    padding: 0;
                    background: #fff;
                    color: #000;
                }

                body {
                    width: 72mm;
                    margin: 0 auto;
                    padding: 5px;

                    font-family:
                        "Courier New",
                        monospace;

                    font-size: 11px;

                    line-height: 1.3;

                    font-weight: normal;

                }

                .titulo {

                    text-align: center;

                    font-size: 18px;

                    font-weight: 900;

                    margin-bottom: 3px;

                }

                .subtitulo {

                    text-align: center;

                    font-size: 12px;

                    font-weight: 900;

                    margin-bottom: 5px;

                }

                .linea {

                    border-top: 1px dashed #000;

                    margin: 6px 0;

                }

                .venta-numero {

                    text-align: center;

                    font-size: 17px;

                    font-weight: 900;

                    margin: 7px 0;

                }

                .info {

                    margin: 3px 0;

                    font-size: 11px;

                    font-weight: bold;

                    overflow-wrap: anywhere;

                    word-break: break-word;

                }

                .direccion-entrega {

                    margin: 8px 0;

                    padding: 6px;

                    border: 1px dashed #000;

                    overflow-wrap: anywhere;

                    word-break: break-word;

                }

                .direccion-titulo {

                    font-size: 11px;

                    font-weight: 900;

                    margin-bottom: 3px;

                }

                .direccion-texto {

                    font-size: 11px;

                    font-weight: bold;

                    line-height: 1.4;

                    overflow-wrap: anywhere;

                    word-break: break-word;

                }

                .seccion {

                    text-align: center;

                    font-size: 12px;

                    font-weight: 900;

                    margin: 8px 0;

                }

                .producto {

                    margin: 8px 0;

                }

                .producto-header {

                    display: flex;

                    align-items: flex-start;

                    gap: 5px;

                    font-size: 12px;

                    font-weight: 900;

                }

                .producto-cantidad {

                    min-width: 32px;

                    font-size: 12px;

                    font-weight: 900;

                }

                .producto-nombre {

                    flex: 1;

                    overflow-wrap: anywhere;

                    word-break: break-word;

                }

                .producto-tipo {

                    padding-left: 37px;

                    font-size: 9px;

                    margin-top: 2px;

                }

                .producto-valores {

                    display: flex;

                    justify-content: space-between;

                    gap: 5px;

                    padding-left: 37px;

                    margin-top: 3px;

                    font-size: 10px;

                }

                .producto-valores strong {

                    white-space: nowrap;

                }

                .total {

                    display: flex;

                    justify-content: space-between;

                    align-items: center;

                    gap: 5px;

                    font-size: 16px;

                    font-weight: 900;

                    margin-top: 10px;

                    padding: 8px 0;

                    border-top: 2px dashed #000;

                    border-bottom: 2px dashed #000;

                }

                .pago {

                    margin-top: 8px;

                    font-size: 11px;

                    font-weight: bold;

                    text-align: center;

                }

                .footer {

                    text-align: center;

                    font-size: 11px;

                    font-weight: 900;

                    margin-top: 12px;

                    margin-bottom: 8px;

                }

                @media print {

                    html,
                    body {

                        width: 80mm;

                        margin: 0;

                        padding: 0;

                    }

                    body {

                        width: 72mm;

                        padding: 5px;

                    }

                }

            </style>

        </head>

        <body>

            <!-- ENCABEZADO -->

            <div class="titulo">
                PARCHE EL ANTOJO
            </div>

            <div class="subtitulo">
                COMPROBANTE DE VENTA
            </div>

            <div class="linea"></div>


            <!-- NUMERO DE VENTA -->

            <div class="venta-numero">
                VENTA #${escaparHTML(numero)}
            </div>


            <!-- DATOS GENERALES -->

            <div class="info">
                FECHA: ${escaparHTML(fecha)}
            </div>

            <div class="info">
                CLIENTE: ${cliente}
            </div>

            ${servicioHTML}

            ${direccionHTML}

            ${mesaHTML}

            <div class="info">
                CATEGORÍA: ${categoria}
            </div>

            <div class="info">
                ATENDIDO POR: ${usuario}
            </div>

            <div class="info">
                MÉTODO DE PAGO: ${metodoPago}
            </div>


            <!-- PRODUCTOS -->

            <div class="linea"></div>

            <div class="seccion">
                PRODUCTOS
            </div>

            <div class="linea"></div>

            ${productosHTML}


            <!-- TOTAL -->

            <div class="total">

                <span>
                    TOTAL
                </span>

                <span>
                    ${formatoMoneda(total)}
                </span>

            </div>


            <!-- METODO DE PAGO -->

            <div class="pago">
                PAGO: ${metodoPago}
            </div>


            <!-- PIE -->

            <div class="linea"></div>

            <div class="footer">
                ¡GRACIAS POR SU COMPRA!
            </div>

            <div class="footer">
                PARCHE EL ANTOJO
            </div>

        </body>

        </html>

    `;


    // =============================================
    // VENTANA DE IMPRESION
    // =============================================

    const ventana = window.open(
        "",
        "_blank",
        "width=400,height=700"
    );

    if (!ventana) {

        mostrarMensaje(
            "El navegador bloqueó la ventana de impresión.",
            "warning"
        );

        return;

    }

    ventana.document.open();

    ventana.document.write(html);

    ventana.document.close();

    ventana.onafterprint = () => {
        ventana.close();
    };

    setTimeout(() => {

        if (!ventana.closed) {

            ventana.focus();

            ventana.print();

        }

    }, 500);

}


// =====================================================
// CERRAR MODAL
// =====================================================

window.cerrarModal = function () {

    getEl("modalCompra")?.classList.add("hidden");

};


// =====================================================
// INICIALIZAR EVENTOS DEL MODAL
// =====================================================

function inicializarModalVentas() {

    // =============================================
    // VER DETALLE
    // =============================================

    getEl("tablaVentas")?.addEventListener(
        "click",
        event => {

            const boton = event.target.closest(
                ".btn-ver-detalle-venta"
            );

            if (!boton) return;

            const id = Number(
                boton.dataset.ventaId
            );

            if (id > 0) {

                window.verDetalleVenta(id);

            }

        }
    );


    // =============================================
    // IMPRIMIR COMPROBANTE
    // =============================================

    getEl("btnImprimirVenta")?.addEventListener(
        "click",
        imprimirComprobanteVenta
    );


    // =============================================
    // CERRAR AL HACER CLIC FUERA
    // =============================================

    getEl("modalCompra")?.addEventListener(
        "click",
        event => {

            if (event.target === getEl("modalCompra")) {

                window.cerrarModal();

            }

        }
    );


    // =============================================
    // CERRAR CON ESCAPE
    // =============================================

    document.addEventListener(
        "keydown",
        event => {

            if (
                event.key === "Escape" &&
                !getEl("modalCompra")?.classList.contains("hidden")
            ) {

                window.cerrarModal();

            }

        }
    );

}


// =====================================================
// MENSAJES TOAST
// =====================================================

function mostrarMensaje(mensaje, tipo = "success") {

    document
        .querySelectorAll(".toast")
        .forEach(toast => toast.remove());

    const iconos = {

        success: "✅",

        warning: "⚠️",

        error: "❌",

        info: "ℹ️"

    };

    const duraciones = {

        success: 3000,

        info: 4000,

        warning: 6000,

        error: 8000

    };

    const toast = document.createElement("div");

    toast.className = `toast ${tipo}`;

    toast.textContent = `${iconos[tipo] || ""} ${mensaje}`;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {

        toast.classList.add("show");

    });

    window.setTimeout(() => {

        toast.classList.remove("show");

        window.setTimeout(() => toast.remove(), 300);

    }, duraciones[tipo] || 4000);

}
