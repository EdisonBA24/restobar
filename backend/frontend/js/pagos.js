
import { apiFetch, API_URL } from "./api.js";
import { TablaUI } from "./tablas.js";

// =====================================================
// CONFIGURACION Y ESTADO
// =====================================================

const STORAGE_PAGE_SIZE = "pagos_page_size";
const EXCEL_MIME = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";

let tablaPagosUI = null;
let timeoutBusqueda = null;
let solicitudActual = 0;
let solicitudResumenActual = 0;


// =====================================================
// HELPERS GENERALES
// =====================================================

function getEl(id) {
    return document.getElementById(id);
}


function escaparHTML(valor) {

    return String(valor ?? "").replace(
        /[&<>"']/g,
        caracter => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        })[caracter]
    );

}


function fechaLocalHoy() {

    const hoy = new Date();

    const anio = hoy.getFullYear();

    const mes = String(
        hoy.getMonth() + 1
    ).padStart(2, "0");

    const dia = String(
        hoy.getDate()
    ).padStart(2, "0");

    return `${anio}-${mes}-${dia}`;

}


function formatoMoneda(valor) {

    const monto = Number(valor) || 0;

    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP",
        maximumFractionDigits: 0
    }).format(monto);

}


function formatoNumero(valor) {

    return new Intl.NumberFormat("es-CO", {
        maximumFractionDigits: 0
    }).format(Number(valor) || 0);

}


// =====================================================
// FILTROS COMPARTIDOS
// =====================================================

function obtenerFiltrosActuales() {

    return {

        search: getEl("busquedaPago")?.value.trim() || "",

        fecha_inicio: getEl("fechaInicioPago")?.value || "",

        fecha_fin: getEl("fechaFinPago")?.value || ""

    };

}


function crearParametrosFiltros() {

    const filtros = obtenerFiltrosActuales();

    const params = new URLSearchParams();

    if (filtros.search) {
        params.set("search", filtros.search);
    }

    if (filtros.fecha_inicio) {
        params.set("fecha_inicio", filtros.fecha_inicio);
    }

    if (filtros.fecha_fin) {
        params.set("fecha_fin", filtros.fecha_fin);
    }

    return params;

}


function validarRangoFechas(mostrarAviso = true) {

    const {
        fecha_inicio,
        fecha_fin
    } = obtenerFiltrosActuales();

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
// INICIALIZACION
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {

    if (!getEl("tablaPagos")) {
        return;
    }

    // =============================================
    // TABLA UI
    // =============================================

    tablaPagosUI = new TablaUI({

        nombre: "pagos",

        callback: () => cargarPagos(),

        tabla: "#tablaPagosTabla",

        pageSize: "#pageSizePagos",

        btnAnterior: "#btnPaginaAnteriorPagos",

        btnSiguiente: "#btnPaginaSiguientePagos",

        numeros: "#numerosPaginacionPagos",

        resumen: "#resumenPaginacionPagos",

        info: "#infoPaginacionPagos"

    }).init();


    // =============================================
    // TAMAÑO DE PAGINA
    // =============================================

    const pageSizeGuardado = Number(
        localStorage.getItem(STORAGE_PAGE_SIZE)
    );

    const pageSizeInicial = [10, 20, 50, 100].includes(
        pageSizeGuardado
    )
        ? pageSizeGuardado
        : 10;

    tablaPagosUI.actualizarDesdeBackend({

        page: 1,

        page_size: pageSizeInicial,

        total: 0,

        total_pages: 1,

        sort_by: "id",

        sort_order: "desc"

    });


    getEl("pageSizePagos")?.addEventListener(
        "change",
        event => {

            localStorage.setItem(
                STORAGE_PAGE_SIZE,
                event.target.value
            );

        }
    );


    // =============================================
    // FORMULARIO
    // =============================================

    getEl("formPago")?.addEventListener(
        "submit",
        guardarPago
    );

    getEl("btnNuevoPago")?.addEventListener(
        "click",
        mostrarFormularioPago
    );

    getEl("btnCancelarPago")?.addEventListener(
        "click",
        cancelarFormularioPago
    );


    // =============================================
    // BUSQUEDA
    // =============================================

    getEl("busquedaPago")?.addEventListener(
        "input",
        filtrarPagos
    );


    // =============================================
    // FILTROS DE FECHA
    // =============================================

    getEl("fechaInicioPago")?.addEventListener(
        "change",
        aplicarFiltros
    );

    getEl("fechaFinPago")?.addEventListener(
        "change",
        aplicarFiltros
    );

    getEl("btnLimpiarFiltrosPagos")?.addEventListener(
        "click",
        limpiarFiltros
    );


    // =============================================
    // EXPORTAR EXCEL
    // =============================================

    getEl("btnExportarPagos")?.addEventListener(
        "click",
        descargarPagosExcel
    );


    // =============================================
    // CARGAR EMPLEADOS
    // =============================================

    await cargarUsuarios();


    // =============================================
    // COMPATIBILIDAD CON CREAR_PAGO.HTML
    // =============================================

    const url = new URL(window.location.href);

    if (url.searchParams.get("accion") === "nuevo") {

        url.searchParams.delete("accion");

        window.history.replaceState(
            {},
            "",
            url.pathname + url.search + url.hash
        );

        mostrarFormularioPago();

    }


    // =============================================
    // CARGAR INFORMACION INICIAL
    // =============================================

    await recargarDatosPagos();

});


// =====================================================
// CARGAR EMPLEADOS ACTIVOS
// =====================================================

async function cargarUsuarios() {

    const select = getEl("usuario_id");

    if (!select) return;

    try {

        const res = await apiFetch("/usuarios/select");

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible cargar los empleados."
            );

        }

        const usuarios = Array.isArray(res.data)
            ? res.data
            : [];

        select.innerHTML = "";

        const opcionInicial = document.createElement("option");

        opcionInicial.value = "";

        opcionInicial.textContent = usuarios.length
            ? "Seleccione un empleado"
            : "No hay empleados activos";

        select.appendChild(opcionInicial);

        usuarios.forEach(usuario => {

            const opcion = document.createElement("option");

            opcion.value = usuario.id;

            opcion.textContent = usuario.nombre || "Sin nombre";

            select.appendChild(opcion);

        });

    } catch (error) {

        console.error(
            "Error cargando empleados:",
            error
        );

        select.innerHTML = `
            <option value="">Error cargando empleados</option>
        `;

        mostrarMensaje(
            error.message || "Error cargando empleados.",
            "error"
        );

    }

}


// =====================================================
// MOSTRAR FORMULARIO
// =====================================================

function mostrarFormularioPago() {

    const form = getEl("formPago");

    if (form) {
        form.reset();
    }

    const fecha = getEl("fecha");

    if (fecha) {
        fecha.value = fechaLocalHoy();
    }

    getEl("formContainer")?.classList.remove("hidden");

    getEl("usuario_id")?.focus();

    getEl("formContainer")?.scrollIntoView({

        behavior: "smooth",

        block: "start"

    });

}


// Compatibilidad con el menú existente.

window.abrirNuevoPago = mostrarFormularioPago;


// =====================================================
// CANCELAR FORMULARIO
// =====================================================

function cancelarFormularioPago() {

    getEl("formPago")?.reset();

    getEl("formContainer")?.classList.add("hidden");

}


// =====================================================
// GUARDAR PAGO
// =====================================================

async function guardarPago(event) {

    event.preventDefault();

    const usuarioId = Number(
        getEl("usuario_id")?.value
    );

    const monto = Number(
        getEl("monto")?.value
    );

    const concepto = (
        getEl("concepto")?.value || ""
    ).trim();

    const fecha = getEl("fecha")?.value;


    // =============================================
    // VALIDACIONES
    // =============================================

    if (
        !usuarioId ||
        !Number.isFinite(monto) ||
        monto <= 0 ||
        !concepto ||
        !fecha
    ) {

        mostrarMensaje(
            "Completa todos los campos correctamente.",
            "warning"
        );

        return;

    }


    const datos = {

        usuario_id: usuarioId,

        monto,

        concepto,

        fecha

    };


    const boton = getEl("btnGuardarPago");

    if (boton) {

        boton.disabled = true;

        boton.textContent = "Guardando...";

    }


    try {

        const res = await apiFetch(
            "/pagos",
            "POST",
            datos
        );

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible registrar el pago."
            );

        }

        mostrarMensaje(
            res.message || "Pago registrado correctamente.",
            "success"
        );


        // Limpiar y cerrar el formulario.

        getEl("formPago")?.reset();

        const fechaInput = getEl("fecha");

        if (fechaInput) {
            fechaInput.value = fechaLocalHoy();
        }

        getEl("formContainer")?.classList.add("hidden");


        // Actualizar tabla e indicadores.

        tablaPagosUI?.reiniciarPaginacion();

        await recargarDatosPagos();


    } catch (error) {

        console.error(
            "Error registrando pago:",
            error
        );

        mostrarMensaje(
            error.message || "Error registrando el pago.",
            "error"
        );

    } finally {

        if (boton) {

            boton.disabled = false;

            boton.textContent = "💾 Guardar Pago";

        }

    }

}


// =====================================================
// BÚSQUEDA
// =====================================================

function filtrarPagos() {

    clearTimeout(timeoutBusqueda);

    timeoutBusqueda = setTimeout(() => {

        recargarPorFiltros();

    }, 350);

}


// =====================================================
// APLICAR FILTROS
// =====================================================

function aplicarFiltros() {

    clearTimeout(timeoutBusqueda);

    recargarPorFiltros();

}


// =====================================================
// LIMPIAR FILTROS
// =====================================================

function limpiarFiltros() {

    const busqueda = getEl("busquedaPago");

    const fechaInicio = getEl("fechaInicioPago");

    const fechaFin = getEl("fechaFinPago");

    if (busqueda) {
        busqueda.value = "";
    }

    if (fechaInicio) {
        fechaInicio.value = "";
    }

    if (fechaFin) {
        fechaFin.value = "";
    }

    clearTimeout(timeoutBusqueda);

    recargarPorFiltros();

}


// =====================================================
// RECARGA COORDINADA DE INFORMACION
// =====================================================

async function recargarPorFiltros() {

    if (!validarRangoFechas()) {
        return;
    }

    tablaPagosUI?.reiniciarPaginacion();

    await recargarDatosPagos();

}


async function recargarDatosPagos() {

    await Promise.all([

        cargarPagos(),

        cargarResumenPagos()

    ]);

}


// =====================================================
// CARGAR HISTORIAL PAGINADO
// =====================================================

async function cargarPagos() {

    if (!tablaPagosUI) return;

    if (!validarRangoFechas(false)) return;

    const numeroSolicitud = ++solicitudActual;

    const filtros = obtenerFiltrosActuales();

    const params = new URLSearchParams({

        page: String(tablaPagosUI.page),

        page_size: String(tablaPagosUI.pageSize),

        sort_by: tablaPagosUI.sortBy,

        sort_order: tablaPagosUI.sortOrder

    });

    if (filtros.search) {
        params.set("search", filtros.search);
    }

    if (filtros.fecha_inicio) {
        params.set("fecha_inicio", filtros.fecha_inicio);
    }

    if (filtros.fecha_fin) {
        params.set("fecha_fin", filtros.fecha_fin);
    }

    try {

        const res = await apiFetch(
            `/pagos?${params.toString()}`
        );


        // Evita que una consulta anterior
        // sobrescriba una consulta más reciente.

        if (numeroSolicitud !== solicitudActual) {
            return;
        }

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible consultar los pagos."
            );

        }

        const resultado = res.data || {};

        const pagos = Array.isArray(resultado.items)
            ? resultado.items
            : [];


        // Actualizar paginación y ordenamiento.

        tablaPagosUI.actualizarDesdeBackend(resultado);

        const tbody = getEl("tablaPagos");

        if (!tbody) return;

        if (!pagos.length) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="pagos-empty">
                        No se encontraron pagos registrados.
                    </td>
                </tr>
            `;

            return;

        }


        // Renderizar pagos.

        tbody.innerHTML = pagos.map(pago => {

            const id = Number(pago.id) || 0;

            const empleado = escaparHTML(
                pago.empleado || "Empleado no disponible"
            );

            const concepto = escaparHTML(
                pago.concepto || ""
            );

            const fecha = escaparHTML(
                formatearFecha(pago.fecha)
            );

            const monto = formatoMoneda(pago.monto);

            return `
                <tr>

                    <td data-label="ID">
                        ${id}
                    </td>

                    <td data-label="Empleado">
                        ${empleado}
                    </td>

                    <td data-label="Concepto">
                        ${concepto}
                    </td>

                    <td data-label="Fecha">
                        ${fecha}
                    </td>

                    <td data-label="Monto" class="pagos-amount">
                        ${monto}
                    </td>

                </tr>
            `;

        }).join("");


    } catch (error) {

        if (numeroSolicitud !== solicitudActual) {
            return;
        }

        console.error(
            "Error cargando pagos:",
            error
        );

        getEl("tablaPagos").innerHTML = `
            <tr>
                <td colspan="5" class="pagos-empty">
                    No fue posible cargar los pagos.
                </td>
            </tr>
        `;

        mostrarMensaje(
            error.message || "Error cargando pagos.",
            "error"
        );

    }

}


// =====================================================
// RESUMEN FINANCIERO
// =====================================================

function mostrarEstadoResumen(mensaje, tipo = "normal") {

    const estado = getEl("estadoResumenPagos");

    if (!estado) return;

    estado.textContent = mensaje;

    estado.dataset.estado = tipo;

}


function actualizarIndicadoresResumen(resumen = {}) {

    const cantidad = Number(
        resumen.cantidad_pagos
    ) || 0;

    const total = Number(
        resumen.total_pagado
    ) || 0;

    const empleados = Number(
        resumen.empleados
    ) || 0;

    const promedio = Number(
        resumen.promedio_pago
    ) || 0;


    const elCantidad = getEl("resumenCantidadPagos");

    const elTotal = getEl("resumenTotalPagado");

    const elEmpleados = getEl("resumenEmpleadosPagos");

    const elPromedio = getEl("resumenPromedioPago");


    if (elCantidad) {
        elCantidad.textContent = formatoNumero(cantidad);
    }

    if (elTotal) {
        elTotal.textContent = formatoMoneda(total);
    }

    if (elEmpleados) {
        elEmpleados.textContent = formatoNumero(empleados);
    }

    if (elPromedio) {
        elPromedio.textContent = formatoMoneda(promedio);
    }

}


async function cargarResumenPagos() {

    if (!validarRangoFechas(false)) {
        return;
    }

    const numeroSolicitud = ++solicitudResumenActual;

    const params = crearParametrosFiltros();

    const query = params.toString();

    mostrarEstadoResumen(
        "Actualizando indicadores...",
        "loading"
    );


    try {

        const endpoint = query
            ? `/pagos/resumen?${query}`
            : "/pagos/resumen";

        const res = await apiFetch(endpoint);


        // Ignorar respuestas de filtros anteriores.

        if (numeroSolicitud !== solicitudResumenActual) {
            return;
        }

        if (!res || res.status !== "success") {

            throw new Error(
                res?.message || "No fue posible consultar el resumen de pagos."
            );

        }

        const resumen = res.data || {};

        actualizarIndicadoresResumen(resumen);

        const cantidad = Number(
            resumen.cantidad_pagos
        ) || 0;

        mostrarEstadoResumen(

            cantidad === 0
                ? "No hay pagos para los filtros seleccionados."
                : `Indicadores calculados sobre ${formatoNumero(cantidad)} pago(s).`,

            "success"

        );


    } catch (error) {

        if (numeroSolicitud !== solicitudResumenActual) {
            return;
        }

        console.error(
            "Error cargando resumen de pagos:",
            error
        );

        actualizarIndicadoresResumen({});

        mostrarEstadoResumen(
            error.message || "No fue posible actualizar los indicadores.",
            "error"
        );

    }

}


// =====================================================
// EXPORTAR PAGOS A EXCEL
// =====================================================

function obtenerNombreArchivo(response) {

    const disposition = response.headers.get(
        "Content-Disposition"
    ) || "";

    const coincidencia = disposition.match(
        /filename\*?=(?:UTF-8''|"?)("[^"]+"|[^;]+)/i
    );

    if (!coincidencia) {
        return `pagos_${fechaLocalHoy()}.xlsx`;
    }

    const nombre = coincidencia[1]
        .replace(/"/g, "")
        .trim();

    try {

        return decodeURIComponent(nombre);

    } catch (_) {

        return nombre;

    }

}


async function leerMensajeError(response) {

    const texto = await response.text();

    if (!texto) {

        return `No fue posible exportar los pagos (HTTP ${response.status}).`;

    }

    try {

        const json = JSON.parse(texto);

        return json.message || `Error ${response.status}`;

    } catch (_) {

        return texto;

    }

}


async function descargarPagosExcel() {

    if (!validarRangoFechas()) {
        return;
    }

    const boton = getEl("btnExportarPagos");

    const textoOriginal = boton?.textContent || "📥 Exportar Excel";

    if (boton) {

        boton.disabled = true;

        boton.textContent = "Generando Excel...";

    }


    try {

        const params = crearParametrosFiltros();

        const query = params.toString();

        const endpoint = query
            ? `${API_URL}/pagos/exportar?${query}`
            : `${API_URL}/pagos/exportar`;


        // Se utiliza fetch directamente porque la respuesta
        // es un archivo binario y no una respuesta JSON.

        const response = await fetch(endpoint, {

            method: "GET",

            credentials: "include",

            headers: {
                Accept: EXCEL_MIME
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
                await leerMensajeError(response)
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
                await leerMensajeError(response)
            );

        }


        const blob = await response.blob();

        if (!blob.size) {

            throw new Error(
                "El archivo Excel recibido está vacío."
            );

        }


        // Crear enlace temporal de descarga.

        const url = window.URL.createObjectURL(blob);

        const enlace = document.createElement("a");

        enlace.href = url;

        enlace.download = obtenerNombreArchivo(response);

        enlace.style.display = "none";

        document.body.appendChild(enlace);

        enlace.click();

        enlace.remove();


        // Liberar memoria.

        window.setTimeout(() => {

            window.URL.revokeObjectURL(url);

        }, 1500);


        mostrarMensaje(
            "El archivo Excel de pagos se generó correctamente.",
            "success"
        );


    } catch (error) {

        console.error(
            "Error exportando pagos:",
            error
        );

        mostrarMensaje(
            error.message || "No fue posible descargar el Excel.",
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
// FORMATO DE FECHA
// =====================================================

function formatearFecha(valor) {

    if (!valor) return "";

    const texto = String(valor).trim();

    // Evita desfases de zona horaria en fechas YYYY-MM-DD.

    const soloFecha = texto.match(
        /^(\d{4})-(\d{2})-(\d{2})$/
    );

    if (soloFecha) {

        return `${soloFecha[3]}/${soloFecha[2]}/${soloFecha[1]}`;

    }

    try {

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


    } catch (error) {

        console.error(
            "Error formateando fecha:",
            error
        );

        return texto;

    }

}


// =====================================================
// MENSAJES TOAST
// =====================================================

function mostrarMensaje(msg, tipo = "success") {

    document
        .querySelectorAll(".toast")
        .forEach(toast => toast.remove());

    const iconos = {

        success: "✅",

        warning: "⚠️",

        error: "❌",

        info: "ℹ️"

    };

    const tiempos = {

        success: 3000,

        info: 4000,

        warning: 6000,

        error: 8000

    };

    const toast = document.createElement("div");

    toast.className = `toast ${tipo}`;

    toast.textContent = `${iconos[tipo] || ""} ${msg}`;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {

        toast.classList.add("show");

    });

    window.setTimeout(() => {

        toast.classList.remove("show");

        window.setTimeout(() => toast.remove(), 300);

    }, tiempos[tipo] || 4000);

}
