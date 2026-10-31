import { apiFetch } from "./api.js";
import { TablaUI } from "./tablas.js";


// =====================================================
// CONFIGURACIÓN Y ESTADO
// =====================================================

const STORAGE_PAGE_SIZE = "pagos_page_size";

let tablaPagosUI = null;

let timeoutBusqueda = null;

let solicitudActual = 0;


// =====================================================
// HELPERS
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


// =====================================================
// INICIALIZACIÓN
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {

    // Evita inicializar el módulo en otra página.
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
    // TAMAÑO DE PÁGINA GUARDADO
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
        (e) => {

            localStorage.setItem(
                STORAGE_PAGE_SIZE,
                e.target.value
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
    // BÚSQUEDA
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
    // CARGAR HISTORIAL
    // =============================================

    await cargarPagos();

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
            <option value="">
                Error cargando empleados
            </option>
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


    getEl("formContainer")?.classList.remove(
        "hidden"
    );


    getEl("usuario_id")?.focus();


    getEl("formContainer")?.scrollIntoView({

        behavior: "smooth",

        block: "start"

    });

}


// Permite abrir el formulario desde el menú lateral.
window.abrirNuevoPago = mostrarFormularioPago;


// =====================================================
// CANCELAR FORMULARIO
// =====================================================

function cancelarFormularioPago() {

    getEl("formPago")?.reset();

    getEl("formContainer")?.classList.add(
        "hidden"
    );

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

        monto: monto,

        concepto: concepto,

        fecha: fecha

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

        getEl("fecha").value = fechaLocalHoy();

        getEl("formContainer")?.classList.add(
            "hidden"
        );


        // Mostrar el registro nuevo desde la primera página.

        tablaPagosUI.reiniciarPaginacion();

        await cargarPagos();


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

        tablaPagosUI.reiniciarPaginacion();

        cargarPagos();

    }, 350);

}


// =====================================================
// APLICAR FILTROS DE FECHA
// =====================================================

function aplicarFiltros() {

    const fechaInicio = getEl("fechaInicioPago")?.value;

    const fechaFin = getEl("fechaFinPago")?.value;


    if (
        fechaInicio &&
        fechaFin &&
        fechaFin < fechaInicio
    ) {

        mostrarMensaje(
            "La fecha final no puede ser anterior a la inicial.",
            "warning"
        );

        return;

    }


    tablaPagosUI.reiniciarPaginacion();

    cargarPagos();

}


// =====================================================
// LIMPIAR FILTROS
// =====================================================

function limpiarFiltros() {

    getEl("busquedaPago").value = "";

    getEl("fechaInicioPago").value = "";

    getEl("fechaFinPago").value = "";


    tablaPagosUI.reiniciarPaginacion();

    cargarPagos();

}


// =====================================================
// CARGAR HISTORIAL PAGINADO
// =====================================================

async function cargarPagos() {

    if (!tablaPagosUI) return;


    const fechaInicio = getEl("fechaInicioPago")?.value || "";

    const fechaFin = getEl("fechaFinPago")?.value || "";


    if (
        fechaInicio &&
        fechaFin &&
        fechaFin < fechaInicio
    ) {
        return;
    }


    const numeroSolicitud = ++solicitudActual;


    try {

        const params = new URLSearchParams({

            page: tablaPagosUI.page,

            page_size: tablaPagosUI.pageSize,

            search: getEl("busquedaPago")?.value.trim() || "",

            fecha_inicio: fechaInicio,

            fecha_fin: fechaFin,

            sort_by: tablaPagosUI.sortBy,

            sort_order: tablaPagosUI.sortOrder

        });


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


        // Actualizar estado de paginación y ordenamiento.

        tablaPagosUI.actualizarDesdeBackend(resultado);


        const tbody = getEl("tablaPagos");

        if (!tbody) return;


        if (!pagos.length) {

            tbody.innerHTML = `
                <tr>
                    <td
                        colspan="5"
                        class="pagos-empty"
                    >
                        No se encontraron pagos registrados.
                    </td>
                </tr>
            `;

            return;

        }


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
                <td
                    colspan="5"
                    class="pagos-empty"
                >
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
// FORMATO DE MONEDA
// =====================================================

function formatoMoneda(valor) {

    const monto = Number(valor) || 0;

    return new Intl.NumberFormat("es-CO", {

        style: "currency",

        currency: "COP",

        maximumFractionDigits: 0

    }).format(monto);

}


// =====================================================
// FORMATO DE FECHA
// =====================================================

function formatearFecha(valor) {

    if (!valor) return "";


    const texto = String(valor).trim();


    // Evita que una fecha YYYY-MM-DD
    // se muestre como el día anterior por la zona horaria.

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


    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => toast.remove(), 300);

    }, tiempos[tipo] || 4000);

}