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

let direccionSeleccionada = null;

const MENUS = {

    EJECUTIVO: {

        tipo: "MENU_EJECUTIVO",

        nombre: "Menú Ejecutivo",

        precio: 17000

    },

    PREMIUM: {

        tipo: "MENU_PREMIUM",

        nombre: "Menú Premium",

        precio: 23000

    },

    ESPECIAL: {

        tipo: "MENU_ESPECIAL",

        nombre: "Menú Especial",

        precio: 25000

    }

};

const MODOS = {

    MENU: "MENU",

    ADICION: "ADICION"

};

const CABECERAS = {

    ADICION: {

        titulo: "🍽️ Agregar Adiciones",

        badge: "Adiciones del almuerzo",

        descripcion:
            "Seleccione cada uno de los componentes que desea agregar como adición."

    },

    MENU_EJECUTIVO: {

        titulo: "🍽️ Menú Ejecutivo",

        badge: "Menú Ejecutivo",

        descripcion:
            "Seleccione los componentes incluidos en el Menú Ejecutivo."

    },

    MENU_PREMIUM: {

        titulo: "🥘 Menú Premium",

        badge: "Menú Premium",

        descripcion:
            "Seleccione los componentes incluidos en el Menú Premium."

    },

    MENU_ESPECIAL: {

        titulo: "⭐ Menú Especial",

        badge: "Menú Especial",

        descripcion:
            "Seleccione los componentes incluidos en el Menú Especial."

    }

};

/*******************************************************************/

/********************************************************************
 * CONFIGURACIÓN
 ********************************************************************/

/********************************************************************
 * ESTADO GLOBAL
 ********************************************************************/

/********************************************************************
 * CACHE DOM
 ********************************************************************/
function cacheDOM() {

    elementosDOM = {

        /*=========================================
        = DATOS DEL PEDIDO
        =========================================*/

        mesa: document.getElementById("mesa"),
        cliente: document.getElementById("cliente"),
        listaClientes: document.getElementById("listaClientes"),

        grupoDireccion:
            document.getElementById(
                "grupoDireccion"
            ),

        direccionEntrega:
            document.getElementById(
                "direccionEntrega"
            ),

        infoDirecciones:
            document.getElementById(
                "infoDirecciones"
            ),

        tipoServicio:
            document.getElementById(
                "tipoServicio"
            ),

        /*=========================================
        = SELECTOR DE TIPO DE PEDIDO
        =========================================*/

        contenidoPedido:
            document.getElementById("contenidoPedido"),

        tarjetasTipoPedido:
            document.querySelectorAll(".tipo-pedido-card"),

        /*=========================================
        = PANELES
        =========================================*/

        panelConstruir:
            document.getElementById("panelConstruir"),

        panelMenus:
            document.getElementById("panelMenus"),

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

        tituloConstructor:
            document.getElementById("tituloConstructor"),

        badgeConstructor:
            document.getElementById("badgeConstructor"),

        descripcionConstructor:
            document.getElementById("descripcionConstructor"),

        /*=========================================
        = BOTONES
        =========================================*/

        btnAgregar:
            document.getElementById("btnAgregar"),

        textoBotonAgregar: "➕ Agregar al pedido",

        btnCancelar:
            document.getElementById("btnCancelar"),

        btnGuardar:
            document.getElementById("btnGuardar"),

        /*=========================================
        = CONTENEDORES
        =========================================*/

        divResumen:
            document.getElementById("divResumen"),

        lblTipoPedido:
            document.getElementById("lblTipoPedido"),

        lblEstadoPedido:
            document.getElementById("lblEstadoPedido"),

        resSopa:
            document.getElementById("resSopa"),

        resProteina:
            document.getElementById("resProteina"),

        resSeco:
            document.getElementById("resSeco"),

        resEnsalada:
            document.getElementById("resEnsalada"),

        resJugo:
            document.getElementById("resJugo"),

        divPedido:
            document.getElementById("divPedido"),

        /*=========================================
        = ETIQUETAS
        =========================================*/

        lblSubtotal:
            document.getElementById("lblSubtotal"),

        lblTotal:
            document.getElementById("lblTotal"),

        lblCantidadMenus:
            document.getElementById("lblCantidadMenus"),

        lblCantidadAdiciones:
            document.getElementById("lblCantidadAdiciones"),

        lblCantidadItems:
            document.getElementById("lblCantidadItems"),

        mensajeVacio:
            document.getElementById("mensajeVacio"),

        loading:
            document.getElementById("loading"),

        modalClienteRapido:
            document.getElementById(
                "modalClienteRapido"
            ),

        btnGuardarClienteRapido:
            document.getElementById(
                "btnGuardarClienteRapido"
            ),

        btnCancelarClienteRapido:
            document.getElementById(
                "btnCancelarClienteRapido"
            ),

        btnCerrarModalClienteRapido:
            document.getElementById(
                "btnCerrarModalClienteRapido"
            ),

        nuevoNombre:
            document.getElementById(
                "nuevoNombre"
            ),

        nuevoDocumento:
            document.getElementById(
                "nuevoDocumento"
            ),

        nuevoTelefono:
            document.getElementById(
                "nuevoTelefono"
            ),

        nuevoDireccion:
            document.getElementById(
                "nuevoDireccion"
            ),

        nuevoBarrio:
            document.getElementById(
                "nuevoBarrio"
            ),

        nuevoReferencia:
            document.getElementById(
                "nuevoReferencia"
            ),

    };

}

async function init() {

    cacheDOM();

    crearNuevoAlmuerzo();

    registrarEventos();

    await cargarComponentes();

    //tipoServicio = elementosDOM.tipoServicio.value;

    cambiarTipoServicio({

        target: {

            value: tipoServicio

        }

    });

    //actualizarResumen();
    actualizarResumenActual();

    renderPedido();

}

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

    document.addEventListener(

        "keydown",

        manejarEscapeModalCliente

    );

    elementosDOM.modalClienteRapido.addEventListener(

        "click",

        cerrarModalClickFuera

    );

    //=========================
    // TIPOS DE PEDIDO
    //=========================

    elementosDOM.tarjetasTipoPedido.forEach(card => {

        card.addEventListener(

            "click",

            () => seleccionarTipoPedido(card)

        );

    });

    elementosDOM.btnCancelarClienteRapido
        .addEventListener(
            "click",
            cerrarModalClienteRapido
        );

    elementosDOM.btnCerrarModalClienteRapido
        .addEventListener(
            "click",
            cerrarModalClienteRapido
        );

    elementosDOM.btnGuardarClienteRapido
        ?.addEventListener(
            "click",
            guardarClienteRapido
        );

    elementosDOM.direccionEntrega.addEventListener(

        "change",

        () => {

            direccionSeleccionada =

                Number(

                    elementosDOM.direccionEntrega.value

                );

        }

    );

}

/********************************************************************/

/********************************************************************
 * CLIENTES
 ********************************************************************/
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

        const clientes = res.data?.items || [];

        pintarListaClientes(clientes);


    } catch (error) {

        console.error("Error buscando clientes:", error);

    }

}

function pintarListaClientes(lista) {

    elementosDOM.listaClientes.innerHTML = "";

    if (lista.length === 0) {

        elementosDOM.listaClientes.innerHTML = `
        <div class="autocomplete-empty">

            <div>Cliente no encontrado</div>

            <button
                type="button"
                id="btnCrearClienteRapido"
                class="btn-primary btn-crear-cliente">

                ➕ Crear cliente nuevo

            </button>

        </div>
        `;

        const btnCrear = document.getElementById("btnCrearClienteRapido");

        if (btnCrear) {

            btnCrear.addEventListener("click", () => {

                //window.abrirCrearCliente();
                abrirModalClienteRapido();

            });

        }

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

function abrirModalClienteRapido() {

    limpiarFormularioClienteRapido();

    elementosDOM.nuevoNombre.value =
        elementosDOM.cliente.value.trim();

    elementosDOM.modalClienteRapido
        .classList.remove("hidden");

    elementosDOM.nuevoNombre.focus();

}

async function guardarClienteRapido() {

    try {

        elementosDOM.btnGuardarClienteRapido.disabled = true;

        elementosDOM.btnGuardarClienteRapido.textContent =
            "Guardando...";

        const nombre =
            elementosDOM.nuevoNombre.value.trim();

        const documento =
            elementosDOM.nuevoDocumento.value.trim();

        const telefono =
            elementosDOM.nuevoTelefono.value.trim();

        const direccion =
            elementosDOM.nuevoDireccion.value.trim();

        const barrio =
            elementosDOM.nuevoBarrio.value.trim();

        const referencia =
            elementosDOM.nuevoReferencia.value.trim();

        //==============================
        // VALIDACIONES
        //==============================

        if (!nombre) {

            mostrarError(
                "Debe ingresar el nombre del cliente."
            );

            elementosDOM.nuevoNombre.focus();

            return;

        }

        if (!direccion) {

            mostrarError(
                "Debe ingresar la dirección principal."
            );

            elementosDOM.nuevoDireccion.focus();

            return;

        }

        const payload = {

            nombre,

            documento,

            telefono,

            email: "",

            direcciones: [

                {

                    nombre: "Principal",

                    direccion,

                    barrio,

                    referencia,

                    principal: 1,

                    activo: 1

                }

            ]

        };

        console.log(
            "Cliente rápido:",
            payload
        );

        const response = await apiFetch(

            "/clientes",

            "POST",

            payload

        );

        if (!response) {

            throw new Error(
                "No se recibió respuesta del servidor."
            );

        }

        if (response.status !== "success") {

            throw new Error(

                response.message ||

                "No fue posible crear el cliente."

            );

        }

        await actualizarClienteCreado(

            response.cliente_id

        );

        cerrarModalClienteRapido();

        mostrarToast(

            "Cliente creado correctamente",

            "success"

        );

    }

    catch (error) {

        console.error(error);

        mostrarError(

            error.message

        );

    } finally {

        elementosDOM.btnGuardarClienteRapido.disabled = false;

        elementosDOM.btnGuardarClienteRapido.textContent =
            "Guardar Cliente";

    }

}

async function actualizarClienteCreado(clienteId) {

    const response = await apiFetch(

        `/clientes/${clienteId}`

    );

    if (

        !response ||

        response.status !== "success"

    ) {

        return;

    }

    const cliente = response.data;

    seleccionarCliente(cliente);

}

function seleccionarCliente(cliente) {

    clienteSeleccionado = cliente.id;

    if (

        elementosDOM.tipoServicio.value === "DOMICILIO"

    ) {

        cargarDireccionesCliente(cliente.id);

    }

    elementosDOM.cliente.value = cliente.nombre;

    elementosDOM.listaClientes.innerHTML = "";

    elementosDOM.listaClientes.classList.add("hidden");

}

function limpiarFormularioClienteRapido() {

    elementosDOM.nuevoNombre.value = "";

    elementosDOM.nuevoDocumento.value = "";

    elementosDOM.nuevoTelefono.value = "";

    elementosDOM.nuevoDireccion.value = "";

    elementosDOM.nuevoBarrio.value = "";

    elementosDOM.nuevoReferencia.value = "";

}

function cerrarModalClienteRapido() {

    limpiarFormularioClienteRapido();

    elementosDOM.modalClienteRapido
        .classList.add("hidden");

}

/********************************************************************/

/********************************************************************
 * DIRECCIONES
 ********************************************************************/
function limpiarDirecciones() {

    elementosDOM.direccionEntrega.innerHTML = `

        <option value="">

            Seleccione una dirección...

        </option>

    `;

    elementosDOM.infoDirecciones.classList.add("hidden");

    //elementosDOM.accionesDireccion.classList.add("hidden");

}

async function cargarDireccionesCliente(clienteId) {

    limpiarDirecciones();

    elementosDOM.infoDirecciones.textContent =
        "Cargando direcciones...";

    elementosDOM.infoDirecciones.classList.remove("hidden");

    try {

        const response = await apiFetch(

            `/clientes/${clienteId}`

        );

        if (

            !response ||

            response.status !== "success"

        ) {

            throw new Error(

                "No fue posible obtener las direcciones."

            );

        }

        const cliente = response.data;

        llenarDirecciones(

            cliente.direcciones || []

        );

    }

    catch (error) {

        console.error(error);

        elementosDOM.infoDirecciones.textContent =

            "Error cargando direcciones.";

    }

}

function llenarDirecciones(direcciones) {

    limpiarDirecciones();

    if (

        !direcciones ||

        direcciones.length === 0

    ) {

        elementosDOM.infoDirecciones.textContent =

            "Cliente sin direcciones registradas.";

        elementosDOM.infoDirecciones.classList.remove("hidden");

        //elementosDOM.accionesDireccion.classList.remove("hidden");

        return;

    }

    direcciones.forEach(direccion => {

        const option = document.createElement("option");

        option.value = direccion.id;

        option.textContent =

            `${direccion.nombre} - ${direccion.direccion}`;

        if (direccion.principal) {

            option.selected = true;
            direccionSeleccionada = direccion.id;

        }

        elementosDOM.direccionEntrega.appendChild(option);

    });

    elementosDOM.infoDirecciones.classList.add("hidden");

    //elementosDOM.accionesDireccion.classList.remove("hidden");

}

/********************************************************************/

/********************************************************************
 * MENÚS
 ********************************************************************/
function seleccionarMenu(tipo) {

    crearNuevoAlmuerzo();

    almuerzoActual.modo = MODOS.MENU;

    almuerzoActual.tipo = MENUS[tipo].tipo;

    almuerzoActual.nombre = MENUS[tipo].nombre;

    almuerzoActual.precioBase = MENUS[tipo].precio;

    almuerzoActual.calcularPrecio();

    actualizarCabeceraConstructor();

    elementosDOM.contenidoPedido.classList.remove("hidden");

    document
        .querySelectorAll(".tab-panel")
        .forEach(panel => {
            panel.classList.remove("active");
            panel.classList.add("hidden");
        });

    elementosDOM.panelConstruir.classList.remove("hidden");
    elementosDOM.panelConstruir.classList.add("active");

    actualizarResumenActual();
}

function seleccionarTipoPedido(card) {

    elementosDOM.tarjetasTipoPedido.forEach(

        t => t.classList.remove("active")

    );

    card.classList.add("active");

    if (!card.dataset.menu) {

        crearNuevoAlmuerzo();

        almuerzoActual.modo = MODOS.ADICION;

        actualizarCabeceraConstructor();

        actualizarResumenActual();

    }

    const menu = card.dataset.menu;

    if (menu && MENUS[menu]) {

        crearNuevoAlmuerzo();

        almuerzoActual.modo = MODOS.MENU;

        almuerzoActual.tipo = MENUS[menu].tipo;

        almuerzoActual.nombre = MENUS[menu].nombre;

        almuerzoActual.precioBase = MENUS[menu].precio;

        almuerzoActual.calcularPrecio();

        actualizarCabeceraConstructor();

        actualizarResumenActual();

    }

    elementosDOM.contenidoPedido.classList.remove("hidden");

    document

        .querySelectorAll(".tab-panel")

        .forEach(panel => {

            panel.classList.remove("active");

            panel.classList.add("hidden");

        });

    const panel = document.getElementById(

        card.dataset.panel

    );

    if (panel) {

        panel.classList.remove("hidden");

        panel.classList.add("active");

    }

}

function cambiarTipoServicio() {

    tipoServicio = elementosDOM.tipoServicio.value;

    if (tipoServicio !== "DOMICILIO") {

        elementosDOM.grupoDireccion.classList.add("hidden");

        limpiarDirecciones();

        return;

    }

    elementosDOM.grupoDireccion.classList.remove("hidden");

    if (clienteSeleccionado) {

        cargarDireccionesCliente(clienteSeleccionado);

    }

}

/********************************************************************/

/********************************************************************
 * CONSTRUCTOR
 ********************************************************************/
function crearNuevoAlmuerzo() {

    almuerzoActual = new Almuerzo();

    editandoId = null;

    // Estado por defecto
    almuerzoActual.modo = MODOS.ADICION;

    almuerzoActual.precioBase = 0;

    almuerzoActual.nombre = "Adición";

    actualizarCabeceraConstructor();

    actualizarEstadoEdicion();

}

function actualizarCabeceraConstructor() {

    if (!almuerzoActual)
        return;

    let config = CABECERAS.ADICION;

    if (almuerzoActual.modo === MODOS.MENU) {

        switch (almuerzoActual.tipo) {

            case MENUS.EJECUTIVO.tipo:

                config = CABECERAS.MENU_EJECUTIVO;
                break;

            case MENUS.PREMIUM.tipo:

                config = CABECERAS.MENU_PREMIUM;
                break;

            case MENUS.ESPECIAL.tipo:

                config = CABECERAS.MENU_ESPECIAL;
                break;

        }

    }

    elementosDOM.tituloConstructor.textContent =
        config.titulo;

    elementosDOM.badgeConstructor.textContent =
        config.badge;

    elementosDOM.descripcionConstructor.textContent =
        config.descripcion;

}

function actualizarEstadoEdicion() {

    if (editandoId) {

        elementosDOM.btnAgregar.innerHTML =
            "💾 Actualizar almuerzo";

        elementosDOM.btnCancelar.style.display =
            "inline-flex";

    }
    else {

        elementosDOM.btnAgregar.innerHTML =
            elementosDOM.textoBotonAgregar;

        elementosDOM.btnCancelar.style.display =
            "none";

    }

}

function actualizarObservaciones() {

    if (!almuerzoActual)
        return;

    almuerzoActual.observaciones =
        elementosDOM.txtObservaciones.value;

}

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

/********************************************************************/

/********************************************************************
 * PEDIDO
 ********************************************************************/
function agregarAlPedido() {

    const faltantes = validarAlmuerzo();

    if (faltantes.length > 0) {

        mostrarToast(

            `Se agregará el pedido sin: ${faltantes.join(", ")}.`,

            "warning"

        );

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

    //actualizarResumen();
    actualizarResumenActual();

    renderPedido();

}

function editarAlmuerzo(id) {

    const almuerzo = almuerzosPedido.find(

        item => item.id === id

    );

    if (!almuerzo)
        return;

    editandoId = id;

    almuerzoActual = almuerzo.duplicar();

    actualizarCabeceraConstructor();

    actualizarEstadoEdicion();

    //=========================================
    // ACTIVAR TARJETA SEGÚN EL MODO
    //=========================================

    elementosDOM.tarjetasTipoPedido.forEach(card => {

        card.classList.remove("active");

    });

    document
        .querySelectorAll(".tab-panel")
        .forEach(panel => {

            panel.classList.remove("active");

            panel.classList.add("hidden");

        });

    if (almuerzo.modo === MODOS.MENU) {

        const tarjetaMenus = [...elementosDOM.tarjetasTipoPedido]

            .find(card =>

                card.dataset.panel === "panelMenus"

            );

        tarjetaMenus?.classList.add("active");

    }

    else {

        const tarjetaAdiciones = [...elementosDOM.tarjetasTipoPedido]

            .find(card =>

                card.dataset.panel === "panelConstruir"

            );

        tarjetaAdiciones?.classList.add("active");

    }

    elementosDOM.panelConstruir.classList.remove("hidden");

    elementosDOM.panelConstruir.classList.add("active");

    elementosDOM.contenidoPedido.classList.remove("hidden");

    //=========================================
    // CARGAR COMPONENTES
    //=========================================

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

    actualizarResumenActual();

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}

function generarId() {

    if (window.crypto && typeof crypto.randomUUID === "function") {
        return crypto.randomUUID();
    }

    return "ALM-" +
        Date.now() +
        "-" +
        Math.random().toString(36).substring(2, 10);

}

function duplicarAlmuerzo(id) {

    const almuerzo = almuerzosPedido.find(
        item => item.id === id
    );

    if (!almuerzo)
        return;

    const copia = almuerzo.duplicar();

    copia.id = generarId();

    almuerzosPedido.push(copia);

    renderPedido();

}

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

function renderPedido() {

    if (!elementosDOM.divPedido)
        return;

    elementosDOM.divPedido.innerHTML = "";

    if (almuerzosPedido.length === 0) {

        elementosDOM.mensajeVacio.style.display = "block";

        actualizarResumenActual();

        actualizarResumenPedido();

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

    actualizarResumenActual();

    actualizarResumenPedido();

}

function crearCardAlmuerzo(

    almuerzo,

    numero

) {

    const card = document.createElement("div");

    card.className = "pedido-item";

    card.innerHTML = `

        <div class="pedido-card">

            <div class="pedido-card-header">

                <div>

                    <div class="pedido-titulo">

                        ${almuerzo.nombre}

                    </div>

                    <div class="pedido-subtitulo">

                        Item #${numero}

                    </div>

                </div>

                <div class="pedido-precio">

                    ${formatearMoneda(almuerzo.precio)}

                    <small>

                        ${almuerzo.modo === MODOS.MENU
            ? "Precio fijo del menú"
            : "Adición"}

                    </small>

                </div>

            </div>

            <div class="pedido-componentes">

                <div class="pedido-componente">

                    <label>🍲 Sopa</label>

                    <span>${almuerzo.sopa?.nombre ?? "—"}</span>

                </div>

                <div class="pedido-componente">

                    <label>🥩 Proteína</label>

                    <span>${almuerzo.proteina?.nombre ?? "—"}</span>

                </div>

                <div class="pedido-componente">

                    <label>🍚 Seco</label>

                    <span>${almuerzo.seco?.nombre ?? "—"}</span>

                </div>

                <div class="pedido-componente">

                    <label>🥗 Ensalada</label>

                    <span>${almuerzo.ensalada?.nombre ?? "—"}</span>

                </div>

                <div class="pedido-componente">

                    <label>🥤 Jugo</label>

                    <span>${almuerzo.jugo?.nombre ?? "—"}</span>

                </div>

            </div>

            ${almuerzo.observaciones
            ? `
                <div class="pedido-observaciones">

                    <strong>📝 Observaciones</strong>

                    <p>${almuerzo.observaciones}</p>

                </div>
                `
            : ""}

            <div class="pedido-footer">

                <button
                    class="btn btn-primary"
                    onclick="editarAlmuerzo('${almuerzo.id}')">

                    ✏ Editar

                </button>

                <button
                    class="btn btn-secondary"
                    onclick="duplicarAlmuerzo('${almuerzo.id}')">

                    📄 Duplicar

                </button>

                <button
                    class="btn btn-danger"
                    onclick="eliminarAlmuerzo('${almuerzo.id}')">

                    🗑 Eliminar

                </button>

            </div>

        </div>

    `;

    return card;

}

function cancelarEdicion() {

    editandoId = null;

    crearNuevoAlmuerzo();

    limpiarFormulario();

    //elementosDOM.btnCancelar.style.display =
    //    "none";
    actualizarEstadoEdicion();

}

/********************************************************************/

/********************************************************************
 * RESUMEN
 ********************************************************************/
function actualizarResumenActual() {

    //=========================================
    // VALIDACIONES
    //=========================================

    if (!almuerzoActual)
        return;

    //=========================================
    // CABECERA DEL PANEL
    //=========================================

    elementosDOM.lblTipoPedido.textContent =
        almuerzoActual.nombre;

    elementosDOM.lblEstadoPedido.textContent =
        almuerzoActual.modo === MODOS.MENU
            ? "Construyendo menú"
            : "Adición al pedido";

    //=========================================
    // COMPONENTES
    //=========================================

    elementosDOM.resSopa.textContent =
        almuerzoActual.sopa
            ? almuerzoActual.sopa.nombre
            : "Sin seleccionar";

    elementosDOM.resProteina.textContent =
        almuerzoActual.proteina
            ? almuerzoActual.proteina.nombre
            : "Sin seleccionar";

    elementosDOM.resSeco.textContent =
        almuerzoActual.seco
            ? almuerzoActual.seco.nombre
            : "Sin seleccionar";

    elementosDOM.resEnsalada.textContent =
        almuerzoActual.ensalada
            ? almuerzoActual.ensalada.nombre
            : "Sin seleccionar";

    elementosDOM.resJugo.textContent =
        almuerzoActual.jugo
            ? almuerzoActual.jugo.nombre
            : "Sin seleccionar";

    //=========================================
    // TOTAL
    //=========================================

    elementosDOM.lblSubtotal.textContent =
        formatearMoneda(almuerzoActual.precio);

    //=========================================
    // ESTADO VISUAL
    //=========================================

    actualizarEstadoResumen(elementosDOM.resSopa);

    actualizarEstadoResumen(elementosDOM.resProteina);

    actualizarEstadoResumen(elementosDOM.resSeco);

    actualizarEstadoResumen(elementosDOM.resEnsalada);

    actualizarEstadoResumen(elementosDOM.resJugo);

}

function actualizarEstadoResumen(elemento) {

    if (!elemento)
        return;

    if (elemento.textContent === "Sin seleccionar") {

        elemento.classList.remove("ok");

        elemento.classList.add("empty");

    }
    else {

        elemento.classList.remove("empty");

        elemento.classList.add("ok");

    }

}

function actualizarResumenPedido() {

    console.table(
        almuerzosPedido.map(a => ({
            nombre: a.nombre,
            modo: a.modo,
            tipo: a.tipo,
            precio: a.precio
        }))
    );

    const total = obtenerTotalPedido();

    const cantidadMenus = almuerzosPedido.filter(item =>
        item.tipo?.startsWith("MENU_")
    ).length;

    const cantidadAdiciones = almuerzosPedido.filter(item =>
        item.tipo === "ADICION"
    ).length;

    const totalItems = almuerzosPedido.length;

    if (elementosDOM.lblTotal) {

        elementosDOM.lblTotal.textContent =
            formatearMoneda(total);

    }

    elementosDOM.lblCantidadMenus.textContent = cantidadMenus;
    elementosDOM.lblCantidadAdiciones.textContent = cantidadAdiciones;
    elementosDOM.lblCantidadItems.textContent = almuerzosPedido.length;

}

function obtenerTotalPedido() {

    return almuerzosPedido.reduce(

        (total, almuerzo) =>

            total + Number(almuerzo.precio),

        0

    );

}

/********************************************************************/

/********************************************************************
 * GUARDAR PEDIDO
 ********************************************************************/
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

        const response = await apiFetch(

            "/pedidos",

            "POST",

            pedido

        );

        console.log("Respuesta servidor:", response);

        if (!response) {

            throw new Error("No hubo respuesta del servidor.");

        }

        if (response.status !== "success") {

            throw new Error(

                response.message || "No fue posible guardar el pedido."

            );

        }

        mostrarToast(

            "Pedido registrado correctamente.",

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

function construirPedido() {

    return {

        mesa: mesaSeleccionada,

        tipo: tipoServicio,

        cliente: elementosDOM.cliente.value.trim(),

        cliente_id: clienteSeleccionado,

        direccion_id: direccionSeleccionada,

        estado: "PENDIENTE",

        categoria: "ALMUERZOS",

        detalles: construirDetallesPedido()

    };

}

function construirDetallesPedido() {

    const detalles = [];

    almuerzosPedido.forEach(almuerzo => {

        const componentes = [];

        [
            almuerzo.sopa,
            almuerzo.proteina,
            almuerzo.seco,
            almuerzo.ensalada,
            almuerzo.jugo
        ].forEach(item => {

            if (!item) return;

            componentes.push({
                producto_id: item.id
            });

        });

        detalles.push({
            tipo_item: almuerzo.tipo || "ADICION",
            cantidad: 1,
            precio: almuerzo.precio,
            observaciones: almuerzo.observaciones,
            componentes
        });

    });

    return detalles;

}

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

function limpiarDespuesGuardar() {

    limpiarPedido();

    elementosDOM.cliente.value = "";

    clienteSeleccionado = null;

    elementosDOM.tipoServicio.selectedIndex = 0;

    tipoServicio = null;

    elementosDOM.mesa.value = "";

    mesaSeleccionada = null;

}

function validarAlmuerzo() {

    const faltantes = [];

    if (!almuerzoActual.sopa)
        faltantes.push("Sopa");

    if (!almuerzoActual.proteina)
        faltantes.push("Proteína");

    if (!almuerzoActual.seco)
        faltantes.push("Seco");

    if (!almuerzoActual.ensalada)
        faltantes.push("Ensalada");

    if (!almuerzoActual.jugo)
        faltantes.push("Jugo");

    return faltantes;

}

/********************************************************************
 * UTILIDADES
 ********************************************************************/
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

function mostrarToast(msg, tipo = "success") {

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

function mostrarError(error) {

    mostrarToast(

        error,

        "error"

    );

}

function obtenerProductoSeleccionado(

    combo,

    lista

) {

    return buscarProducto(

        lista,

        combo.value

    );

}

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

function subirInicio() {

    window.scrollTo({

        top: 0,

        behavior: "smooth"

    });

}

function cerrarAutocomplete() {

    elementosDOM.listaClientes.innerHTML = "";

    elementosDOM.listaClientes.classList.add(

        "hidden"

    );

}

function mostrarCargando(mostrar) {

    if (!elementosDOM.loading)
        return;

    elementosDOM.loading.style.display =

        mostrar

            ? "flex"

            : "none";

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

function manejarEscapeModalCliente(event) {

    if (event.key !== "Escape") {

        return;

    }

    if (
        elementosDOM.modalClienteRapido.classList.contains("hidden")
    ) {

        return;

    }

    cerrarModalClienteRapido();

}

function cerrarModalClickFuera(event) {

    if (

        event.target === elementosDOM.modalClienteRapido

    ) {

        cerrarModalClienteRapido();

    }

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
= DEBUG
==============================================================*/

function debugPedido() {

    console.table(almuerzosPedido);

}

window.seleccionarMenu = seleccionarMenu;

window.editarAlmuerzo = editarAlmuerzo;

window.duplicarAlmuerzo = duplicarAlmuerzo;

window.eliminarAlmuerzo = eliminarAlmuerzo;

window.cancelarEdicion = cancelarEdicion;

window.debugPedido = debugPedido;

document.addEventListener(

    "DOMContentLoaded",

    init

);






