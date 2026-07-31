import { apiFetch } from "./api.js";
// IMPORTACION DE TABLAS.JS
import { TablaUI } from "./tablas.js";

let productos = [];
let tiposIVA = [];
let proveedores = [];

let proveedorSeleccionado = null;

// =====================================
// FILTROS DEL LISTADO
// =====================================

const filtrosCompras = {

    periodo: "mes_actual",

    fecha_inicio: "",

    fecha_fin: "",

    proveedor_id: "",

    buscar: ""

};

const STORAGE_PAGE_SIZE = "compras_page_size";

//SE AGREGAR AL IMPORTA TABLAS.JS
let tablaCompras = null;

// ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
// const estadoPaginacion = {
//    page: 1,
//    page_size: 10,
//    total: 0,
//    total_pages: 1
//};

// ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
// const estadoOrden = {
//    sort_by: "id",
//    sort_order: "desc"
//};

let timeoutBusqueda = null;

document.addEventListener("DOMContentLoaded", async () => {

    await cargarProductos();

    await cargarProveedores();

    await cargarTiposIVA();

    //SE AGREGA AL IMPORTA TABLAS.JS
    tablaCompras = new TablaUI({

        nombre: "compras",

        callback: () => cargarCompras(),

        tabla: "#tablaCompras",

        pageSize: "#pageSizeCompras",

        btnAnterior: "#btnPaginaAnterior",

        btnSiguiente: "#btnPaginaSiguiente",

        numeros: "#numerosPaginacion",

        resumen: "#resumenPaginacionCompras",

        info: "#infoPaginacionCompras"

    }).init(); //SE AGREGA .INIT() POR AJUSTE EL TABLAS.JS

    //tablaCompras.setEstado({

    //    page: estadoPaginacion.page,

    //    page_size: estadoPaginacion.page_size,

    //    total: estadoPaginacion.total,

    //    total_pages: estadoPaginacion.total_pages,

    //    sort_by: estadoOrden.sort_by,

    //    sort_order: estadoOrden.sort_order

    //});

    const pageSizeGuardado = Number(
        localStorage.getItem(STORAGE_PAGE_SIZE)
    ) || 10;

    tablaCompras.setEstado({

        page: 1,

        page_size: pageSizeGuardado,

        total: 0,

        total_pages: 1,

        sort_by: "id",

        sort_order: "desc"

    });
    // ACA FINALIZA

    inicializarFechaCompra();

    inicializarFiltrosCompras();

    inicializarBuscadorProveedor();

    inicializarPaginacion();

    inicializarPageSize();

    inicializarOrdenamiento();

    const btnAgregarProducto = document.getElementById("btnAgregarProducto");

    if (btnAgregarProducto) {
        btnAgregarProducto.addEventListener("click", agregarProducto);
    }

    if (document.getElementById("tablaCompras")) {
        cargarCompras();
    }

    const form = document.getElementById("compraForm");

    if (form) {

        form.addEventListener("submit", async (e) => {

            e.preventDefault();

            await guardarCompra();

        });

    }

});


// ======================================================
// MÓDULO COMPRAS
//
// Este módulo únicamente registra compras de proveedores.
//
// La lógica de negocio (actualización de stock y cálculo
// del costo promedio) se ejecuta exclusivamente en el
// backend.
//
// En el futuro, el módulo Inventario será responsable de:
// - Kardex
// - Movimientos
// - Ajustes
// - Transferencias
// - Consumos por recetas
//
// Este frontend continuará enviando únicamente los datos
// de la compra.
// ======================================================
function ordenarPor(columna) {

    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    // if (estadoOrden.sort_by === columna) {

    //    estadoOrden.sort_order =
    //        estadoOrden.sort_order === "asc"
    //            ? "desc"
    //            : "asc";

    //} else {

    //    estadoOrden.sort_by = columna;
    //    estadoOrden.sort_order = "asc";

    //}

    //estadoPaginacion.page = 1;

    //actualizarIndicadoresOrden();

    //cargarCompras();

    tablaCompras.toggleOrden(columna);

    //actualizarIndicadoresOrden();

    //cargarCompras();

}

function actualizarIndicadoresOrden() {

    document
        .querySelectorAll("th[data-sort]")
        .forEach(th => {

            const icono = th.querySelector(".sort-icon");

            if (!icono) return;

            // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
            /*if (th.dataset.sort !== estadoOrden.sort_by)*/
            if (th.dataset.sort !== tablaCompras.sortBy) {

                icono.textContent = "⇅";
                return;

            }

            // ELIMINAR DESPUES DE IMPLEMENTAR TABLAS.JS
            // icono.textContent =
            //    estadoOrden.sort_order === "asc"
            icono.textContent =
                tablaCompras.sortOrder === "asc"
                    ? "▲"
                    : "▼";

        });

}


// =============================
// CARGAR TIPOS DE IVA
// =============================
async function cargarTiposIVA() {
    try {
        const res = await apiFetch("/compras/tipos-iva");

        if (!res || res.status === "error") {
            tiposIVA = [];
            return;
        }

        tiposIVA = res.data || [];

    } catch (error) {
        console.error("Error cargando tipos de IVA:", error);
        tiposIVA = [];
    }
}

// =============================
// GENERAR SELECT DE TIPO DE IVA
// =============================
function generarSelectIVA(selectedId = "") {

    let html = `<select class="form-select tipoIVA">`;

    html += `<option value="">Seleccione...</option>`;

    tiposIVA.forEach(iva => {

        html += `
            <option value="${iva.id}"
                ${Number(selectedId) === Number(iva.id) ? "selected" : ""}>
                ${iva.descripcion}
            </option>
        `;

    });

    html += `</select>`;

    return html;
}


// =============================
// CARGAR PRODUCTOS
// =============================
async function cargarProductos() {
    try {
        const res = await apiFetch("/productos?page=1&limit=100&inactivos=false");

        // 🔥 PROTECCIÓN
        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando productos ❌", "error");
            return;
        }

        //productos = (res.data || []).filter(p =>
        //    p.tipo === "INSUMO" ||
        //    p.tipo === "LICORES" ||
        //    p.tipo === "BEBIDAS"
        //);

        productos = res.data || [];

    } catch (error) {
        console.error("Error productos:", error);
        mostrarMensaje("Error cargando productos ❌", "error");
    }
}

// =============================
// CARGAR PROVEEDORES
// =============================
async function cargarProveedores() {

    try {

        const res = await apiFetch(
            "/proveedores?page=1&limit=1000&inactivos=false"
        );

        if (!res || res.status === "error") {

            proveedores = [];

            return;

        }

        proveedores = res.data || [];

    } catch (error) {

        console.error(error);

        proveedores = [];

    }

}

function mostrarListaProveedores(lista) {

    const contenedor = document.getElementById("listaProveedores");

    if (!contenedor) return;

    if (lista.length === 0) {

        contenedor.innerHTML = "";

        contenedor.classList.add("hidden");

        return;

    }

    contenedor.innerHTML = lista.map(p => `
        <div
            class="autocomplete-item"
            data-id="${p.id}">
            <strong>${p.nombre}</strong>
            <small>${p.nit || ""}</small>
        </div>
    `).join("");

    contenedor.classList.remove("hidden");

}

function filtrarProveedores(texto) {

    texto = texto.trim().toLowerCase();

    if (!texto) {

        mostrarListaProveedores([]);

        return;

    }

    const resultado = proveedores.filter(p =>
        (p.nombre || "")
            .toLowerCase()
            .includes(texto)
    );

    mostrarListaProveedores(resultado);

}

function seleccionarProveedor(id) {

    const proveedor = proveedores.find(
        p => Number(p.id) === Number(id)
    );

    if (!proveedor) return;

    proveedorSeleccionado = proveedor;

    document.getElementById("proveedorBusqueda").value =
        proveedor.nombre;

    document.getElementById("proveedorId").value =
        proveedor.id;

    mostrarListaProveedores([]);

}

function inicializarBuscadorProveedor() {

    const input = document.getElementById("proveedorBusqueda");

    const lista = document.getElementById("listaProveedores");

    if (!input || !lista) return;

    input.addEventListener("input", e => {

        proveedorSeleccionado = null;

        document.getElementById("proveedorId").value = "";

        filtrarProveedores(e.target.value);

    });

    lista.addEventListener("click", e => {

        const item = e.target.closest(".autocomplete-item");

        if (!item) return;

        seleccionarProveedor(item.dataset.id);

    });

    document.addEventListener("click", e => {

        if (
            !input.contains(e.target) &&
            !lista.contains(e.target)
        ) {

            lista.classList.add("hidden");

        }

    });

}

function inicializarFechaCompra() {

    const input = document.getElementById("fechaCompra");

    if (!input) return;

    const hoy = new Date();

    const yyyy = hoy.getFullYear();

    const mm = String(hoy.getMonth() + 1).padStart(2, "0");

    const dd = String(hoy.getDate()).padStart(2, "0");

    input.value = `${yyyy}-${mm}-${dd}`;

}


// =============================
// AGREGAR PRODUCTO
// =============================
function agregarProducto() {

    const container = document.getElementById("productosContainer");

    const indice =
        container.querySelectorAll(".producto-card").length + 1;

    const id = `producto_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;

    container.insertAdjacentHTML(
        "beforeend",
        crearCardProducto(id, indice)
    );

    const card = container.lastElementChild;

    inicializarCardProducto(card);

}

function crearCardProducto(id, indice) {

    return `
        <div class="producto-card" data-id="${id}">

            <div class="producto-card-header">

                <h4>Producto ${indice}</h4>

                <button
                    type="button"
                    class="btn-icon btn-danger eliminar-producto">

                    🗑

                </button>

            </div>

            <div class="form-grid">

                <div class="form-group">

                    <label>Producto</label>

                    <input type="hidden" class="productoId">

                    <input type="text" class="productoBusqueda" placeholder="Buscar producto..." autocomplete="off">

                    <div class="autocomplete-list hidden"></div>

                </div>

                <div class="form-group">

                    <label>Cantidad</label>

                    <input
                        type="number"
                        class="cantidadProducto"
                        min="1">

                </div>

                <div class="form-group">

                    <label>Precio Unitario</label>

                    <input
                        type="number"
                        class="precioProducto"
                        min="0">

                </div>

                <div class="form-group">

                    <label>IVA</label>

                    ${generarSelectIVA()}

                </div>

            </div>

            <div class="producto-totales">

                <div>

                    <span>Subtotal</span>

                    <strong class="subtotalProducto">$0</strong>

                </div>

                <div>

                    <span>IVA</span>

                    <strong class="ivaProducto">$0</strong>

                </div>

                <div>

                    <span>Total</span>

                    <strong class="totalProducto">$0</strong>

                </div>

            </div>

        </div>
    `;

}

// =============================
// INICIALIZAR CARD
// =============================
function inicializarCardProducto(card) {

    inicializarAutocompleteProducto(card);

    inicializarEventosCard(card);

    inicializarEliminar(card);

}

function inicializarAutocompleteProducto(card) {

    const input = card.querySelector(".productoBusqueda");
    const lista = card.querySelector(".autocomplete-list");
    const hidden = card.querySelector(".productoId");

    if (!input || !lista || !hidden) return;

    input.addEventListener("input", () => {

        hidden.value = "";

        const texto = input.value.trim().toLowerCase();

        if (!texto) {
            lista.innerHTML = "";
            lista.classList.add("hidden");
            return;
        }

        const filtrados = productos.filter(p =>
            (p.nombre || "").toLowerCase().includes(texto)
        );

        mostrarListaProductos(card, filtrados);

    });

    lista.addEventListener("click", (e) => {

        const item = e.target.closest(".autocomplete-item");

        if (!item) return;

        seleccionarProducto(card, Number(item.dataset.id));

    });

    document.addEventListener("click", (e) => {

        if (
            !input.contains(e.target) &&
            !lista.contains(e.target)
        ) {
            lista.classList.add("hidden");
        }

    });

}

function inicializarEventosCard(card) {

    const cantidad = card.querySelector(".cantidadProducto");
    const precio = card.querySelector(".precioProducto");
    const iva = card.querySelector(".tipoIVA");

    [cantidad, precio, iva].forEach(control => {

        if (!control) return;

        control.addEventListener("input", () => calcularCard(card));
        control.addEventListener("change", () => calcularCard(card));

    });

}

function calcularCard(card) {

    const cantidad =
        parseFloat(card.querySelector(".cantidadProducto").value) || 0;

    const precio =
        parseFloat(card.querySelector(".precioProducto").value) || 0;

    const tipoIVA =
        Number(card.querySelector(".tipoIVA").value);

    let porcentajeIVA = 0;

    const iva = tiposIVA.find(i => Number(i.id) === tipoIVA);

    if (iva) {
        porcentajeIVA = Number(iva.porcentaje);
    }

    const subtotal = cantidad * precio;

    const valorIVA = subtotal * porcentajeIVA / 100;

    const total = subtotal + valorIVA;

    card.querySelector(".subtotalProducto").textContent =
        formatoMoneda(subtotal);

    card.querySelector(".ivaProducto").textContent =
        formatoMoneda(valorIVA);

    card.querySelector(".totalProducto").textContent =
        formatoMoneda(total);

    actualizarResumenCompra();

}

function actualizarResumenCompra() {

    let subtotal = 0;
    let iva = 0;
    let total = 0;

    document.querySelectorAll(".producto-card").forEach(card => {

        const cantidad =
            parseFloat(card.querySelector(".cantidadProducto").value) || 0;

        const precio =
            parseFloat(card.querySelector(".precioProducto").value) || 0;

        const tipoIVA =
            Number(card.querySelector(".tipoIVA").value);

        let porcentaje = 0;

        const tipo = tiposIVA.find(t => Number(t.id) === tipoIVA);

        if (tipo) {
            porcentaje = Number(tipo.porcentaje);
        }

        const sub = cantidad * precio;
        const ivaLinea = sub * porcentaje / 100;

        subtotal += sub;
        iva += ivaLinea;
        total += sub + ivaLinea;

    });

    document.getElementById("subtotalCompra").textContent =
        formatoMoneda(subtotal);

    document.getElementById("ivaCompra").textContent =
        formatoMoneda(iva);

    document.getElementById("totalCompra").textContent =
        formatoMoneda(total);

}

function mostrarListaProductos(card, listaProductos) {

    const lista = card.querySelector(".autocomplete-list");

    if (!lista) return;

    if (listaProductos.length === 0) {

        lista.innerHTML = "";
        lista.classList.add("hidden");
        return;

    }

    lista.innerHTML = listaProductos.map(producto => `

        <div
            class="autocomplete-item"
            data-id="${producto.id}">

            <strong>${producto.nombre}</strong><br>

            <small>
                ${producto.categoria || ""}
                ${producto.unidad ? " • " + producto.unidad : ""}
            </small>

        </div>

    `).join("");

    lista.classList.remove("hidden");

}

function seleccionarProducto(card, productoId) {

    const producto = productos.find(
        p => Number(p.id) === Number(productoId)
    );

    if (!producto) return;

    card.querySelector(".productoId").value = producto.id;

    card.querySelector(".productoBusqueda").value = producto.nombre;

    const selectIVA = card.querySelector(".tipoIVA");

    if (selectIVA && producto.tipo_iva_id) {
        selectIVA.value = producto.tipo_iva_id;
    }

    card.querySelector(".autocomplete-list")
        .classList.add("hidden");

}

function inicializarEliminar(card) {

    const boton = card.querySelector(".eliminar-producto");

    if (!boton) return;

    boton.addEventListener("click", () => {

        card.remove();

        renumerarTarjetas();

        actualizarResumenCompra();

    });

}

function renumerarTarjetas() {

    document
        .querySelectorAll(".producto-card")
        .forEach((card, index) => {

            const titulo = card.querySelector("h4");

            if (titulo) {
                titulo.textContent = `Producto ${index + 1}`;
            }

        });

}

// =============================
// GUARDAR COMPRA
// =============================
window.guardarCompra = async function () {

    const proveedor_id = Number(
        document.getElementById("proveedorId").value
    );

    const fecha = document.getElementById("fechaCompra").value;

    const tarjetas = document.querySelectorAll(".producto-card");

    if (!proveedor_id) {

        mostrarMensaje(
            "Seleccione un proveedor ⚠️",
            "warning"
        );

        document.getElementById("proveedorBusqueda").focus();

        return;

    }

    if (!fecha) {

        mostrarMensaje(
            "Seleccione la fecha de la compra ⚠️",
            "warning"
        );

        document.getElementById("fechaCompra").focus();

        return;

    }

    if (tarjetas.length === 0) {
        mostrarMensaje("Agrega productos ⚠️", "warning");
        return;
    }

    let detalles = [];

    for (const card of tarjetas) {

        const producto_id = Number(
            card.querySelector(".productoId").value
        );

        const cantidad = parseFloat(
            card.querySelector(".cantidadProducto").value
        );

        const precio = parseFloat(
            card.querySelector(".precioProducto").value
        );

        const tipo_iva_id = Number(
            card.querySelector(".tipoIVA").value
        );

        if (!producto_id || cantidad <= 0 || precio <= 0) {
            mostrarMensaje("Datos incompletos o inválidos ⚠️", "warning");
            return;
        }

        detalles.push({

            producto_id,

            cantidad,

            precio_unitario: precio,

            tipo_iva_id

        });
    }

    try {

        console.log("===== DATOS COMPRA =====");
        console.log("Proveedor ID:", proveedor_id);
        console.log("Fecha:", fecha);
        console.log("Detalles:", detalles);

        const res = await apiFetch("/compras", "POST", {

            proveedor_id,

            fecha,

            detalles

        });

        if (!res || res.status === "error") {
            mostrarMensaje(res?.message || "Error en compra ❌", "error");
            return;
        }

        mostrarMensaje(
            "Compra registrada correctamente ✅",
            "success"
        );

        limpiarFormularioCompra();

        cancelarCompra();

        await cargarCompras();

    } catch (error) {
        console.error("Error compra:", error);
        mostrarMensaje("Error guardando compra ❌", "error");
    }
};


// =============================
// UTILIDADES
// =============================
function formatoMoneda(valor) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(valor || 0);
}


// =============================
// TOAST
// =============================
function mostrarMensaje(msg, tipo = "success") {

    const toast = document.createElement("div");
    toast.className = `toast ${tipo}`;
    toast.innerText = msg;

    document.body.appendChild(toast);

    setTimeout(() => toast.classList.add("show"), 50);

    setTimeout(() => {
        toast.classList.remove("show");
        setTimeout(() => toast.remove(), 300);
    }, 3000);
}

// =====================================
// FILTROS DEL LISTADO
// =====================================

function inicializarFiltrosCompras() {

    const periodo = document.getElementById("filtroPeriodo");

    const proveedor = document.getElementById("filtroProveedor");

    const buscar = document.getElementById("buscarCompra");

    const fechaInicio = document.getElementById("fechaInicio");

    const fechaFin = document.getElementById("fechaFin");

    const limpiar = document.getElementById("btnLimpiarFiltros");

    if (periodo) {

        periodo.addEventListener(
            "change",
            actualizarPeriodo
        );

    }

    if (proveedor) {

        proveedor.addEventListener("change", actualizarConsulta);

    }

    if (buscar) {

        buscar.addEventListener("input", () => {

            clearTimeout(timeoutBusqueda);

            timeoutBusqueda = setTimeout(() => {

                actualizarConsulta();

            }, 400);

        });

    }

    if (fechaInicio) {

        fechaInicio.addEventListener("change", actualizarConsulta);

    }

    if (fechaFin) {

        fechaFin.addEventListener("change", actualizarConsulta);

    }

    if (limpiar) {

        limpiar.addEventListener(
            "click",
            limpiarFiltrosCompras
        );

    }

    actualizarPeriodo();

}

function obtenerFiltros() {

    filtrosCompras.periodo =
        document.getElementById("filtroPeriodo")?.value || "mes_actual";

    filtrosCompras.fecha_inicio =
        document.getElementById("fechaInicio")?.value || "";

    filtrosCompras.fecha_fin =
        document.getElementById("fechaFin")?.value || "";

    filtrosCompras.proveedor_id =
        document.getElementById("filtroProveedor")?.value || "";

    filtrosCompras.buscar =
        document.getElementById("buscarCompra")?.value.trim() || "";

    return { ...filtrosCompras };

}

function actualizarConsulta() {

    const filtros = obtenerFiltros();

    console.log("Filtros activos:", filtros);

    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    // estadoPaginacion.page = 1;

    tablaCompras.reiniciarPaginacion();

    cargarCompras(filtros);

}

// =====================================
// UTILIDADES DE FECHAS
// =====================================

function formatearFechaISO(fecha) {

    return fecha.toISOString().split("T")[0];

}

function obtenerPrimerDiaMes(fecha) {

    return new Date(
        fecha.getFullYear(),
        fecha.getMonth(),
        1
    );

}

function obtenerPrimerDiaSemana(fecha) {

    const copia = new Date(fecha);

    const dia = copia.getDay();

    const diferencia = dia === 0 ? -6 : 1 - dia;

    copia.setDate(copia.getDate() + diferencia);

    copia.setHours(0, 0, 0, 0);

    return copia;

}

function obtenerUltimoDiaSemana(fecha) {

    const ultimo = obtenerPrimerDiaSemana(fecha);

    ultimo.setDate(ultimo.getDate() + 6);

    return ultimo;

}

function obtenerUltimoDiaMes(fecha) {

    return new Date(
        fecha.getFullYear(),
        fecha.getMonth() + 1,
        0
    );

}

function actualizarPeriodo() {

    const periodo = document.getElementById("filtroPeriodo");

    const fechaInicio = document.getElementById("fechaInicio");

    const fechaFin = document.getElementById("fechaFin");

    const filaFechas = document.getElementById("customDateFilters");

    if (!periodo || !fechaInicio || !fechaFin || !filaFechas) {

        return;

    }

    const opcionSeleccionada =
        periodo.options[periodo.selectedIndex];

    const esPersonalizado =
        opcionSeleccionada.dataset.custom === "true";

    filaFechas.classList.toggle(
        "hidden",
        !esPersonalizado
    );

    fechaInicio.disabled = !esPersonalizado;

    fechaFin.disabled = !esPersonalizado;

    if (esPersonalizado) {

        fechaInicio.value = "";

        fechaFin.value = "";

        return;

    }

    const hoy = new Date();

    let inicio;

    let fin;

    switch (periodo.value) {

        case "hoy":

            inicio = new Date(hoy);

            fin = new Date(hoy);

            break;

        case "ayer":

            inicio = new Date(hoy);

            inicio.setDate(inicio.getDate() - 1);

            fin = new Date(inicio);

            break;

        case "mes_actual":

            inicio = obtenerPrimerDiaMes(hoy);

            fin = obtenerUltimoDiaMes(hoy);

            break;

        case "mes_anterior":

            const anterior = new Date(
                hoy.getFullYear(),
                hoy.getMonth() - 1,
                1
            );

            inicio = obtenerPrimerDiaMes(anterior);

            fin = obtenerUltimoDiaMes(anterior);

            break;

        case "ultimos30":

            fin = new Date(hoy);

            inicio = new Date(hoy);

            inicio.setDate(inicio.getDate() - 29);

            break;

        case "esta_semana":

            inicio = obtenerPrimerDiaSemana(hoy);

            fin = obtenerUltimoDiaSemana(hoy);

            break;

        case "semana_pasada":

            const pasada = obtenerPrimerDiaSemana(hoy);

            pasada.setDate(pasada.getDate() - 7);

            inicio = obtenerPrimerDiaSemana(pasada);

            fin = obtenerUltimoDiaSemana(pasada);

            break;

        default:

            return;

    }

    fechaInicio.value = formatearFechaISO(inicio);

    fechaFin.value = formatearFechaISO(fin);

    actualizarConsulta();

}

function limpiarFiltrosCompras() {

    document.getElementById("filtroPeriodo").value = "mes_actual";

    document.getElementById("filtroProveedor").value = "";

    document.getElementById("buscarCompra").value = "";

    actualizarPeriodo();

}

function inicializarOrdenamiento() {

    document
        .querySelectorAll("th[data-sort]")
        .forEach(th => {

            th.style.cursor = "pointer";

            th.addEventListener("click", () => {

                console.log("CLICK:", th.dataset.sort);

                ordenarPor(th.dataset.sort);

            });

        });

}

// =============================
// CARGAR COMPRAS
// =============================
async function cargarCompras(filtros = null) {

    if (!filtros) {

        filtros = obtenerFiltros();

    }

    console.log("Consultando compras con:", filtros);

    try {

        const params = new URLSearchParams({

            periodo: filtros.periodo,

            fecha_inicio: filtros.fecha_inicio,

            fecha_fin: filtros.fecha_fin,

            proveedor_id: filtros.proveedor_id,

            buscar: filtros.buscar,

            page: tablaCompras.page,

            page_size: tablaCompras.pageSize,

            sort_by: tablaCompras.sortBy,

            sort_order: tablaCompras.sortOrder

        });

        console.log(params.toString());

        const res = await apiFetch(
            `/compras?${params.toString()}`
        );

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando compras ❌", "error");
            return;
        }

        const tabla = document.getElementById("tablaCompras");

        tabla.innerHTML = "";

        const resultado = res.data || {};

        //console.log("Respuesta backend:", resultado);

        actualizarEstadoPaginacion(resultado);

        const compras = resultado.items || [];

        //console.log("Compras:", compras);

        compras.forEach(c => {

            tabla.innerHTML += `
        <tr onclick="verDetalle(${c.id})" style="cursor:pointer">
            <td>${c.id}</td>
            <td>${c.proveedor || ""}</td>
            <td>${formatearFecha(c.fecha)}</td>
            <td>${formatoMoneda(c.subtotal)}</td>
            <td>${formatoMoneda(c.iva_total)}</td>
            <td>${formatoMoneda(c.total)}</td>
            <td>${c.usuario || ""}</td>
        </tr>
    `;

        });

        renderizarPaginacion();

    } catch (error) {
        console.error("Error compras:", error);
        mostrarMensaje("Error cargando compras ❌", "error");
    }
}

function actualizarEstadoPaginacion(resultado = {}) {

    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    // tablaCompras.setEstado({

    //    page: resultado.page ?? 1,

    //    page_size: resultado.page_size ?? 10,

    //    total: resultado.total ?? 0,

    //    total_pages: resultado.total_pages ?? 1

    //});

    tablaCompras.actualizarDesdeBackend(resultado);

}

function renderizarPaginacion() {

    const info =
        tablaCompras.getElemento("info");
    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    // document.getElementById("infoPaginacionCompras");

    const resumen =
        tablaCompras.getElemento("resumen");
    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    //  document.getElementById("resumenPaginacionCompras");

    const btnAnterior =
        tablaCompras.getElemento("btnAnterior");
    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    // document.getElementById("btnPaginaAnterior");

    const btnSiguiente =
        tablaCompras.getElemento("btnSiguiente");
    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    //  document.getElementById("btnPaginaSiguiente");

    if (!info || !btnAnterior || !btnSiguiente) {
        return;
    }

    // ELIMINAR DESPUES DE LA IMPORTACION DE TABLAS.JS
    //info.textContent =
    //    `Página ${estadoPaginacion.page} de ${estadoPaginacion.total_pages}`;

    info.textContent =
        `Página ${tablaCompras.page} de ${tablaCompras.totalPages}`;

    if (resumen) {

        // ELIMINAR DESPUES DE LA IMPORTACION DE TABLAS.JS
        //const inicio = estadoPaginacion.total === 0
        //    ? 0
        //    : ((estadoPaginacion.page - 1) * estadoPaginacion.page_size) + 1;

        //const fin = Math.min(
        //    estadoPaginacion.page * estadoPaginacion.page_size,
        //    estadoPaginacion.total
        //);

        //resumen.textContent =
        //    `Mostrando ${inicio}-${fin} de ${estadoPaginacion.total} compras`;
        const inicio = tablaCompras.total === 0
            ? 0
            : ((tablaCompras.page - 1) * tablaCompras.pageSize) + 1;

        const fin = Math.min(
            tablaCompras.page * tablaCompras.pageSize,
            tablaCompras.total
        );

        resumen.textContent =
            `Mostrando ${inicio}-${fin} de ${tablaCompras.total} compras`;

    }

    // ELIMINAR DESPUES DE LA IMPORTACION DE TABLA.JS
    //btnAnterior.disabled =
    //    estadoPaginacion.page <= 1;

    //btnSiguiente.disabled =
    //    estadoPaginacion.page >= estadoPaginacion.total_pages;

    btnAnterior.disabled =
        tablaCompras.page <= 1;

    btnSiguiente.disabled =
        tablaCompras.page >= tablaCompras.totalPages;

    renderizarNumerosPaginacion();

    actualizarIndicadoresOrden();

}

function inicializarPaginacion() {

    const btnAnterior =
        document.getElementById("btnPaginaAnterior");

    const btnSiguiente =
        document.getElementById("btnPaginaSiguiente");

    if (btnAnterior) {

        btnAnterior.addEventListener(
            "click",
            () => {

                //if (/*estadoPaginacion.page*/tablaCompras.page <= 1) {
                //    return;
                //}

                // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
                // estadoPaginacion.page--;
                tablaCompras.paginaAnterior();

                //cargarCompras();

            }
        );

    }

    if (btnSiguiente) {

        btnSiguiente.addEventListener(
            "click",
            () => {

                //if (
                //    /*estadoPaginacion.page*/tablaCompras.page >=
                //    /*estadoPaginacion.total_pages*/tablaCompras.totalPages
                //) {
                //    return;
                //}

                // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
                // estadoPaginacion.page++;
                tablaCompras.paginaSiguiente();

                //cargarCompras();

            }
        );

    }

}

function inicializarPageSize() {

    // ELIMINAR DESPUES DE IMPORTAR TABLAS.JS
    // const select =
    //    document.getElementById("pageSizeCompras");

    //if (!select) return;

    //select.value = estadoPaginacion.page_size;

    //select.addEventListener("change", () => {

    //    estadoPaginacion.page_size = Number(select.value);

    //    localStorage.setItem(
    //        STORAGE_PAGE_SIZE,
    //        estadoPaginacion.page_size
    //    );

    //    estadoPaginacion.page = 1;

    //    cargarCompras();

    //});

    const select = document.getElementById("pageSizeCompras");

    if (!select) return;

    select.value = tablaCompras.pageSize;

    select.addEventListener("change", () => {

        tablaCompras.cambiarPageSize(
            Number(select.value)
        );

        localStorage.setItem(
            STORAGE_PAGE_SIZE,
            tablaCompras.pageSize
        );

    });

}

function renderizarNumerosPaginacion() {

    // ELIMINAR DESPUES DE LA IMPORTACION DE TABLA.JS
    //console.log("Estado paginación:", estadoPaginacion);

    console.log(
        "Estado TablaUI:",
        tablaCompras.getEstado()
    );

    const contenedor = document.getElementById("numerosPaginacion");

    if (!contenedor) return;

    contenedor.innerHTML = "";

    // ELIMINAR DESPUES DE LA IMPORTACION DE TABLAS.JS
    //const total = estadoPaginacion.total_pages;
    //const actual = estadoPaginacion.page;

    const total = tablaCompras.totalPages;

    const actual = tablaCompras.page;

    console.log("Total páginas:", total);
    console.log("Página actual:", actual);

    if (total <= 1) return;

    function crearBoton(pagina) {

        console.log("Creando botón:", pagina);

        const boton = document.createElement("button");

        boton.type = "button";

        boton.className = "pg-btn";

        boton.textContent = pagina;

        if (pagina === actual) {
            boton.classList.add("pg-btn-active");
        }

        boton.addEventListener("click", () => {

            if (pagina === actual) return;

            // ELIMINAR DESPUES DE LA IMPORTACION DE TABLAS.JS
            // estadoPaginacion.page = pagina;

            //tablaCompras.setPage(pagina);

            //cargarCompras();

            tablaCompras.irAPagina(pagina);

        });

        contenedor.appendChild(boton);

    }

    function crearPuntos() {

        const span = document.createElement("span");

        span.className = "pg-dots";

        span.textContent = "...";

        contenedor.appendChild(span);

    }

    // ===== Hasta 7 páginas =====

    if (total <= 7) {

        for (let i = 1; i <= total; i++) {
            crearBoton(i);
        }

        return;

    }

    // ===== Inicio =====

    if (actual <= 4) {

        for (let i = 1; i <= 5; i++) {
            crearBoton(i);
        }

        crearPuntos();

        crearBoton(total);

        return;

    }

    // ===== Final =====

    if (actual >= total - 3) {

        crearBoton(1);

        crearPuntos();

        for (let i = total - 4; i <= total; i++) {
            crearBoton(i);
        }

        return;

    }

    // ===== Centro =====

    crearBoton(1);

    crearPuntos();

    for (let i = actual - 1; i <= actual + 1; i++) {
        crearBoton(i);
    }

    crearPuntos();

    crearBoton(total);

}

// =============================
window.verDetalle = async function (id) {

    try {

        const res = await apiFetch(`/compras/${id}`);

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando detalle ❌", "error");
            return;
        }

        const modal = document.getElementById("modalCompra");
        const body = document.getElementById("modalBody");

        body.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Precio</th>
                        <th>Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    ${(res.data || []).map(d => `
                        <tr>
                            <td>${d.nombre}</td>
                            <td>${d.cantidad}</td>
                            <td>${formatoMoneda(d.precio_unitario)}</td>
                            <td>${formatoMoneda(d.cantidad * d.precio_unitario)}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;

        modal.classList.remove("hidden");

    } catch (error) {
        console.error("Error detalle:", error);
        mostrarMensaje("Error cargando detalle ❌", "error");
    }
};

window.cerrarModal = function () {
    document.getElementById("modalCompra").classList.add("hidden");
};

document.addEventListener("click", function (e) {

    const modal = document.getElementById("modalCompra");

    if (!modal) return;

    if (e.target === modal) {
        modal.classList.add("hidden");
    }
});

document.addEventListener("keydown", function (e) {
    if (e.key === "Escape") {
        cerrarModal();
    }
});


// =============================
function formatearFecha(fecha) {

    if (!fecha) return "";

    try {

        return new Intl.DateTimeFormat("es-CO", {
            timeZone: "America/Bogota",
            year: "numeric",
            month: "2-digit",
            day: "2-digit",
            hour: "2-digit",
            minute: "2-digit",
            second: "2-digit",
            hour12: false
        }).format(new Date(fecha));

    } catch (error) {

        console.error("Error formateando fecha:", error);

        return fecha;
    }
}

/*
window.abrirModalCompra = function () {
    document
        .getElementById("modalNuevaCompra")
        .classList.remove("hidden");
};

window.cerrarModalCompra = function () {
    document
        .getElementById("modalNuevaCompra")
        .classList.add("hidden");
};
*/
window.mostrarFormularioCompra = function () {

    document.getElementById("compraFormContainer")
        .classList.remove("hidden");

    document.getElementById("listContainer")
        .classList.add("hidden");

    document.getElementById("formTitle").textContent =
        "Nueva Compra";

    limpiarFormularioCompra();

}

window.cancelarCompra = function () {

    document.getElementById("compraFormContainer")
        .classList.add("hidden");

    document.getElementById("listContainer")
        .classList.remove("hidden");

}

function limpiarFormularioCompra() {

    document.getElementById("compraForm").reset();

    proveedorSeleccionado = null;

    document.getElementById("proveedorBusqueda").value = "";

    document.getElementById("proveedorId").value = "";

    document.getElementById("productosContainer").innerHTML = "";

    document.getElementById("subtotalCompra").textContent = formatoMoneda(0);

    document.getElementById("ivaCompra").textContent = formatoMoneda(0);

    document.getElementById("totalCompra").textContent = formatoMoneda(0);

    inicializarFechaCompra();

}