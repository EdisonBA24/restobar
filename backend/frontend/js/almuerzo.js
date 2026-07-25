/**********************************************************************
 * Archivo : almuerzos.js
 * Módulo  : Constructor de pedidos de almuerzos
 **********************************************************************/

import { apiFetch } from "./api.js";
import { Almuerzo } from "./models/almuerzo.js";

/*==============================================================
= VARIABLES
==============================================================*/

let componentes = {
    sopas: [],
    proteinas: [],
    secos: [],
    ensaladas: [],
    jugos: []
};

let almuerzoActual = null;
let almuerzosPedido = [];

let editandoId = null;

let clienteSeleccionado = null;
let mesaSeleccionada = null;
let tipoServicio = null;

let elementosDOM = {};


/*==============================================================
= CACHE DOM
==============================================================*/

function cacheDOM() {

    elementosDOM = {

        /*=========================================
        = DATOS DEL PEDIDO
        =========================================*/

        tipoServicio: document.getElementById("tipoServicio"),
        mesa: document.getElementById("mesa"),
        cliente: document.getElementById("cliente"),
        listaClientes: document.getElementById("listaClientes"),

        /*=========================================
        = SELECTOR DE TIPO DE PEDIDO
        =========================================*/

        selectorTipoPedido:
            document.getElementById("selectorTipoPedido"),

        contenidoPedido:
            document.getElementById("contenidoPedido"),

        btnVolverSelector:
            document.getElementById("btnVolverSelector"),

        tarjetasTipoPedido:
            document.querySelectorAll(".tipo-pedido-card"),

        /*=========================================
        = PANELES
        =========================================*/

        panelConstruir:
            document.getElementById("panelConstruir"),

        panelMenus:
            document.getElementById("panelMenus"),

        panelEspeciales:
            document.getElementById("panelEspeciales"),

        /*=========================================
        = CONSTRUCTOR
        =========================================*/

        cboSopa: document.getElementById("cboSopa"),
        cboProteina: document.getElementById("cboProteina"),
        cboSeco: document.getElementById("cboSeco"),
        cboEnsalada: document.getElementById("cboEnsalada"),
        cboJugo: document.getElementById("cboJugo"),

        txtObservaciones:
            document.getElementById("txtObservaciones"),

        /*=========================================
        = BOTONES
        =========================================*/

        btnAgregar:
            document.getElementById("btnAgregar"),

        btnCancelar:
            document.getElementById("btnCancelar"),

        btnGuardar:
            document.getElementById("btnGuardar"),

        /*=========================================
        = CONTENEDORES
        =========================================*/

        divResumen:
            document.getElementById("divResumen"),

        divPedido:
            document.getElementById("divPedido"),

        /*=========================================
        = ETIQUETAS
        =========================================*/

        lblSubtotal:
            document.getElementById("lblSubtotal"),

        lblTotal:
            document.getElementById("lblTotal"),

        lblCantidadAlmuerzos:
            document.getElementById("lblCantidadAlmuerzos"),

        lblCantidadAlmuerzosResumen:
            document.getElementById("lblCantidadAlmuerzosResumen"),

        lblCantidadProductos:
            document.getElementById("lblCantidadProductos"),

        mensajeVacio:
            document.getElementById("mensajeVacio"),

        loading:
            document.getElementById("loading")

    };

}


/*==============================================================
= NUEVO ALMUERZO
==============================================================*/

function crearNuevoAlmuerzo() {

    almuerzoActual = new Almuerzo();

    editandoId = null;

}


/*==============================================================
= INIT
==============================================================*/

async function init() {

    cacheDOM();

    crearNuevoAlmuerzo();

    registrarEventos();

    await cargarComponentes();

    tipoServicio = elementosDOM.tipoServicio.value;

    cambiarTipoServicio({

        target: {

            value: tipoServicio

        }

    });

    actualizarResumen();

    renderPedido();

}


/*==============================================================
= OBSERVACIONES
==============================================================*/

function actualizarObservaciones() {

    if (!almuerzoActual)
        return;

    almuerzoActual.observaciones =
        elementosDOM.txtObservaciones.value;

}

/*==============================================================
= CARGAR COMPONENTES
==============================================================*/

async function cargarComponentes() {

    try {

        mostrarCargando(true);

        const res = await apiFetch("/productos/almuerzo");

        if (!res || res.status === "error") {
            mostrarError("No fue posible obtener los componentes del almuerzo.");
            return;
        }

        componentes = {
            sopas: res.data?.sopas || [],
            proteinas: res.data?.proteinas || [],
            secos: res.data?.secos || [],
            ensaladas: res.data?.ensaladas || [],
            jugos: res.data?.jugos || []
        };

        console.log("✅ Componentes cargados:", componentes);

        llenarTodosLosCombos();

    } catch (error) {

        console.error("Error cargando componentes:", error);

        mostrarError(error.message);

    } finally {

        mostrarCargando(false);

    }

}


/*==============================================================
= LLENAR TODOS LOS COMBOS
==============================================================*/

function llenarTodosLosCombos() {

    llenarCombo(

        elementosDOM.cboSopa,

        componentes.sopas,

        "Seleccione una sopa"

    );

    llenarCombo(

        elementosDOM.cboProteina,

        componentes.proteinas,

        "Seleccione una proteína"

    );

    llenarCombo(

        elementosDOM.cboSeco,

        componentes.secos,

        "Seleccione un seco"

    );

    llenarCombo(

        elementosDOM.cboEnsalada,

        componentes.ensaladas,

        "Seleccione una ensalada"

    );

    llenarCombo(

        elementosDOM.cboJugo,

        componentes.jugos,

        "Seleccione un jugo"

    );

}


/*==============================================================
= LLENAR COMBO
==============================================================*/

function llenarCombo(

    select,

    lista,

    textoInicial

) {

    if (!select)
        return;

    select.innerHTML = "";

    const opcion = document.createElement("option");

    opcion.value = "";

    opcion.textContent = textoInicial;

    select.appendChild(opcion);

    lista.forEach(producto => {

        const option = document.createElement("option");

        option.value = producto.id;

        option.textContent =

            `${producto.nombre} (${formatearMoneda(producto.precio_venta)})`;

        option.dataset.precio = producto.precio_venta;

        select.appendChild(option);

    });

}


/*==============================================================
= BUSCAR PRODUCTO
==============================================================*/

function buscarProducto(

    lista,

    id

) {

    if (

        id === null ||

        id === undefined ||

        id === ""

    ) {

        return null;

    }

    return lista.find(

        producto =>

            Number(producto.id) === Number(id)

    ) || null;

}

function mostrarCargando(mostrar) {

    if (!elementosDOM.loading)
        return;

    elementosDOM.loading.style.display =

        mostrar

            ? "flex"

            : "none";

}

/*==============================================================
= REGISTRAR EVENTOS
==============================================================*/

function registrarEventos() {

    //=========================
    // COMPONENTES
    //=========================

    [
        elementosDOM.cboSopa,
        elementosDOM.cboProteina,
        elementosDOM.cboSeco,
        elementosDOM.cboEnsalada,
        elementosDOM.cboJugo
    ].forEach(control => {

        control?.addEventListener(
            "change",
            actualizarSeleccion
        );

    });

    //=========================
    // OBSERVACIONES
    //=========================

    elementosDOM.txtObservaciones?.addEventListener(

        "input",

        actualizarObservaciones

    );

    //=========================
    // CLIENTE
    //=========================

    elementosDOM.cliente?.addEventListener(

        "input",

        buscarClientes

    );

    //=========================
    // TIPO SERVICIO
    //=========================

    elementosDOM.tipoServicio?.addEventListener(

        "change",

        cambiarTipoServicio

    );

    //=========================
    // MESA
    //=========================

    elementosDOM.mesa?.addEventListener(

        "input",

        e => {

            mesaSeleccionada = e.target.value.trim();

        }

    );

    //=========================
    // BOTONES
    //=========================

    elementosDOM.btnAgregar?.addEventListener(

        "click",

        agregarAlPedido

    );

    elementosDOM.btnCancelar?.addEventListener(

        "click",

        cancelarEdicion

    );

    elementosDOM.btnGuardar?.addEventListener(

        "click",

        guardarPedido

    );

}

/*==============================================================
= CAMBIAR TIPO SERVICIO
==============================================================*/

function cambiarTipoServicio(e) {

    tipoServicio = e.target.value;

    if (tipoServicio === "MESA") {

        elementosDOM.mesa.disabled = false;

        elementosDOM.mesa.focus();

    } else {

        elementosDOM.mesa.value = "";

        mesaSeleccionada = null;

        elementosDOM.mesa.disabled = true;

    }

}

/*==============================================================
= BUSCAR CLIENTES
==============================================================*/

async function buscarClientes(e) {

    const texto = e.target.value.trim();

    clienteSeleccionado = null;

    if (texto.length < 2) {

        elementosDOM.listaClientes.innerHTML = "";
        elementosDOM.listaClientes.classList.add("hidden");
        return;

    }

    try {

        const res = await apiFetch(
            `/clientes?search=${encodeURIComponent(texto)}`
        );

        if (!res || res.status === "error") {
            return;
        }

        pintarListaClientes(res.data || []);

    } catch (error) {

        console.error("Error buscando clientes:", error);

    }

}

/*==============================================================
= PINTAR CLIENTES
==============================================================*/

function pintarListaClientes(lista) {

    elementosDOM.listaClientes.innerHTML = "";

    if (lista.length === 0) {

        elementosDOM.listaClientes.innerHTML = `
        <div class="autocomplete-empty">
            <div>Cliente no encontrado</div>

            <button
                type="button"
                class="btn-primary btn-crear-cliente"
                onclick="abrirCrearCliente()">
                ➕ Crear cliente nuevo
            </button>
        </div>
    `;

        elementosDOM.listaClientes.classList.remove("hidden");

        return;

    }

    lista.forEach(cliente => {

        const div = document.createElement("div");

        div.className = "autocomplete-item";

        div.innerHTML = `

            <strong>${cliente.nombre}</strong><br>

            <small>

                ${cliente.documento || ""}

            </small>

        `;

        div.onclick = () => seleccionarCliente(cliente);

        elementosDOM.listaClientes.appendChild(div);

    });

    elementosDOM.listaClientes.classList.remove("hidden");

}

/*==============================================================
= SELECCIONAR CLIENTE
==============================================================*/

function seleccionarCliente(cliente) {

    clienteSeleccionado = cliente.id;

    elementosDOM.cliente.value = cliente.nombre;

    elementosDOM.listaClientes.innerHTML = "";

    elementosDOM.listaClientes.classList.add("hidden");

}

document.addEventListener(

    "click",

    e => {

        if (

            !elementosDOM.listaClientes.contains(e.target)

            &&

            e.target !== elementosDOM.cliente

        ) {

            elementosDOM.listaClientes.classList.add(

                "hidden"

            );

        }

    }

);

/*==============================================================
= AGREGAR AL PEDIDO
==============================================================*/

function agregarAlPedido() {

    const error = validarAlmuerzo();

    if (error) {

        mostrarError(error);

        return;

    }

    const almuerzo = almuerzoActual.duplicar();

    if (editandoId) {

        const indice = almuerzosPedido.findIndex(

            item => item.id === editandoId

        );

        if (indice >= 0) {

            almuerzosPedido[indice] = almuerzo;

        }

    } else {

        almuerzosPedido.push(almuerzo);

    }

    editandoId = null;

    crearNuevoAlmuerzo();

    limpiarFormulario();

    actualizarResumen();

    renderPedido();

}

/*==============================================================
= EDITAR ALMUERZO
==============================================================*/

function editarAlmuerzo(id) {

    const almuerzo = almuerzosPedido.find(

        item => item.id === id

    );

    if (!almuerzo)
        return;

    editandoId = id;

    almuerzoActual = almuerzo.duplicar();

    elementosDOM.cboSopa.value =
        almuerzo.sopa?.id ?? "";

    elementosDOM.cboProteina.value =
        almuerzo.proteina?.id ?? "";

    elementosDOM.cboSeco.value =
        almuerzo.seco?.id ?? "";

    elementosDOM.cboEnsalada.value =
        almuerzo.ensalada?.id ?? "";

    elementosDOM.cboJugo.value =
        almuerzo.jugo?.id ?? "";

    elementosDOM.txtObservaciones.value =
        almuerzo.observaciones ?? "";

    elementosDOM.btnCancelar.style.display =
        "inline-flex";

    actualizarResumen();

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}

/*==============================================================
= CANCELAR EDICION
==============================================================*/

function cancelarEdicion() {

    editandoId = null;

    crearNuevoAlmuerzo();

    limpiarFormulario();

    elementosDOM.btnCancelar.style.display =
        "none";

}

/*==============================================================
= DUPLICAR ALMUERZO
==============================================================*/

function duplicarAlmuerzo(id) {

    const almuerzo = almuerzosPedido.find(

        item => item.id === id

    );

    if (!almuerzo)
        return;

    const copia = almuerzo.duplicar();

    copia.id = crypto.randomUUID();

    almuerzosPedido.push(copia);

    renderPedido();

}

/*==============================================================
= ELIMINAR ALMUERZO
==============================================================*/

function eliminarAlmuerzo(id) {

    if (

        !confirm(

            "¿Desea eliminar este almuerzo?"

        )

    ) {

        return;

    }

    almuerzosPedido = almuerzosPedido.filter(

        item => item.id !== id

    );

    renderPedido();

}

/*==============================================================
= LIMPIAR FORMULARIO
==============================================================*/

function limpiarFormulario() {

    elementosDOM.cboSopa.selectedIndex = 0;

    elementosDOM.cboProteina.selectedIndex = 0;

    elementosDOM.cboSeco.selectedIndex = 0;

    elementosDOM.cboEnsalada.selectedIndex = 0;

    elementosDOM.cboJugo.selectedIndex = 0;

    elementosDOM.txtObservaciones.value = "";

    elementosDOM.btnCancelar.style.display =
        "none";

}

/*==============================================================
= LIMPIAR PEDIDO
==============================================================*/

function limpiarPedido() {

    almuerzosPedido = [];

    editandoId = null;

    crearNuevoAlmuerzo();

    limpiarFormulario();

    renderPedido();

}

/*==============================================================
= CANTIDAD COMPONENTES
==============================================================*/

function obtenerCantidadComponentes() {

    return almuerzosPedido.reduce(

        (total, almuerzo) => {

            let cantidad = 0;

            if (almuerzo.sopa) cantidad++;

            if (almuerzo.proteina) cantidad++;

            if (almuerzo.seco) cantidad++;

            if (almuerzo.ensalada) cantidad++;

            if (almuerzo.jugo) cantidad++;

            return total + cantidad;

        },

        0

    );

}

/*==============================================================
= RENDER PEDIDO
==============================================================*/

function renderPedido() {

    if (!elementosDOM.divPedido)
        return;

    elementosDOM.divPedido.innerHTML = "";

    if (almuerzosPedido.length === 0) {

        elementosDOM.mensajeVacio.style.display = "block";

        actualizarResumen();

        return;

    }

    elementosDOM.mensajeVacio.style.display = "none";

    almuerzosPedido.forEach((almuerzo, index) => {

        elementosDOM.divPedido.appendChild(

            crearCardAlmuerzo(

                almuerzo,

                index + 1

            )

        );

    });

    actualizarResumen();

}

/*==============================================================
= CREAR CARD ALMUERZO
==============================================================*/

function crearCardAlmuerzo(

    almuerzo,

    numero

) {

    const card = document.createElement("div");

    card.className = "pedido-item";

    card.innerHTML = `

        <div class="pedido-header">

            <h4>

                Almuerzo #${numero}

            </h4>

            <span class="precio">

                ${formatearMoneda(almuerzo.precio)}

            </span>

        </div>

        <div class="pedido-body">

            <ul>

                <li><strong>Sopa:</strong> ${almuerzo.sopa?.nombre ?? "-"}</li>

                <li><strong>Proteína:</strong> ${almuerzo.proteina?.nombre ?? "-"}</li>

                <li><strong>Seco:</strong> ${almuerzo.seco?.nombre ?? "-"}</li>

                <li><strong>Ensalada:</strong> ${almuerzo.ensalada?.nombre ?? "-"}</li>

                <li><strong>Jugo:</strong> ${almuerzo.jugo?.nombre ?? "-"}</li>

            </ul>

            ${almuerzo.observaciones
            ? `<div class="observaciones">
                        <strong>Observaciones:</strong>
                        ${almuerzo.observaciones}
                   </div>`
            : ""
        }

        </div>

        <div class="pedido-footer">

            <button
                class="btn btn-primary"
                onclick="editarAlmuerzo('${almuerzo.id}')">

                Editar

            </button>

            <button
                class="btn btn-secondary"
                onclick="duplicarAlmuerzo('${almuerzo.id}')">

                Duplicar

            </button>

            <button
                class="btn btn-danger"
                onclick="eliminarAlmuerzo('${almuerzo.id}')">

                Eliminar

            </button>

        </div>

    `;

    return card;

}

/*==============================================================
= ACTUALIZAR RESUMEN
==============================================================*/

function actualizarResumen() {

    const cantidadAlmuerzos = almuerzosPedido.length;

    const cantidadProductos = obtenerCantidadComponentes();

    const total = obtenerTotalPedido();

    if (elementosDOM.lblCantidadAlmuerzos)
        elementosDOM.lblCantidadAlmuerzos.textContent = cantidadAlmuerzos;

    if (elementosDOM.lblCantidadAlmuerzosResumen)
        elementosDOM.lblCantidadAlmuerzosResumen.textContent = cantidadAlmuerzos;

    if (elementosDOM.lblCantidadProductos)
        elementosDOM.lblCantidadProductos.textContent = cantidadProductos;

    if (elementosDOM.lblTotal)
        elementosDOM.lblTotal.textContent = formatearMoneda(total);

}

/*==============================================================
= TOTAL PEDIDO
==============================================================*/

function obtenerTotalPedido() {

    return almuerzosPedido.reduce(

        (total, almuerzo) =>

            total + Number(almuerzo.precio),

        0

    );

}

/*==============================================================
= DEBUG
==============================================================*/

function debugPedido() {

    console.table(almuerzosPedido);

}

/*==============================================================
= RESUMEN ALMUERZO ACTUAL
==============================================================*/

function actualizarResumenActual() {

    if (!elementosDOM.divResumen)
        return;

    if (!almuerzoActual) {

        elementosDOM.divResumen.innerHTML = "";

        return;

    }

    elementosDOM.divResumen.innerHTML = `

        <ul class="resumen-almuerzo">

            <li><strong>Sopa:</strong> ${almuerzoActual.sopa?.nombre ?? "-"}</li>

            <li><strong>Proteína:</strong> ${almuerzoActual.proteina?.nombre ?? "-"}</li>

            <li><strong>Seco:</strong> ${almuerzoActual.seco?.nombre ?? "-"}</li>

            <li><strong>Ensalada:</strong> ${almuerzoActual.ensalada?.nombre ?? "-"}</li>

            <li><strong>Jugo:</strong> ${almuerzoActual.jugo?.nombre ?? "-"}</li>

        </ul>

    `;

    if (elementosDOM.lblSubtotal) {

        elementosDOM.lblSubtotal.textContent =
            formatearMoneda(almuerzoActual.precio);

    }

}

/*==============================================================
= GUARDAR PEDIDO
==============================================================*/

async function guardarPedido() {

    try {

        const error = validarPedidoCompleto();

        if (error) {

            mostrarError(error);

            return;

        }

        mostrarCargando(true);

        const pedido = construirPedido();

        console.log("Pedido a guardar:", pedido);

        const response = await fetch(

            `${API_URL}/pedidos`,

            {

                method: "POST",

                credentials: "include",

                headers: {

                    "Content-Type": "application/json"

                },

                body: JSON.stringify(pedido)

            }

        );

        const json = await response.json();

        if (!response.ok || json.status !== "success") {

            throw new Error(

                json.message ||

                "No fue posible guardar el pedido."

            );

        }

        mostrarToast(

            "Pedido registrado correctamente",

            "success"

        );

        limpiarDespuesGuardar();

    }

    catch (error) {

        console.error(error);

        mostrarError(error.message);

    }

    finally {

        mostrarCargando(false);

    }

}

/*==============================================================
= CONSTRUIR PEDIDO
==============================================================*/

function construirPedido() {

    return {
        mesa: mesaSeleccionada,
        tipo: tipoServicio,
        cliente: elementosDOM.cliente.value.trim(),
        cliente_id: clienteSeleccionado,
        estado: "pendiente",
        categoria: "ALMUERZOS",
        detalles: construirDetallesPedido()
    }

}

/*==============================================================
= CONSTRUIR DETALLES
==============================================================*/

function construirDetallesPedido() {

    const detalles = [];

    almuerzosPedido.forEach(almuerzo => {

        detalles.push({

            tipo_item: "ALMUERZO",

            cantidad: 1,

            precio: almuerzo.precio,

            observaciones: almuerzo.observaciones,

            componentes: [

                { producto_id: almuerzo.sopa.id },

                { producto_id: almuerzo.proteina.id },

                { producto_id: almuerzo.seco.id },

                { producto_id: almuerzo.ensalada.id },

                { producto_id: almuerzo.jugo.id }

            ]

        });

    });

    return detalles;
}


/*==============================================================
= VALIDAR PEDIDO
==============================================================*/

function validarPedidoCompleto() {

    if (almuerzosPedido.length === 0) {

        return "Debe agregar al menos un almuerzo.";

    }

    if (!tipoServicio) {

        return "Seleccione el tipo de servicio.";

    }

    if (

        tipoServicio === "MESA"

        &&

        !mesaSeleccionada

    ) {

        return "Debe indicar la mesa.";

    }

    return null;

}

/*==============================================================
= LIMPIAR DESPUES GUARDAR
==============================================================*/

function limpiarDespuesGuardar() {

    limpiarPedido();

    elementosDOM.cliente.value = "";

    clienteSeleccionado = null;

    elementosDOM.tipoServicio.selectedIndex = 0;

    tipoServicio = null;

    elementosDOM.mesa.value = "";

    mesaSeleccionada = null;

}

/*==============================================================
= VALIDAR ALMUERZO
==============================================================*/

function validarAlmuerzo() {

    if (!almuerzoActual.sopa)
        return "Debe seleccionar una sopa.";

    if (!almuerzoActual.proteina)
        return "Debe seleccionar una proteína.";

    if (!almuerzoActual.seco)
        return "Debe seleccionar un seco.";

    if (!almuerzoActual.ensalada)
        return "Debe seleccionar una ensalada.";

    if (!almuerzoActual.jugo)
        return "Debe seleccionar un jugo.";

    return null;

}

/*==============================================================
= FORMATEAR MONEDA
==============================================================*/

function formatearMoneda(valor) {

    return Number(valor || 0).toLocaleString(

        "es-CO",

        {

            style: "currency",

            currency: "COP",

            minimumFractionDigits: 0

        }

    );

}

/*==============================================================
= TOAST
==============================================================*/

function mostrarToast(

    mensaje,

    tipo = "success"

) {

    if (window.Toastify) {

        Toastify({

            text: mensaje,

            duration: 3000,

            gravity: "top",

            position: "right",

            className: tipo

        }).showToast();

        return;

    }

    alert(mensaje);

}

/*==============================================================
= ERROR
==============================================================*/

function mostrarError(error) {

    mostrarToast(

        error,

        "error"

    );

}

/*==============================================================
= SELECCIONAR COMPONENTE
==============================================================*/

function obtenerProductoSeleccionado(

    combo,

    lista

) {

    return buscarProducto(

        lista,

        combo.value

    );

}

/*==============================================================
= ACTUALIZAR SELECCION
==============================================================*/

function actualizarSeleccion() {

    almuerzoActual.sopa =

        obtenerProductoSeleccionado(

            elementosDOM.cboSopa,

            componentes.sopas

        );

    almuerzoActual.proteina =

        obtenerProductoSeleccionado(

            elementosDOM.cboProteina,

            componentes.proteinas

        );

    almuerzoActual.seco =

        obtenerProductoSeleccionado(

            elementosDOM.cboSeco,

            componentes.secos

        );

    almuerzoActual.ensalada =

        obtenerProductoSeleccionado(

            elementosDOM.cboEnsalada,

            componentes.ensaladas

        );

    almuerzoActual.jugo =

        obtenerProductoSeleccionado(

            elementosDOM.cboJugo,

            componentes.jugos

        );

    almuerzoActual.calcularPrecio();

    actualizarResumenActual();

}

/*==============================================================
= UUID
==============================================================*/

function generarId() {

    if (window.crypto?.randomUUID) {

        return crypto.randomUUID();

    }

    return Date.now().toString();

}

/*==============================================================
= SCROLL
==============================================================*/

function subirInicio() {

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}

/*==============================================================
= CERRAR AUTOCOMPLETE
==============================================================*/

function cerrarAutocomplete() {

    elementosDOM.listaClientes.innerHTML = "";

    elementosDOM.listaClientes.classList.add(

        "hidden"

    );

}

window.editarAlmuerzo = editarAlmuerzo;

window.duplicarAlmuerzo = duplicarAlmuerzo;

window.eliminarAlmuerzo = eliminarAlmuerzo;

window.cancelarEdicion = cancelarEdicion;

window.debugPedido = debugPedido;

document.addEventListener(

    "DOMContentLoaded",

    init

);



