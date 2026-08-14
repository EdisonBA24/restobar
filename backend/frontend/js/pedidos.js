import { apiFetch, API_URL } from "./api.js";
import { TablaUI } from "./tablas.js";

const STORAGE_PAGE_SIZE = "pedidos_page_size";

let tablaPedidos = null;

const filtrosPedidos = {

    periodo: "mes_actual",

    fecha_inicio: "",

    fecha_fin: "",

    estado: "",

    servicio: "",

    buscar: ""

};

let productos = [];
let modo = "";
let pedidoActual = null;
let detallePedidoActual = [];
let clientePedidoActual = "";
let mesaPedidoActual = "";
let servicioPedidoActual = "";
let tipoPedidoActual = "";

document.addEventListener("DOMContentLoaded", async () => {

    if (document.getElementById("productosPedido")) {

        modo = "crear";

        await cargarProductos();

        inicializarAutocompleteClientes();

    }

    if (document.getElementById("tablaPedidos")) {

        modo = "consultar";

        tablaPedidos = new TablaUI({

            nombre: "pedidos",

            callback: () => cargarPedidos(),

            tabla: "#tablaPedidosTabla",

            pageSize: "#pageSizePedidos",

            btnAnterior: "#btnPaginaAnterior",

            btnSiguiente: "#btnPaginaSiguiente",

            numeros: "#numerosPaginacion",

            resumen: "#resumenPaginacionPedidos",

            info: "#infoPaginacionPedidos"

        }).init();

        inicializarFiltrosPedidos();

        inicializarExportacionPedidos();

        inicializarOrdenamientoPedidos();

        inicializarAutoCompleteClientes();

        cargarPedidos();

    }

    document
        .getElementById("btnFacturar")
        ?.addEventListener("click", facturarPedido);

    document
        .getElementById("btnImprimirComanda")
        ?.addEventListener("click", imprimirComanda);

});

function inicializarAutoCompleteClientes() {

    const input = document.getElementById("cliente");

    if (input) {

        cargarClientesAutocomplete();

        input.addEventListener("input", function () {

            const valor = this.value.toLowerCase();
            const lista = document.getElementById("listaClientes");

            this.dataset.id = ""; // 🔥 FIX

            if (!valor) {
                lista.classList.add("hidden");
                return;
            }

            const filtrados = clientesCache.filter(c =>
                (c.nombre || "").toLowerCase().includes(valor) ||
                (c.documento || "").toLowerCase().includes(valor)
            );

            if (filtrados.length === 0) {

                lista.innerHTML = `
                    <div class="item-cliente no-result">
                        Cliente no encontrado
                    </div>
                    <div class="item-cliente crear-nuevo"
                        onclick="abrirCrearCliente()">
                        ➕ Crear cliente nuevo
                    </div>
                `;

            } else {

                lista.innerHTML = filtrados.map(c => `
                    <div class="item-cliente"
                        onclick="seleccionarCliente('${c.nombre}', ${c.id})">
                        ${c.nombre} - ${c.documento || ""}
                    </div>
                `).join("");
            }

            lista.classList.remove("hidden");
        });
    }
}

// =============================
// CARGAR PRODUCTOS
// =============================
async function cargarProductos() {

    const categoria = document.body.dataset.categoria;

    const res = await apiFetch("/productos?page=1&limit=100&inactivos=false");

    productos = res.data.filter(p =>
        p.tipo === "RECETA" &&
        (!categoria || p.categoria === categoria)
    );
}

// =============================
// AGREGAR PRODUCTO
// =============================
window.agregarProducto = function () {

    const container = document.getElementById("productosPedido");
    const mensaje = document.getElementById("mensajeVacio");

    if (mensaje) mensaje.style.display = "none";

    const row = document.createElement("div");
    row.className = "compra-item";

    row.innerHTML = `
        <select class="producto">
            ${productos.map(p => `
                <option value="${p.id}" data-precio="${p.precio_venta}">
                    ${p.nombre}
                </option>
            `).join("")}
        </select>

        <input type="number" class="cantidad" placeholder="0">
        <input type="number" class="precio" readonly>
        <div class="subtotal">$0</div>
        <button class="btn-remove">✖</button>
    `;

    const select = row.querySelector(".producto");
    const precioInput = row.querySelector(".precio");
    const cantidadInput = row.querySelector(".cantidad");

    const actualizar = () => {
        const option = select.options[select.selectedIndex];
        const precio = parseFloat(option.dataset.precio || 0);
        const cantidad = parseFloat(cantidadInput.value) || 0;

        precioInput.value = precio;

        const subtotal = precio * cantidad;
        row.querySelector(".subtotal").innerText = formatoMoneda(subtotal);

        calcularTotal();
    };

    select.addEventListener("change", actualizar);
    cantidadInput.addEventListener("input", actualizar);

    row.querySelector(".btn-remove").onclick = () => {
        row.remove();
        calcularTotal();
    };

    actualizar();
    container.appendChild(row);
};

// =============================
function calcularTotal() {

    let total = 0;

    document.querySelectorAll(".compra-item").forEach(row => {

        const cantidad = parseFloat(row.querySelector(".cantidad").value) || 0;
        const precio = parseFloat(row.querySelector(".precio").value) || 0;

        total += cantidad * precio;
    });

    document.getElementById("totalPedido").innerText = formatoMoneda(total);
}

// =============================
// GUARDAR PEDIDO (🔥 FIX)
// =============================
window.guardarPedido = async function () {

    const filas = document.querySelectorAll(".compra-item");

    if (filas.length === 0) {
        mostrarMensaje("Agrega productos ⚠️", "warning");
        return;
    }

    let detalles = [];

    for (let f of filas) {

        const cantidad = parseFloat(f.querySelector(".cantidad").value);
        const precio = parseFloat(f.querySelector(".precio").value);

        if (cantidad <= 0 || precio <= 0) {
            mostrarMensaje("Datos inválidos ⚠️", "warning");
            return;
        }

        detalles.push({
            producto_id: f.querySelector(".producto").value,
            cantidad,
            precio
        });
    }

    try {

        const categoriaPedido =
            document.body.dataset.categoria || "";

        const res = await apiFetch("/pedidos", "POST", {
            mesa: document.getElementById("mesa")?.value || "General",
            tipo: document.getElementById("tipoServicio")?.value || "MESA",
            categoria: categoriaPedido,
            cliente: document.getElementById("cliente")?.value || "General",
            cliente_id: document.getElementById("cliente")?.dataset.id || null,
            estado: "pendiente",
            detalles
        });

        if (res.status === "error") {
            mostrarMensaje(res.message, "error");
            return;
        }

        mostrarMensaje("Pedido registrado ✅", "success");

        // Redirigir a la lista de pedidos después de 1 segundo
        setTimeout(() => {
            window.location.href = "../pages/pedidos.html";
        }, 1000);

        document.getElementById("productosPedido").innerHTML = "";
        document.getElementById("totalPedido").innerText = "$0";

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error en pedido ❌", "error");
    }
};

// =============================
// CONSULTAR PEDIDOS
// =============================
async function cargarPedidos() {

    try {

        const estadoTabla = tablaPedidos
            ? tablaPedidos.getEstado()
            : {
                page: 1,
                page_size: 10,
                sort_by: "id",
                sort_order: "desc"
            };

        const params = new URLSearchParams({

            page: estadoTabla.page,

            page_size: estadoTabla.page_size,

            sort_by: estadoTabla.sort_by,

            sort_order: estadoTabla.sort_order,

            periodo: filtrosPedidos.periodo,

            fecha_inicio: filtrosPedidos.fecha_inicio,

            fecha_fin: filtrosPedidos.fecha_fin,

            estado: filtrosPedidos.estado,

            servicio: filtrosPedidos.servicio,

            buscar: filtrosPedidos.buscar

        });

        const res = await apiFetch(

            `/pedidos?${params.toString()}`

        );

        if (!res || res.status === "error") {

            mostrarMensaje(

                res?.message || "Error consultando pedidos",

                "error"

            );

            return;

        }

        //const tabla = document.getElementById("tablaPedidos");

        //tabla.innerHTML = "";

        //(res.data || []).forEach(pedido => {

        //    tabla.appendChild(

        //        crearFilaPedido(pedido)

        //    );

        //});
        const tabla = document.getElementById("tablaPedidos");

        tabla.innerHTML = "";

        const pedidos = res.data?.items || [];

        pedidos.forEach(pedido => {

            tabla.appendChild(

                crearFilaPedido(pedido)

            );

        });

        // =============================
        // KPIs
        // =============================
        await cargarKPIsPedidos();

        if (tablaPedidos) {

            /*
            tablaPedidos.actualizarDesdeBackend({

                page: res.page ?? estadoTabla.page,

                page_size: res.page_size ?? estadoTabla.page_size,

                total: res.total ?? res.data.length,

                total_pages: res.total_pages ?? 1,

                sort_by: res.sort_by ?? estadoTabla.sort_by,

                sort_order: res.sort_order ?? estadoTabla.sort_order

            });
            */
            const pag = res.data?.pagination || {};

            tablaPedidos.actualizarDesdeBackend({

                page: pag.page ?? estadoTabla.page,

                page_size: pag.page_size ?? estadoTabla.page_size,

                total: pag.total ?? 0,

                total_pages: pag.total_pages ?? 1,

                sort_by: estadoTabla.sort_by,

                sort_order: estadoTabla.sort_order

            });

        }

    }
    catch (error) {

        console.error(error);

        mostrarMensaje(

            "Error cargando pedidos",

            "error"

        );

    }

}

async function cargarKPIsPedidos() {

    const filtros = obtenerFiltrosPedidos();

    const params = new URLSearchParams({

        periodo: filtros.periodo,

        fecha_inicio: filtros.fecha_inicio,

        fecha_fin: filtros.fecha_fin,

        estado: filtros.estado,

        servicio: filtros.servicio,

        buscar: filtros.buscar

    });

    const res = await apiFetch(

        `/pedidos/kpis?${params}`

    );

    if (!res || res.status === "error")
        return;

    actualizarKPIsPedidos(res.data);

}

// ======================================
// KPIs
// ======================================

function actualizarKPIsPedidos(res) {

    const kpis = res || {};

    const pendientes =
        Number(kpis.pendientes ?? 0);

    const facturados =
        Number(kpis.facturados ?? 0);

    const ventasDia =
        Number(kpis.ventas_dia ?? 0);

    const ticketPromedio =
        Number(kpis.ticket_promedio ?? 0);

    actualizarTexto("kpiPendientes", pendientes);

    actualizarTexto("kpiFacturados", facturados);

    actualizarTexto(
        "kpiVentasDia",
        formatoMoneda(ventasDia)
    );

    actualizarTexto(
        "kpiTicketPromedio",
        formatoMoneda(ticketPromedio)
    );

}

// =======================================================
// EXPORTAR EXCEL
// =======================================================

function inicializarExportacionPedidos() {

    const btn = document.getElementById("btnExportarExcel");

    if (!btn)
        return;

    btn.addEventListener(

        "click",

        exportarPedidosExcel

    );

}

// =====================================================
// 📊 EXPORTAR PEDIDOS A EXCEL
// =====================================================

async function exportarPedidosExcel() {

    try {

        // ==========================================
        // OBTENER FILTROS ACTUALES
        // ==========================================

        const params = new URLSearchParams();

        params.append(
            "periodo",
            document.getElementById(
                "filtroPeriodo"
            )?.value || ""
        );

        params.append(
            "fecha_inicio",
            document.getElementById(
                "fechaInicio"
            )?.value || ""
        );

        params.append(
            "fecha_fin",
            document.getElementById(
                "fechaFin"
            )?.value || ""
        );

        params.append(
            "estado",
            document.getElementById(
                "filtroEstado"
            )?.value || ""
        );

        params.append(
            "servicio",
            document.getElementById(
                "filtroServicio"
            )?.value || ""
        );

        params.append(
            "buscar",
            document.getElementById(
                "buscarPedido"
            )?.value || ""
        );

        // ==========================================
        // URL
        // ==========================================

        const url =
            `${API_URL}/pedidos/exportar?${params.toString()}`;

        console.log(
            "📊 EXPORTAR PEDIDOS:"
        );

        console.log(
            Object.fromEntries(
                params.entries()
            )
        );

        // ==========================================
        // SOLICITUD
        // ==========================================

        const response = await fetch(
            url,
            {
                method: "GET",
                credentials: "include"
            }
        );

        // ==========================================
        // VALIDAR RESPUESTA
        // ==========================================

        if (!response.ok) {

            let mensaje =
                "No fue posible generar el Excel.";

            try {

                const error =
                    await response.json();

                mensaje =
                    error.message ||
                    mensaje;

            } catch (_) {

                // La respuesta no era JSON.
            }

            throw new Error(
                mensaje
            );
        }

        // ==========================================
        // CONVERTIR A BLOB
        // ==========================================

        const blob =
            await response.blob();

        // ==========================================
        // OBTENER NOMBRE DEL ARCHIVO
        // ==========================================

        let nombreArchivo =
            "Reporte_Pedidos.xlsx";

        const disposition =
            response.headers.get(
                "Content-Disposition"
            );

        if (disposition) {

            const match =
                disposition.match(
                    /filename="?([^"]+)"?/i
                );

            if (match && match[1]) {

                nombreArchivo =
                    match[1];

            }

        }

        // ==========================================
        // DESCARGAR
        // ==========================================

        const urlBlob =
            window.URL.createObjectURL(
                blob
            );

        const enlace =
            document.createElement(
                "a"
            );

        enlace.href =
            urlBlob;

        enlace.download =
            nombreArchivo;

        document.body.appendChild(
            enlace
        );

        enlace.click();

        enlace.remove();

        window.URL.revokeObjectURL(
            urlBlob
        );

        // ==========================================
        // MENSAJE ÉXITO
        // ==========================================

        if (
            typeof mostrarToast ===
            "function"
        ) {

            mostrarToast(
                "Reporte de pedidos exportado correctamente.",
                "success"
            );

        } else {

            console.log(
                "✅ Reporte de pedidos exportado correctamente."
            );

        }

    } catch (error) {

        console.error(
            "❌ ERROR EXPORTAR PEDIDOS:",
            error
        );

        if (
            typeof mostrarToast ===
            "function"
        ) {

            mostrarToast(
                error.message ||
                "No fue posible exportar los pedidos.",
                "error"
            );

        } else {

            alert(
                error.message ||
                "No fue posible exportar los pedidos."
            );

        }

    }

}

function actualizarTexto(id, valor) {

    const elemento = document.getElementById(id);

    if (!elemento) return;

    elemento.textContent = valor;

}

function crearFilaPedido(pedido) {

    const tr = document.createElement("tr");

    tr.style.cursor = "pointer";

    tr.onclick = () =>

        verDetallePedido(

            pedido.id,

            pedido.estado,

            pedido.categoria || ""

        );

    const badgeEstado =

        pedido.estado === "facturado"

            ? '<span class="badge-success">FACTURADO</span>'

            : '<span class="badge-warning">PENDIENTE</span>';

    tr.innerHTML = `

        <td style="text-align:center">

            ${pedido.id}

        </td>

        <td>

            ${pedido.tipo || ""}

        </td>

        <td>

            ${pedido.mesa || "-"}

        </td>

        <td>

            ${pedido.cliente || "GENERAL"}

        </td>

        <td>

            ${formatearFecha(pedido.fecha)}

        </td>

        <td style="text-align:right">

            ${formatoMoneda(pedido.total)}

        </td>

        <td style="text-align:center">

            ${badgeEstado}

        </td>

        <td style="text-align:center">

            <button
                class="btn-table"
                onclick="event.stopPropagation();
                verDetallePedido(
                    ${pedido.id},
                    '${pedido.estado}',
                    '${pedido.categoria || ""}'
                );">

                👁

            </button>

        </td>

    `;

    return tr;

}

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

function inicializarFiltrosPedidos() {

    const periodo = document.getElementById("filtroPeriodo");
    const estado = document.getElementById("filtroEstado");
    const servicio = document.getElementById("filtroServicio");
    const buscar = document.getElementById("buscarPedido");
    const fechaInicio = document.getElementById("fechaInicio");
    const fechaFin = document.getElementById("fechaFin");
    const limpiar = document.getElementById("btnLimpiarFiltros");

    if (periodo)
        periodo.addEventListener("change", actualizarPeriodoPedidos);

    if (estado)
        estado.addEventListener("change", actualizarConsultaPedidos);

    if (servicio)
        servicio.addEventListener("change", actualizarConsultaPedidos);

    if (buscar) {

        let timeoutBusqueda = null;

        buscar.addEventListener("input", () => {

            clearTimeout(timeoutBusqueda);

            timeoutBusqueda = setTimeout(() => {

                actualizarConsultaPedidos();

            }, 400);

        });

    }

    if (fechaInicio)
        fechaInicio.addEventListener("change", actualizarConsultaPedidos);

    if (fechaFin)
        fechaFin.addEventListener("change", actualizarConsultaPedidos);

    if (limpiar)
        limpiar.addEventListener("click", limpiarFiltrosPedidos);

    actualizarPeriodoPedidos();

}

function obtenerFiltrosPedidos() {

    filtrosPedidos.periodo =
        document.getElementById("filtroPeriodo")?.value || "mes_actual";

    filtrosPedidos.estado =
        document.getElementById("filtroEstado")?.value || "";

    filtrosPedidos.servicio =
        document.getElementById("filtroServicio")?.value || "";

    filtrosPedidos.buscar =
        document.getElementById("buscarPedido")?.value.trim() || "";

    filtrosPedidos.fecha_inicio =
        document.getElementById("fechaInicio")?.value || "";

    filtrosPedidos.fecha_fin =
        document.getElementById("fechaFin")?.value || "";

    return { ...filtrosPedidos };

}

function actualizarPeriodoPedidos() {

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

    actualizarConsultaPedidos();

}

function actualizarConsultaPedidos() {

    obtenerFiltrosPedidos();

    if (tablaPedidos) {

        tablaPedidos.reiniciarPaginacion();

    }

    cargarPedidos();

}

function limpiarFiltrosPedidos() {

    document.getElementById("filtroPeriodo").value = "mes_actual";
    document.getElementById("filtroEstado").value = "";
    document.getElementById("filtroServicio").value = "";
    document.getElementById("buscarPedido").value = "";

    document.getElementById("fechaInicio").value = "";
    document.getElementById("fechaFin").value = "";

    actualizarPeriodoPedidos();

    actualizarConsultaPedidos();

}


function inicializarOrdenamientoPedidos() {

    if (!tablaPedidos)
        return;

    tablaPedidos.renderizar();

}

// =============================
// DETALLE
// =============================
window.verDetallePedido = async function (id, estado, tipo) {

    pedidoActual = id;
    window.metodoSeleccionado = null;

    const res = await apiFetch(`/pedidos/${id}`);

    detallePedidoActual = res.data.detalle || [];

    clientePedidoActual =
        res.data.pedido?.cliente || "GENERAL";

    mesaPedidoActual =
        res.data.pedido?.mesa || "";

    servicioPedidoActual =
        res.data.pedido?.tipo || "";

    tipoPedidoActual =
        String(
            res.data.pedido?.categoria ||
            tipo ||
            ""
        )
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .trim()
            .toUpperCase();

    const modal = document.getElementById("modalCompra");
    const body = document.getElementById("modalBody");
    const btnFacturar = document.getElementById("btnFacturar");
    const btnComanda = document.getElementById("btnImprimirComanda");

    // ======================================
    // ENCABEZADO
    // ======================================

    document.getElementById("detallePedidoNumero").textContent =
        `#${id}`;

    document.getElementById("detallePedidoEstado").textContent =
        estado;

    document.getElementById("detallePedidoFecha").textContent =
        formatearFecha(
            res.data.pedido?.fecha
        );

    // ======================================
    // CLIENTE
    // ======================================

    document.getElementById("detalleCliente").textContent =
        clientePedidoActual || "GENERAL";

    document.getElementById("detalleServicio").textContent =
        servicioPedidoActual || "-";

    document.getElementById("detalleMesa").textContent =
        mesaPedidoActual || "-";

    // ======================================
    // DETALLE
    // ======================================

    //renderizarDetallePedido();
    renderDetallePedido(detallePedidoActual);

    // ======================================
    // TOTAL
    // ======================================

    const total = detallePedidoActual.reduce(

        (sum, item) =>

            sum +

            (Number(item.cantidad) *

                Number(item.precio)),

        0

    );

    document.getElementById("detalleTotalPedido").textContent =

        formatoMoneda(total);

    /*
    if (btnFacturar) {
        btnFacturar.style.display =
            estado === "facturado"
                ? "none"
                : "inline-block";
    }
    */
    btnFacturar.classList.toggle(

        "hidden",

        estado.toUpperCase() === "FACTURADO"

    );

    if (btnComanda) {

        const tiposConComanda = [
            "DESAYUNOS",
            "ALMUERZOS",
            "COMIDAS RAPIDAS"
        ];

        const mostrarComanda =
            tiposConComanda.includes(tipoPedidoActual);

        btnComanda.classList.remove("hidden");

        btnComanda.style.display =
            mostrarComanda
                ? "inline-flex"
                : "none";

        console.log(
            "🖨 COMANDA:",
            {
                tipoRecibido: tipo,
                categoriaBackend: res.data.pedido?.categoria,
                tipoPedidoActual,
                mostrarComanda
            }
        );
    }

    modal.classList.remove("hidden");
};

function renderDetallePedido(detalle) {

    const contenedor =
        document.getElementById("detalleItemsPedido");

    if (!contenedor) return;

    contenedor.innerHTML = "";

    if (!detalle || detalle.length === 0) {

        contenedor.innerHTML = `
            <div class="pedido-productos-vacio">

                <div class="pedido-productos-vacio-icon">
                    🍽️
                </div>

                <strong>
                    No existen productos en este pedido
                </strong>

                <span>
                    El pedido no tiene productos registrados.
                </span>

            </div>
        `;

        const totalElemento =
            document.getElementById("detalleTotalPedido");

        if (totalElemento) {
            totalElemento.textContent =
                formatoMoneda(0);
        }

        return;
    }

    let total = 0;

    detalle.forEach((item, index) => {

        const cantidad =
            Number(item.cantidad || 0);

        const precio =
            Number(item.precio || 0);

        const subtotal =
            Number(
                item.subtotal ??
                (cantidad * precio)
            );

        total += subtotal;

        const card =
            document.createElement("article");

        card.className =
            "detalle-item-card";

        const tipo =
            (item.tipo || "PRODUCTO")
                .toString()
                .toUpperCase();

        let componentes = "";

        if (
            Array.isArray(item.componentes) &&
            item.componentes.length > 0
        ) {

            componentes = `
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
                                Componentes de la receta
                            </small>
                        </div>

                    </div>

                    <div class="detalle-componentes-list">

                        ${item.componentes.map(c => `
                            
                            <div class="detalle-componente">

                                <span class="detalle-componente-categoria">
                                    ${c.categoria || "COMPONENTE"}
                                </span>

                                <strong>
                                    ${c.nombre || "-"}
                                </strong>

                            </div>

                        `).join("")}

                    </div>

                </div>
            `;
        }

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
                                    ${item.nombre || "Producto"}
                                </strong>

                                <span class="badge-detalle">
                                    ${tipo}
                                </span>

                            </div>

                            <span class="detalle-item-description">
                                Producto incluido en el pedido
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


                <!-- INFORMACIÓN DEL PRODUCTO -->
                <div class="detalle-item-data">

                    <div class="detalle-item-data-box">

                        <span>
                            📦 Cantidad
                        </span>

                        <strong>
                            ${cantidad}
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


                <!-- COMPONENTES DE LA RECETA -->
                ${componentes}

            </div>
        `;

        contenedor.appendChild(card);

    });


    const totalElemento =
        document.getElementById("detalleTotalPedido");

    if (totalElemento) {

        totalElemento.textContent =
            formatoMoneda(total);

    }

}

/*
function renderizarDetallePedido() {

    const contenedor =
        document.getElementById(
            "detalleItemsPedido"
        );

    if (!contenedor)
        return;

    contenedor.innerHTML = "";

    if (!detallePedidoActual.length) {

        contenedor.innerHTML = `

            <div class="empty-state">

                No existen productos en este pedido.

            </div>

        `;

        return;

    }

    detallePedidoActual.forEach(item => {

        contenedor.appendChild(

            crearCardDetalle(item)

        );

    });

}
    */

function crearCardDetalle(item) {

    const card = document.createElement("div");

    card.className = "detalle-producto";

    card.innerHTML = `

        <div class="detalle-producto-header">

            <div>

                <h4>

                    ${item.nombre}

                </h4>

                <small>

                    Cantidad:

                    ${item.cantidad}

                </small>

            </div>

            <div class="detalle-producto-total">

                ${formatoMoneda(

        Number(item.precio) *

        Number(item.cantidad)

    )}

            </div>

        </div>

        <div class="detalle-producto-body">

            <div>

                Precio unitario

            </div>

            <strong>

                ${formatoMoneda(item.precio)}

            </strong>

        </div>

    `;

    return card;

}

// =============================
// FACTURAR (🔥 FIX)
// =============================
async function facturarPedido() {

    if (!pedidoActual) return;

    if (!window.metodoSeleccionado) {
        if (typeof abrirModalPago === "function") {
            abrirModalPago();
        } else {
            mostrarMensaje("Selecciona método de pago ⚠️", "warning");
        }
        return;
    }

    try {

        const data = await apiFetch(`/pedidos/${pedidoActual}/facturar`, "POST", {
            metodo_pago: window.metodoSeleccionado
        });

        if (data.status === "error") {
            mostrarMensaje(data.message, "error");
            return;
        }

        mostrarMensaje("Pedido facturado correctamente ✅", "success");

        document.getElementById("modalCompra").classList.add("hidden");

        window.metodoSeleccionado = null;

        if (modo === "consultar") {
            cargarPedidos();
        }

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error al facturar ❌", "error");
    }
}

// =============================
// TODO LO DEMÁS SE DEJA EXACTAMENTE IGUAL
// (clientes autocomplete, utilidades, etc.)
// =============================

// =============================
// UTILIDADES
// =============================
function formatoMoneda(v) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(v || 0);
}

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

function mostrarMensaje(msg, tipo = "success") {

    document
        .querySelectorAll(".toast")
        .forEach(t => t.remove());

    const iconos = {

        success: "✅",

        warning: "⚠",

        error: "❌",

        info: "ℹ"

    };

    const tiempos = {

        success: 3000,

        info: 4000,

        warning: 6000,

        error: 8000

    };

    const toast = document.createElement("div");

    toast.className = `toast ${tipo}`;

    toast.innerHTML = `${iconos[tipo] || ""} ${msg}`;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {

        toast.classList.add("show");

    });

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => toast.remove(), 300);

    }, tiempos[tipo] || 4000);

}

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

window.metodoSeleccionado = null;

// =============================
// 🔥 AUTOCOMPLETE CLIENTES (FIX REAL)
// =============================
let clientesCache = [];

async function cargarClientesAutocomplete() {
    const res = await apiFetch("/clientes?page=1&limit=100");
    clientesCache = res.data || [];
}

// =============================
// 🔥 GUARDAR CLIENTE RÁPIDO (FIX)
// =============================
window.guardarClienteRapido = async function () {

    const nombre = document.getElementById("nuevoNombre")?.value;
    const documento = document.getElementById("nuevoDocumento")?.value;
    const telefono = document.getElementById("nuevoTelefono")?.value;
    const direccion = document.getElementById("nuevoDireccion")?.value;
    const duplicado = validarClienteDuplicado();

    if (duplicado) {
        const confirmar = confirm(
            `El cliente ya existe (${duplicado.nombre}). ¿Deseas continuar?`
        );

        if (!confirmar) return;
    }

    if (!nombre) {
        mostrarMensaje("El nombre es obligatorio ⚠️", "warning");
        return;
    }

    const data = {
        nombre,
        documento,
        telefono,
        direccion
    };

    try {

        const res = await apiFetch("/clientes", "POST", data);

        if (res.status === "error") {
            mostrarMensaje(res.message || "Error creando cliente ❌", "error");
            return;
        }

        mostrarMensaje("Cliente creado correctamente ✅", "success");

        // 🔥 recargar cache
        await cargarClientesAutocomplete();

        // 🔥 buscar cliente recién creado (por nombre)
        const nuevo = clientesCache.find(c =>
            (c.nombre || "").toLowerCase() === nombre.toLowerCase()
        );

        if (nuevo) {
            seleccionarCliente(nuevo.nombre, nuevo.id);
        } else {
            // fallback si no lo encuentra
            document.getElementById("cliente").value = nombre;
        }

        cerrarModalCliente();

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error al guardar cliente ❌", "error");
    }
};

window.abrirCrearCliente = function () {

    const nombre = document.getElementById("cliente").value;

    document.getElementById("nuevoNombre").value = nombre;

    document.getElementById("modalCliente").classList.remove("hidden");
};

window.cerrarModalCliente = function () {
    document.getElementById("modalCliente").classList.add("hidden");
};

// =============================
// 🔥 VALIDAR CLIENTE DUPLICADO
// =============================
function validarClienteDuplicado() {

    const nombre = document.getElementById("nuevoNombre")?.value.toLowerCase();
    const documento = document.getElementById("nuevoDocumento")?.value;

    if (!nombre && !documento) return;

    const duplicado = clientesCache.find(c =>
        (nombre && (c.nombre || "").toLowerCase() === nombre) ||
        (documento && (c.documento || "") === documento)
    );

    const warning = document.getElementById("warningCliente");

    if (duplicado) {

        warning.innerHTML = `⚠️ Cliente ya existe: <b>${duplicado.nombre}</b>`;
        warning.classList.remove("hidden");

        return duplicado;

    } else {
        warning.classList.add("hidden");
        return null;
    }
}


// =============================
// IMPRIMIR COMANDA 80MM TERMICA
// =============================
// =============================
// IMPRIMIR COMANDA 80MM TERMICA
// =============================
function imprimirComanda() {

    const tipoNormalizado =
        String(tipoPedidoActual || "")
            .normalize("NFD")
            .replace(/[\u0300-\u036f]/g, "")
            .trim()
            .toUpperCase();

    const tiposPermitidos = [
        "DESAYUNOS",
        "ALMUERZOS",
        "COMIDAS RAPIDAS"
    ];

    if (!tiposPermitidos.includes(tipoNormalizado)) {

        mostrarMensaje(
            "Este pedido no requiere comanda",
            "warning"
        );

        return;
    }

    // ==========================================
    // SEGURIDAD PARA TEXTO HTML
    // ==========================================
    const escaparHtml = (valor) => {

        return String(valor ?? "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    };

    const fechaActual =
        new Date().toLocaleString();

    // ==========================================
    // HTML COMANDA
    // ==========================================
    let html = `
    <html>

    <head>

        <title>Comanda Cocina</title>

        <style>

            @page {
                size: 80mm auto;
                margin: 0;
            }

            * {
                box-sizing: border-box;
            }

            body {
                width: 72mm;
                margin: 0 auto;
                padding: 5px;

                font-family:
                    "Courier New",
                    monospace;

                font-size: 11px;
                line-height: 1.25;

                color: #000;
                background: #fff;
            }

            .titulo {
                text-align: center;

                font-size: 17px;
                font-weight: 900;

                margin-bottom: 2px;
            }

            .subtitulo {
                text-align: center;

                font-size: 10px;
                font-weight: bold;

                margin-bottom: 6px;
            }

            .linea {
                border-top: 1px dashed #000;

                margin: 6px 0;
            }

            .pedido {
                text-align: center;

                font-size: 18px;
                font-weight: 900;

                margin: 7px 0;
            }

            .info {
                margin: 3px 0;

                font-size: 11px;
                font-weight: bold;

                word-break: break-word;
            }

            .seccion {
                text-align: center;

                font-size: 11px;
                font-weight: 900;

                margin: 5px 0;
            }

            .producto {
                margin: 8px 0 10px 0;
            }

            .producto-cabecera {
                display: flex;

                align-items: flex-start;

                gap: 5px;

                font-size: 14px;
                font-weight: 900;
            }

            .cantidad {
                min-width: 30px;

                font-size: 15px;
                font-weight: 900;
            }

            .producto-nombre {
                flex: 1;

                word-break: break-word;
            }

            .componentes {
                margin-top: 4px;

                padding-left: 30px;
            }

            .componente {
                margin: 5px 0;

                font-size: 11px;
            }

            .componente-categoria {
                display: block;

                font-size: 9px;
                font-weight: bold;

                text-transform: uppercase;
            }

            .componente-nombre {
                display: block;

                padding-left: 5px;

                font-size: 11px;
                font-weight: bold;

                word-break: break-word;
            }

            .sin-componentes {
                margin-top: 3px;
                padding-left: 30px;

                font-size: 10px;
                font-style: italic;
            }

            .footer {
                text-align: center;

                font-size: 12px;
                font-weight: 900;

                margin-top: 10px;
                margin-bottom: 5px;
            }

            @media print {

                body {
                    width: 72mm;
                    margin: 0;
                    padding: 5px;
                }

            }

        </style>

    </head>

    <body>

        <!-- ========================== -->
        <!-- ENCABEZADO -->
        <!-- ========================== -->

        <div class="titulo">
            PARCHE EL ANTOJO
        </div>

        <div class="subtitulo">
            COMANDA DE COCINA
        </div>

        <div class="linea"></div>

        <div class="pedido">
            PEDIDO #${escaparHtml(pedidoActual)}
        </div>

        <div class="info">
            FECHA: ${escaparHtml(fechaActual)}
        </div>

        <div class="info">
            CLIENTE: ${escaparHtml(
                clientePedidoActual || "GENERAL"
            )}
        </div>

        <div class="info">
            SERVICIO: ${escaparHtml(
                servicioPedidoActual || ""
            )}
        </div>

        <div class="info">
            MESA: ${escaparHtml(
                mesaPedidoActual || ""
            )}
        </div>

        <div class="info">
            CATEGORÍA: ${escaparHtml(
                tipoPedidoActual
            )}
        </div>

        <div class="linea"></div>

        <div class="seccion">
            PREPARACIÓN
        </div>

        <div class="linea"></div>
    `;

    // ==========================================
    // PRODUCTOS
    // ==========================================

    detallePedidoActual.forEach((item, index) => {

        const cantidad =
            Number(item.cantidad || 0);

        const nombre =
            escaparHtml(
                item.nombre || "Producto"
            );

        html += `
            <div class="producto">

                <div class="producto-cabecera">

                    <span class="cantidad">
                        x${cantidad}
                    </span>

                    <span class="producto-nombre">
                        ${nombre}
                    </span>

                </div>
        `;

        // ======================================
        // COMPONENTES
        // ======================================

        if (
            Array.isArray(item.componentes) &&
            item.componentes.length > 0
        ) {

            html += `
                <div class="componentes">
            `;

            item.componentes.forEach(componente => {

                const categoria =
                    escaparHtml(
                        componente.categoria ||
                        "COMPONENTE"
                    );

                const nombreComponente =
                    escaparHtml(
                        componente.nombre ||
                        "-"
                    );

                html += `
                    <div class="componente">

                        <span class="componente-categoria">
                            ${categoria}
                        </span>

                        <span class="componente-nombre">
                            • ${nombreComponente}
                        </span>

                    </div>
                `;

            });

            html += `
                </div>
            `;

        }

        html += `
            </div>
        `;

        // Separador entre productos
        if (
            index <
            detallePedidoActual.length - 1
        ) {

            html += `
                <div class="linea"></div>
            `;

        }

    });

    // ==========================================
    // PIE DE COMANDA
    // ==========================================

    html += `

        <div class="linea"></div>

        <div class="footer">
            *** PREPARAR PEDIDO ***
        </div>

    </body>

    </html>
    `;

    // ==========================================
    // VENTANA DE IMPRESIÓN
    // ==========================================

    const ventana =
        window.open(
            "",
            "",
            "width=400,height=700"
        );

    if (!ventana) {

        mostrarMensaje(
            "El navegador bloqueó la ventana de impresión.",
            "warning"
        );

        return;
    }

    ventana.document.write(html);

    ventana.document.close();

    ventana.focus();

    setTimeout(() => {

        ventana.print();

        ventana.close();

    }, 500);
}