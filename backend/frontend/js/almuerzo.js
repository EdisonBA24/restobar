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

let catalogoMenus = [];

const preciosCatalogoCache = new Map();

/*const MENUS = {

    EJECUTIVO: {

        tipo: "MENU_EJECUTIVO",

        //nombre: "Menú Ejecutivo",
        nombre: "Menú del día",

        precio: 18500,

        precio_llevar: 19000

    },

    PREMIUM: {

        tipo: "MENU_PREMIUM",

        //nombre: "Menú Premium",
        nombre: "Especiales",

        precio: 25000

    },

    ESPECIAL: {

        tipo: "MENU_ESPECIAL",

        //nombre: "Menú Especial",
        nombre: "Cazuela",

        precio: 27000

    }

};
*/

const MODOS = {

    MENU: "MENU",

    ADICION: "ADICION"

};

/*const CABECERAS = {

    ADICION: {

        titulo: "🍽️ Agregar Adiciones",

        badge: "Adiciones del almuerzo",

        descripcion:
            "Seleccione cada uno de los componentes que desea agregar como adición."

    },

    MENU_EJECUTIVO: {

        titulo: "🍽️ Menú del Día",

        badge: "Menú del Día",

        descripcion:
            "Seleccione los componentes incluidos en el Menú del Día."

    },

    MENU_PREMIUM: {

        titulo: "⭐ Especiales",

        badge: "Especiales",

        descripcion:
            "Seleccione los componentes incluidos en los Especiales."

    },

    MENU_ESPECIAL: {

        titulo: "🥘 Cazuela",

        badge: "Cazuela",

        descripcion:
            "Seleccione los componentes incluidos en la Cazuela."

    }

};
*/
const CABECERAS = {

    ADICION: {

        titulo: "🍽️ Agregar Adiciones",

        badge: "Adiciones del almuerzo",

        descripcion:
            "Seleccione cada uno de los componentes que desea agregar como adición."

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

        mesa:
            document.getElementById(
                "mesa"
            ),

        grupoMesa:
            document.getElementById(
                "grupoMesa"
            ),

        cliente:
            document.getElementById(
                "cliente"
            ),

        listaClientes:
            document.getElementById(
                "listaClientes"
            ),

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

        camposAdicion:
            document.getElementById("camposAdicion"),

        categoriasCatalogoMenu:
            document.getElementById("categoriasCatalogoMenu"),

        catalogoMenusGrid:
            document.getElementById("catalogoMenusGrid"),

        resumenCatalogoMenu:
            document.getElementById("resumenCatalogoMenu"),

        /*=========================================
        = CONSTRUCTOR
        =========================================*/

        cboSopa:
            document.getElementById(
                "cboSopa"
            ),

        cboProteina:
            document.getElementById(
                "cboProteina"
            ),

        grupoProteina:
            document.getElementById(
                "grupoProteina"
            ),

        cboSeco:
            document.getElementById(
                "cboSeco"
            ),

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

        btnAgregarAdicionRapida:
            document.getElementById("btnAgregarAdicionRapida"),

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

    /*
     * =============================
     * SERVICIO POR DEFECTO
     * =============================
     *
     * El HTML inicia en LLEVAR.
     * Debemos reflejar ese valor
     * también en el estado JS.
     */

    tipoServicio =
        elementosDOM.tipoServicio?.value
        || "LLEVAR";

    /*
     * =============================
     * CARGAR COMPONENTES
     * =============================
     */

    await cargarComponentes();

    await cargarCatalogoMenus();

    /*
     * =============================
     * APLICAR SERVICIO
     * =============================
     */

    await cambiarTipoServicio();

    actualizarCabeceraConstructor();

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

    elementosDOM.btnAgregarAdicionRapida?.addEventListener(
        "click",
        agregarAdicionDesdePedido
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

    elementosDOM.categoriasCatalogoMenu?.addEventListener(
        "change",
        manejarCambioCategoriaCatalogo
    );

    elementosDOM.categoriasCatalogoMenu?.addEventListener(
        "click",
        manejarClickStepperCatalogo
    );

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

    direccionSeleccionada = null;

    if (elementosDOM.direccionEntrega) {

        elementosDOM.direccionEntrega.innerHTML = `

            <option value="">

                Seleccione una dirección...

            </option>

        `;

        elementosDOM.direccionEntrega.value =
            "";

    }

    if (elementosDOM.infoDirecciones) {

        elementosDOM.infoDirecciones.classList.add(
            "hidden"
        );

    }

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
/********************************************************************
 * CAMBIO DE TIPO DE ALMUERZO
 *
 * IMPORTANTE:
 * Cambiar entre Adición y Menús NO debe reiniciar los datos generales
 * del pedido ni crear un nuevo constructor innecesariamente.
 ********************************************************************/
function cambiarTipoAlmuerzo(configuracion) {

    if (!almuerzoActual) {
        crearNuevoAlmuerzo();
    }

    almuerzoActual.catalogoItemId = null;
    almuerzoActual.codigoCatalogo = null;
    almuerzoActual.lineaCodigo = null;
    almuerzoActual.tipoCatalogo = null;
    almuerzoActual.configuracionMenu = null;
    almuerzoActual.categoriasMenu = [];
    almuerzoActual.componentesSeleccionados = [];

    almuerzoActual.modo = configuracion.modo;
    almuerzoActual.tipo = configuracion.tipo;
    almuerzoActual.nombre = configuracion.nombre;
    almuerzoActual.precioBase = configuracion.precioBase;

    elementosDOM.camposAdicion.classList.remove("hidden");

    elementosDOM.categoriasCatalogoMenu.classList.add("hidden");

    elementosDOM.resumenCatalogoMenu.classList.add("hidden");

    almuerzoActual.calcularPrecio();

    actualizarCabeceraConstructor();

    actualizarSopasSegunTipo();

    actualizarProteinaSegunTipo();

    actualizarResumenActual();

}

/********************************************************************
 * VISIBILIDAD DE PROTEÍNA SEGÚN TIPO DE MENÚ
 ********************************************************************/

function actualizarProteinaSegunTipo() {

    if (
        !elementosDOM.grupoProteina
    ) {

        return;

    }

    const tipo =
        almuerzoActual?.tipo || "ADICION";

    /*
     * Especiales y Cazuela NO utilizan proteína.
     */

    const ocultarProteina =
        tipo === "MENU_PREMIUM"
        ||
        tipo === "MENU_ESPECIAL";


    /*
     * Ocultar / mostrar campo
     */

    if (
        ocultarProteina
    ) {

        elementosDOM.grupoProteina
            .classList.add("hidden");

        /*
         * Limpiar cualquier proteína
         * que hubiera quedado seleccionada
         * al cambiar desde otro menú.
         */

        if (
            almuerzoActual
        ) {

            almuerzoActual.proteina =
                null;

        }

        if (
            elementosDOM.cboProteina
        ) {

            elementosDOM.cboProteina.value =
                "";

        }

    }
    else {

        elementosDOM.grupoProteina
            .classList.remove("hidden");

    }

}

/********************************************************************
 * PRECIO DEL MENÚ DEL DÍA SEGÚN SERVICIO
 ********************************************************************/
/*
function obtenerPrecioMenu(tipoMenu) {

    const menu =
        MENUS[tipoMenu];

    if (!menu) {

        return 0;

    }
*/
/*
 * Solo Menú del Día cambia
 * de precio según servicio.
 */
/*
    if (
        tipoMenu === "EJECUTIVO"
        &&
        tipoServicio === "LLEVAR"
    ) {

        return menu.precio_llevar;

    }

    return menu.precio;

}
*/

/********************************************************************
 * SELECCIONAR MENÚ
 ********************************************************************/
/*
function seleccionarMenu(tipo) {

    const menu =
        MENUS[tipo];

    if (!menu) {

        console.warn(
            "No se encontró configuración para el menú:",
            tipo
        );

        return;

    }

    const precio =
        obtenerPrecioMenu(tipo);

    cambiarTipoAlmuerzo({

        modo: MODOS.MENU,

        tipo: menu.tipo,

        nombre: menu.nombre,

        precioBase: precio

    });

    elementosDOM.contenidoPedido
        ?.classList.remove("hidden");

    document
        .querySelectorAll(".tab-panel")
        .forEach(panel => {

            panel.classList.remove("active");

            panel.classList.add("hidden");

        });

    elementosDOM.panelConstruir
        ?.classList.remove("hidden");

    elementosDOM.panelConstruir
        ?.classList.add("active");

}
*/

function agregarAdicionDesdePedido() {

    // No cambiar de constructor mientras se edita
    // un artículo que ya está en el pedido.
    if (editandoId) {

        mostrarToast(
            "Finalice o cancele la edición actual antes de agregar otra adición.",
            "warning"
        );

        return;

    }

    // Si hay un menú en construcción y todavía no se ha
    // agregado, confirmar antes de descartarlo.
    if (almuerzoActual?.catalogoItemId) {

        const continuar = confirm(
            "Tiene un menú sin agregar. ¿Desea descartarlo y agregar una adición?"
        );

        if (!continuar)
            return;

    }

    const tarjetaAdiciones = [
        ...elementosDOM.tarjetasTipoPedido
    ].find(card =>
        card.dataset.panel === "panelConstruir"
    );

    if (!tarjetaAdiciones) {

        mostrarToast(
            "No se encontró el constructor de Adiciones.",
            "error"
        );

        return;

    }

    // =============================================
    // ACTIVAR PESTAÑA DE ADICIONES
    // =============================================

    elementosDOM.tarjetasTipoPedido.forEach(card => {

        card.classList.remove("active");

    });

    tarjetaAdiciones.classList.add("active");

    document.querySelectorAll(".tab-panel").forEach(panel => {

        panel.classList.remove("active");

        panel.classList.add("hidden");

    });

    elementosDOM.contenidoPedido.classList.remove("hidden");

    elementosDOM.panelConstruir.classList.remove("hidden");

    elementosDOM.panelConstruir.classList.add("active");

    // =============================================
    // CREAR UN CONSTRUCTOR LIMPIO
    // =============================================

    crearNuevoAlmuerzo();

    cambiarTipoAlmuerzo({

        modo: MODOS.ADICION,

        tipo: "ADICION",

        nombre: "Adición",

        precioBase: 0

    });

    // =============================================
    // DESPLAZAR A LOS COMPONENTES
    // =============================================

    desplazarAComponentesPedido(almuerzoActual);

}

/********************************************************************
 * SELECCIONAR TIPO DE PEDIDO
 ********************************************************************/
function seleccionarTipoPedido(card) {

    if (editandoId) {

        mostrarToast(
            "Finalice o cancele la edición antes de cambiar el tipo de constructor.",
            "warning"
        );

        return;

    }

    const panelDestino = card.dataset.panel;

    elementosDOM.tarjetasTipoPedido.forEach(tarjeta => {
        tarjeta.classList.remove("active");
    });

    card.classList.add("active");

    document.querySelectorAll(".tab-panel").forEach(panel => {

        panel.classList.remove("active");

        panel.classList.add("hidden");

    });

    const panel = document.getElementById(panelDestino);

    if (!panel)
        return;

    elementosDOM.contenidoPedido.classList.remove("hidden");

    panel.classList.remove("hidden");

    panel.classList.add("active");

    // La pestaña de Adiciones conserva sus cinco selectores.
    if (panelDestino === "panelConstruir") {

        if (almuerzoActual?.catalogoItemId) {

            const continuar = confirm(
                "Tiene un menú del catálogo sin agregar. ¿Desea descartarlo y cambiar a Adiciones?"
            );

            if (!continuar)
                return;

        }

        crearNuevoAlmuerzo();

        cambiarTipoAlmuerzo({

            modo: MODOS.ADICION,

            tipo: "ADICION",

            nombre: "Adición",

            precioBase: 0

        });

    }

}

/********************************************************************
 * FILTRO DE SOPAS SEGÚN MENÚ
 ********************************************************************/

/********************************************************************
 * SOPAS DISPONIBLES SEGÚN TIPO DE MENÚ
 ********************************************************************/

function obtenerSopasDisponibles(tipo) {

    const sopas =
        componentes.sopas || [];


    /*
     * ==========================================================
     * ADICIÓN
     * ==========================================================
     *
     * Una adición puede utilizar cualquier sopa disponible.
     */

    if (
        tipo === "ADICION"
        ||
        !tipo
    ) {

        return sopas;

    }


    /*
     * ==========================================================
     * MENÚ DEL DÍA
     * ==========================================================
     *
     * Permitimos:
     *
     *   SOPA DE SANCOCHO
     *
     * pero NO:
     *
     *   SANCOCHO
     *
     * Tampoco:
     *
     *   CAZUELA DE FRIJOL
     *   MONDONGO
     *   AJIACO
     */

    if (
        tipo === "MENU_EJECUTIVO"
    ) {

        return sopas.filter(
            sopa => {

                const nombre =
                    String(
                        sopa.nombre || ""
                    )
                        .trim()
                        .toUpperCase();

                /*
                 * SOPA DE SANCOCHO
                 *
                 * Es una opción válida
                 * para el Menú del Día.
                 */

                const esSopaDeSancocho =
                    nombre ===
                    "SOPA DE SANCOCHO";


                /*
                 * SANCOCHO
                 *
                 * El sancocho independiente
                 * NO se debe mostrar.
                 */

                const esSancocho =
                    nombre ===
                    "SANCOCHO";


                /*
                 * Otras sopas especiales
                 * tampoco están disponibles.
                 */

                const esCazuela =
                    nombre ===
                    "CAZUELA DE FRIJOL"
                    ||
                    nombre ===
                    "CAZUELA DE FRIJOLES";

                const esMondongo =
                    nombre ===
                    "MONDONGO";

                const esAjiaco =
                    nombre ===
                    "AJIACO"
                    ||
                    nombre ===
                    "AJÍACO";


                /*
                 * SOPA DE SANCOCHO sí pasa.
                 *
                 * Todo lo demás especial queda fuera.
                 */

                if (
                    esSopaDeSancocho
                ) {

                    return true;

                }

                return !(
                    esSancocho
                    ||
                    esCazuela
                    ||
                    esMondongo
                    ||
                    esAjiaco
                );

            }
        );

    }


    /*
     * ==========================================================
     * ESPECIALES
     * ==========================================================
     *
     * Debe mostrar:
     *
     *   SANCOCHO
     *   MONDONGO
     *   AJIACO
     *
     * y NO:
     *
     *   SOPA DE SANCOCHO
     */

    if (
        tipo === "MENU_PREMIUM"
    ) {

        return sopas.filter(
            sopa => {

                const nombre =
                    String(
                        sopa.nombre || ""
                    )
                        .trim()
                        .toUpperCase();

                return (
                    nombre === "SANCOCHO"
                    ||
                    nombre === "MONDONGO"
                    ||
                    nombre === "AJIACO"
                    ||
                    nombre === "AJÍACO"
                );

            }
        );

    }


    /*
     * ==========================================================
     * CAZUELA
     * ==========================================================
     *
     * Únicamente:
     *
     *   CAZUELA DE FRIJOL
     */

    if (
        tipo === "MENU_ESPECIAL"
    ) {

        return sopas.filter(
            sopa => {

                const nombre =
                    String(
                        sopa.nombre || ""
                    )
                        .trim()
                        .toUpperCase();

                return (
                    nombre ===
                    "CAZUELA DE FRIJOL"
                    ||
                    nombre ===
                    "CAZUELA DE FRIJOLES"
                );

            }
        );

    }


    return sopas;

}


function actualizarSopasSegunTipo() {

    if (!elementosDOM.cboSopa) {

        return;

    }

    const tipo =
        almuerzoActual?.tipo
        || "ADICION";

    const sopas =
        obtenerSopasDisponibles(tipo);

    llenarCombo(

        elementosDOM.cboSopa,

        sopas,

        "Seleccione una sopa"

    );

    /*
     * Si el almuerzo tenía una sopa seleccionada
     * que ya no es válida para el nuevo menú,
     * la eliminamos.
     */

    if (
        almuerzoActual?.sopa
        &&
        !sopas.some(
            sopa =>
                Number(sopa.id)
                ===
                Number(
                    almuerzoActual.sopa.id
                )
        )
    ) {

        almuerzoActual.sopa =
            null;

    }

    /*
     * Restaurar la sopa válida
     * cuando todavía corresponde.
     */

    if (
        almuerzoActual?.sopa
    ) {

        elementosDOM.cboSopa.value =
            almuerzoActual.sopa.id;

    }

    actualizarSeleccion();

}

async function cambiarTipoServicio() {

    // Actualizar el estado con el servicio seleccionado.
    tipoServicio = String(
        elementosDOM.tipoServicio?.value || "GENERAL"
    ).trim().toUpperCase();

    // Resolver nuevamente los precios según la modalidad.
    await actualizarPreciosCatalogoMenus();

    // =============================================
    // MESA
    // =============================================

    if (elementosDOM.grupoMesa) {

        if (tipoServicio === "MESA") {

            elementosDOM.grupoMesa.classList.remove("hidden");

        } else {

            elementosDOM.grupoMesa.classList.add("hidden");

            if (elementosDOM.mesa) {
                elementosDOM.mesa.value = "";
            }

            mesaSeleccionada = null;

        }

    }

    // =============================================
    // DOMICILIO
    // =============================================

    if (tipoServicio === "DOMICILIO") {

        elementosDOM.grupoDireccion?.classList.remove("hidden");

        if (clienteSeleccionado) {

            await cargarDireccionesCliente(
                clienteSeleccionado
            );

        } else {

            limpiarDirecciones();

        }

    } else {

        elementosDOM.grupoDireccion?.classList.add("hidden");

        limpiarDirecciones();

    }

    // =============================================
    // ACTUALIZAR RESUMEN
    // =============================================

    actualizarResumenActual();

}

/********************************************************************/

/********************************************************************
 * CONSTRUCTOR
 ********************************************************************/
function crearNuevoAlmuerzo() {

    almuerzoActual = new Almuerzo();

    elementosDOM.camposAdicion.classList.remove("hidden");

    elementosDOM.categoriasCatalogoMenu.classList.add("hidden");

    elementosDOM.resumenCatalogoMenu.classList.add("hidden");

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

    if (almuerzoActual.catalogoItemId) {

        elementosDOM.tituloConstructor.textContent =
            `🍽️ ${almuerzoActual.nombre}`;

        elementosDOM.badgeConstructor.textContent =
            "Configuración del catálogo";

        elementosDOM.descripcionConstructor.textContent =
            almuerzoActual.configuracionMenu?.instrucciones
            || "Seleccione los componentes disponibles para este menú.";

        return;

    }

    const config = CABECERAS.ADICION;

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

/* =====================================================
   CATALOGO COMERCIAL DE ALMUERZOS
===================================================== */

async function cargarCatalogoMenus() {

    try {

        const respuestaLineas = await apiFetch(
            "/catalogo/lineas"
        );

        if (respuestaLineas?.status !== "success") {
            throw new Error(
                respuestaLineas?.message ||
                "No fue posible consultar las líneas comerciales."
            );
        }

        const lineaAlmuerzos = (
            respuestaLineas.data || []
        ).find(linea =>
            String(linea.codigo || "").toUpperCase() === "ALMUERZOS"
        );

        if (!lineaAlmuerzos) {

            catalogoMenus = [];

            renderizarTarjetasCatalogoMenus();

            return;

        }

        const respuestaItems = await apiFetch(
            `/catalogo/items?linea_id=${lineaAlmuerzos.id}&page=1&page_size=100`
        );

        if (respuestaItems?.status !== "success") {
            throw new Error(
                respuestaItems?.message ||
                "No fue posible consultar los artículos de Almuerzos."
            );
        }

        const items = respuestaItems.data?.items || [];

        catalogoMenus = items.filter(item =>
            ["MENU", "COMBO"].includes(
                String(item.tipo_item || "").toUpperCase()
            )
        );

        await actualizarPreciosCatalogoMenus();

    } catch (error) {

        console.error(
            "Error cargando catálogo de Almuerzos:",
            error
        );

        catalogoMenus = [];

        renderizarTarjetasCatalogoMenus();

        mostrarError(
            error.message ||
            "No fue posible cargar los menús comerciales."
        );

    }

}


async function resolverPrecioCatalogo(itemId) {

    const servicio = tipoServicio || "GENERAL";

    const cacheKey = `${itemId}:${servicio}`;

    if (preciosCatalogoCache.has(cacheKey)) {
        return preciosCatalogoCache.get(cacheKey);
    }

    try {

        const respuesta = await apiFetch(
            `/catalogo/items/${itemId}/precio?tipo_servicio=${encodeURIComponent(servicio)}`
        );

        if (respuesta?.status !== "success") {
            preciosCatalogoCache.set(cacheKey, null);
            return null;
        }

        const precio = Number(respuesta.data?.precio);

        const resultado = Number.isFinite(precio)
            ? precio
            : null;

        preciosCatalogoCache.set(cacheKey, resultado);

        return resultado;

    } catch (error) {

        console.warn(
            `No hay precio disponible para el artículo ${itemId}:`,
            error.message
        );

        preciosCatalogoCache.set(cacheKey, null);

        return null;

    }

}


async function actualizarPreciosCatalogoMenus() {

    if (!catalogoMenus.length) {
        renderizarTarjetasCatalogoMenus();
        return;
    }

    await Promise.all(
        catalogoMenus.map(async menu => {

            menu.precioActual = await resolverPrecioCatalogo(
                menu.id
            );

        })
    );

    // Actualizar los menús que ya están en el pedido.
    for (const almuerzo of almuerzosPedido) {

        if (!almuerzo.catalogoItemId)
            continue;

        const menu = catalogoMenus.find(
            item =>
                Number(item.id) ===
                Number(almuerzo.catalogoItemId)
        );

        if (
            menu &&
            menu.precioActual !== null &&
            menu.precioActual !== undefined
        ) {

            almuerzo.precioBase = menu.precioActual;

            almuerzo.calcularPrecio();

        }

    }

    // Actualizar también el artículo que se está editando.
    if (almuerzoActual?.catalogoItemId) {

        const menuActual = catalogoMenus.find(
            item =>
                Number(item.id) ===
                Number(almuerzoActual.catalogoItemId)
        );

        if (
            menuActual &&
            menuActual.precioActual !== null &&
            menuActual.precioActual !== undefined
        ) {

            almuerzoActual.precioBase =
                menuActual.precioActual;

            almuerzoActual.calcularPrecio();

        }

    }

    renderizarTarjetasCatalogoMenus();

    actualizarResumenActual();

    renderPedido();

}


function renderizarTarjetasCatalogoMenus() {

    const contenedor = elementosDOM.catalogoMenusGrid;

    if (!contenedor)
        return;

    contenedor.innerHTML = "";

    if (!catalogoMenus.length) {

        const vacio = document.createElement("div");

        vacio.className = "almuerzo-catalogo-vacio";

        vacio.textContent =
            "No hay menús o combos activos configurados para Almuerzos.";

        contenedor.appendChild(vacio);

        return;

    }

    catalogoMenus.forEach(menu => {

        // =============================================
        // TARJETA
        // =============================================

        const tarjeta = document.createElement("article");

        tarjeta.className = "almuerzo-catalogo-card";

        // =============================================
        // IMAGEN
        // =============================================

        const media = document.createElement("div");

        media.className = "almuerzo-catalogo-image";

        const imagenUrl = String(
            menu.imagen_url || ""
        ).trim();

        const esImagenSegura = /^https?:\/\//i.test(
            imagenUrl
        );

        const crearPlaceholder = () => {

            const placeholder = document.createElement("div");

            placeholder.className =
                "almuerzo-catalogo-placeholder";

            placeholder.textContent =
                String(menu.tipo_item).toUpperCase() === "COMBO"
                    ? "🍱"
                    : "🍽️";

            return placeholder;

        };

        if (esImagenSegura) {

            const imagen = document.createElement("img");

            imagen.src = imagenUrl;

            imagen.alt = menu.nombre || "Menú";

            imagen.loading = "lazy";

            imagen.addEventListener(
                "error",
                () => {

                    imagen.remove();

                    if (!media.querySelector(
                        ".almuerzo-catalogo-placeholder"
                    )) {

                        media.appendChild(
                            crearPlaceholder()
                        );

                    }

                },
                { once: true }
            );

            media.appendChild(imagen);

        } else {

            media.appendChild(
                crearPlaceholder()
            );

        }

        // =============================================
        // ETIQUETA DEL TIPO DE ARTICULO
        // =============================================

        const tipo = document.createElement("span");

        tipo.className = "almuerzo-catalogo-badge";

        tipo.textContent = menu.tipo_item || "MENU";

        media.appendChild(tipo);

        // =============================================
        // DESTACADO
        // =============================================

        if (menu.destacado) {

            const destacado = document.createElement("span");

            destacado.className =
                "almuerzo-catalogo-featured";

            destacado.textContent = "Destacado";

            media.appendChild(destacado);

        }

        // =============================================
        // CONTENIDO
        // =============================================

        const contenido = document.createElement("div");

        contenido.className =
            "almuerzo-catalogo-content";

        const nombre = document.createElement("h3");

        nombre.textContent =
            menu.nombre || "Artículo comercial";

        const codigo = document.createElement("small");

        codigo.textContent = menu.codigo || "";

        const descripcion = document.createElement("p");

        descripcion.className =
            "almuerzo-catalogo-description";

        descripcion.textContent =
            menu.descripcion || "Menú configurado por administración.";

        // =============================================
        // PRECIO Y CATEGORIA
        // =============================================

        const meta = document.createElement("div");

        meta.className = "almuerzo-catalogo-meta";

        const categoria = document.createElement("span");

        categoria.textContent =
            menu.categoria_nombre || "Almuerzos";

        const precio = document.createElement("strong");

        const precioDisponible =
            menu.precioActual !== null &&
            menu.precioActual !== undefined;

        precio.textContent = precioDisponible
            ? formatearMoneda(menu.precioActual)
            : "Sin precio";

        meta.appendChild(categoria);

        meta.appendChild(precio);

        // =============================================
        // BOTON
        // =============================================

        const boton = document.createElement("button");

        boton.type = "button";

        boton.className =
            "almuerzo-catalogo-button";

        boton.textContent = precioDisponible
            ? "Seleccionar menú"
            : "Precio no configurado";

        boton.disabled = !precioDisponible;

        boton.addEventListener("click", () => {

            seleccionarMenuCatalogo(menu.id);

        });

        // =============================================
        // ARMAR TARJETA
        // =============================================

        contenido.appendChild(nombre);

        contenido.appendChild(codigo);

        contenido.appendChild(descripcion);

        contenido.appendChild(meta);

        contenido.appendChild(boton);

        tarjeta.appendChild(media);

        tarjeta.appendChild(contenido);

        contenedor.appendChild(tarjeta);

    });

}


function crearComponenteCatalogo(
    categoria,
    producto
) {

    const precioAdicional = Number(
        producto.precio_adicional || 0
    );

    return {

        menu_categoria_id: Number(categoria.id),

        categoria_codigo: categoria.codigo || null,

        categoria_nombre: categoria.nombre,

        producto_id: Number(producto.producto_id),

        producto_nombre: producto.producto_nombre,

        cantidad: 1,

        precio_adicional_unitario: precioAdicional,

        subtotal_adicional: precioAdicional,

        predeterminado: Boolean(producto.predeterminado),

        orden_categoria: Number(categoria.orden || 0),

        orden_producto: Number(producto.orden || 0)

    };

}


function obtenerComponentesPredeterminados(categorias) {

    const seleccionados = [];

    (categorias || []).forEach(categoria => {

        (categoria.productos || [])
            .filter(producto => Boolean(producto.predeterminado))
            .forEach(producto => {

                seleccionados.push(
                    crearComponenteCatalogo(
                        categoria,
                        producto
                    )
                );

            });

    });

    return seleccionados;

}


async function seleccionarMenuCatalogo(itemId) {

    const menu = catalogoMenus.find(
        item => Number(item.id) === Number(itemId)
    );

    if (!menu)
        return;

    try {

        mostrarCargando(true);

        // Consultar el precio vigente en el servidor
        // en lugar de reutilizar el valor almacenado en caché.

        preciosCatalogoCache.delete(
            `${itemId}:${tipoServicio || "GENERAL"}`
        );

        const [respuestaConfiguracion, precio] = await Promise.all([

            apiFetch(
                `/catalogo/items/${itemId}/configuracion-menu`
            ),

            resolverPrecioCatalogo(itemId)

        ]);

        if (respuestaConfiguracion?.status !== "success") {

            throw new Error(
                respuestaConfiguracion?.message ||
                "No fue posible consultar la configuración del menú."
            );

        }

        if (precio === null) {

            throw new Error(
                "Este menú no tiene un precio configurado para el tipo de servicio seleccionado."
            );

        }

        const configuracion = respuestaConfiguracion.data;

        if (!configuracion?.categorias?.length) {

            throw new Error(
                "Este menú todavía no tiene categorías configuradas."
            );

        }

        const nuevo = new Almuerzo();

        nuevo.modo = MODOS.MENU;

        nuevo.tipo = String(menu.tipo_item).toUpperCase();

        nuevo.nombre = menu.nombre;

        nuevo.precioBase = precio;

        nuevo.catalogoItemId = Number(menu.id);

        nuevo.codigoCatalogo = menu.codigo || null;

        nuevo.lineaCodigo = menu.linea_codigo || "ALMUERZOS";

        nuevo.tipoCatalogo = nuevo.tipo;

        nuevo.configuracionMenu = (
            configuracion.configuracion || {}
        );

        nuevo.categoriasMenu = configuracion.categorias || [];

        nuevo.componentesSeleccionados =
            obtenerComponentesPredeterminados(
                nuevo.categoriasMenu
            );

        nuevo.observaciones = "";

        nuevo.calcularPrecio();

        almuerzoActual = nuevo;

        editandoId = null;

        elementosDOM.txtObservaciones.value = "";

        elementosDOM.camposAdicion.classList.add("hidden");

        elementosDOM.categoriasCatalogoMenu.classList.remove("hidden");

        renderizarCategoriasCatalogoMenu(almuerzoActual);

        elementosDOM.contenidoPedido.classList.remove("hidden");

        document.querySelectorAll(".tab-panel").forEach(panel => {

            panel.classList.remove("active");

            panel.classList.add("hidden");

        });

        elementosDOM.panelConstruir.classList.remove("hidden");

        elementosDOM.panelConstruir.classList.add("active");

        actualizarCabeceraConstructor();

        actualizarEstadoEdicion();

        actualizarResumenActual();

        // =============================================
        // DESPLAZAR HACIA LOS COMPONENTES DEL MENU
        // =============================================

        requestAnimationFrame(() => {

            const contenedor =
                elementosDOM.categoriasCatalogoMenu;

            if (!contenedor)
                return;

            const primeraCategoria = contenedor.querySelector(
                ".catalogo-categoria"
            );

            const destino = primeraCategoria || contenedor;

            const posicion =
                destino.getBoundingClientRect().top +
                window.scrollY -
                100;

            window.scrollTo({

                top: Math.max(0, posicion),

                behavior: "smooth"

            });

        });

    } catch (error) {

        console.error(
            "Error seleccionando menú del catálogo:",
            error
        );

        mostrarError(error.message);

    } finally {

        mostrarCargando(false);

    }

}


function renderizarCategoriasCatalogoMenu(almuerzo) {

    const contenedor = elementosDOM.categoriasCatalogoMenu;

    if (!contenedor) return;

    contenedor.innerHTML = "";

    const categorias = almuerzo?.categoriasMenu || [];

    const permitePersonalizar =
        almuerzo?.configuracionMenu?.permite_personalizar !== false;

    if (!categorias.length) {

        contenedor.textContent =
            "Este menú no tiene categorías configuradas.";

        return;

    }

    categorias.forEach(categoria => {

        const seccion = document.createElement("section");

        seccion.className = "catalogo-categoria";

        const titulo = document.createElement("h3");

        titulo.textContent = categoria.nombre;

        const min = Number(
            categoria.min_selecciones || 0
        );

        const max = Number(
            categoria.max_selecciones || 0
        );

        const esObligatoria = Boolean(
            categoria.obligatorio
        );

        const minimoReal = esObligatoria
            ? Math.max(1, min)
            : 0;

        const regla = document.createElement("p");

        regla.className = "catalogo-categoria-regla";

        if (!esObligatoria) {

            regla.textContent = max > 0
                ? `Opcional. Puede omitirla o seleccionar hasta ${max} opción(es).`
                : "Opcional. Puede omitir esta categoría.";

        } else {

            regla.textContent = max > 0
                ? `Obligatoria. Seleccione entre ${minimoReal} y ${max} opción(es).`
                : `Obligatoria. Seleccione mínimo ${minimoReal} opción(es).`;

        }

        seccion.appendChild(titulo);

        if (categoria.descripcion) {

            const descripcion = document.createElement("p");

            descripcion.className = "catalogo-categoria-descripcion";

            descripcion.textContent = categoria.descripcion;

            seccion.appendChild(descripcion);

        }

        seccion.appendChild(regla);

        const productos = categoria.productos || [];

        const seleccionados = (
            almuerzo.componentesSeleccionados || []
        ).filter(componente =>
            Number(componente.menu_categoria_id) ===
            Number(categoria.id)
        );

        if (!productos.length) {

            const mensaje = document.createElement("p");

            mensaje.textContent =
                "No hay productos activos asociados a esta categoría.";

            seccion.appendChild(mensaje);

            contenedor.appendChild(seccion);

            return;

        }

        // =============================================
        // CATEGORÍA CON UNA SOLA SELECCIÓN
        // =============================================

        if (max === 1) {

            const select = document.createElement("select");

            select.dataset.categoriaId = categoria.id;

            select.disabled = !permitePersonalizar;

            const opcionInicial = document.createElement("option");

            opcionInicial.value = "";

            opcionInicial.textContent = minimoReal > 0
                ? "Seleccione una opción"
                : "Sin selección";

            select.appendChild(opcionInicial);

            productos.forEach(producto => {

                const opcion = document.createElement("option");

                opcion.value = producto.producto_id;

                const adicional = Number(
                    producto.precio_adicional || 0
                );

                opcion.textContent = adicional > 0
                    ? `${producto.producto_nombre} (+${formatearMoneda(adicional)})`
                    : producto.producto_nombre;

                select.appendChild(opcion);

            });

            const predeterminado = seleccionados[0];

            select.value = predeterminado
                ? String(predeterminado.producto_id)
                : "";

            seccion.appendChild(select);

        }

        // =============================================
        // PERMITE REPETIR PRODUCTOS: CONTROL + / -
        // =============================================

        else if (categoria.permitir_repetidos) {

            const lista = document.createElement("div");

            lista.className = "catalogo-opciones";

            productos.forEach(producto => {

                const fila = document.createElement("div");

                fila.className =
                    "catalogo-opcion catalogo-opcion--stepper";

                // -------------------------------------
                // NOMBRE DEL PRODUCTO
                // -------------------------------------

                const nombre = document.createElement("span");

                nombre.className = "catalogo-opcion-nombre";

                nombre.textContent = producto.producto_nombre;

                // -------------------------------------
                // CANTIDAD PREVIAMENTE SELECCIONADA
                // -------------------------------------

                const cantidadSeleccionada = seleccionados.reduce(
                    (total, componente) => {

                        if (
                            Number(componente.producto_id) ===
                            Number(producto.producto_id)
                        ) {

                            return total + Number(
                                componente.cantidad || 1
                            );

                        }

                        return total;

                    },
                    0
                );

                // -------------------------------------
                // CONTROL DE CANTIDAD
                // -------------------------------------

                const stepper = document.createElement("div");

                stepper.className = "catalogo-stepper";

                stepper.setAttribute("role", "group");

                stepper.setAttribute(
                    "aria-label",
                    `Cantidad de ${producto.producto_nombre}`
                );

                // BOTÓN DISMINUIR

                const btnMenos = document.createElement("button");

                btnMenos.type = "button";

                btnMenos.className =
                    "catalogo-stepper-btn catalogo-stepper-minus";

                btnMenos.dataset.stepperAction = "decrement";

                btnMenos.dataset.stepperCategoriaId = categoria.id;

                btnMenos.dataset.stepperProductoId =
                    producto.producto_id;

                btnMenos.textContent = "−";

                btnMenos.setAttribute(
                    "aria-label",
                    `Disminuir ${producto.producto_nombre}`
                );

                // CONTADOR

                const contador = document.createElement("span");

                contador.className = "catalogo-stepper-value";

                contador.dataset.categoriaId = categoria.id;

                contador.dataset.productoId = producto.producto_id;

                contador.dataset.cantidad = cantidadSeleccionada;

                contador.textContent = cantidadSeleccionada;

                contador.setAttribute("aria-live", "polite");

                // BOTÓN AUMENTAR

                const btnMas = document.createElement("button");

                btnMas.type = "button";

                btnMas.className =
                    "catalogo-stepper-btn catalogo-stepper-plus";

                btnMas.dataset.stepperAction = "increment";

                btnMas.dataset.stepperCategoriaId = categoria.id;

                btnMas.dataset.stepperProductoId =
                    producto.producto_id;

                btnMas.textContent = "+";

                btnMas.setAttribute(
                    "aria-label",
                    `Aumentar ${producto.producto_nombre}`
                );

                // -------------------------------------
                // ESTADO INICIAL
                // -------------------------------------

                btnMenos.disabled =
                    !permitePersonalizar ||
                    cantidadSeleccionada <= 0;

                btnMas.disabled = !permitePersonalizar;

                stepper.appendChild(btnMenos);

                stepper.appendChild(contador);

                stepper.appendChild(btnMas);

                // -------------------------------------
                // PRECIO ADICIONAL
                // -------------------------------------

                const adicional = Number(
                    producto.precio_adicional || 0
                );

                fila.appendChild(nombre);

                fila.appendChild(stepper);

                if (adicional > 0) {

                    const precioExtra = document.createElement("small");

                    precioExtra.textContent =
                        `+ ${formatearMoneda(adicional)} por unidad`;

                    fila.appendChild(precioExtra);

                }

                lista.appendChild(fila);

            });

            seccion.appendChild(lista);

        }

        // =============================================
        // SELECCIÓN NORMAL SIN REPETICIONES
        // =============================================

        else {

            const lista = document.createElement("div");

            lista.className = "catalogo-opciones";

            productos.forEach(producto => {

                const fila = document.createElement("label");

                fila.className = "catalogo-opcion";

                const input = document.createElement("input");

                input.type = "checkbox";

                input.value = producto.producto_id;

                input.dataset.categoriaId = categoria.id;

                input.disabled = !permitePersonalizar;

                input.checked = seleccionados.some(componente =>
                    Number(componente.producto_id) ===
                    Number(producto.producto_id)
                );

                const nombre = document.createElement("span");

                nombre.textContent = producto.producto_nombre;

                fila.appendChild(input);

                fila.appendChild(nombre);

                const adicional = Number(
                    producto.precio_adicional || 0
                );

                if (adicional > 0) {

                    const precioExtra = document.createElement("small");

                    precioExtra.textContent =
                        `+ ${formatearMoneda(adicional)}`;

                    fila.appendChild(precioExtra);

                }

                lista.appendChild(fila);

            });

            seccion.appendChild(lista);

        }

        if (!permitePersonalizar) {

            const aviso = document.createElement("small");

            aviso.className = "catalogo-categoria-regla";

            aviso.textContent =
                "Esta categoría utiliza los componentes predeterminados.";

            seccion.appendChild(aviso);

        }

        contenedor.appendChild(seccion);

    });

}


// =====================================================
// ACTUALIZAR ESTADO DE LOS CONTROLES + / -
// =====================================================

function actualizarEstadoStepperCategoria(categoria) {

    const categoriaId = Number(categoria.id);

    const contadores =
        elementosDOM.categoriasCatalogoMenu.querySelectorAll(
            `.catalogo-stepper-value[data-categoria-id="${categoriaId}"]`
        );

    const maximo = Number(
        categoria.max_selecciones || 0
    );

    const permitePersonalizar =
        almuerzoActual?.configuracionMenu?.permite_personalizar !== false;

    // Total seleccionado en toda la categoría.
    const totalSeleccionado = Array.from(contadores).reduce(
        (total, contador) => {

            return total + Math.max(
                0,
                Number(contador.dataset.cantidad || 0)
            );

        },
        0
    );

    contadores.forEach(contador => {

        const cantidad = Number(
            contador.dataset.cantidad || 0
        );

        const stepper = contador.closest(
            ".catalogo-stepper"
        );

        if (!stepper)
            return;

        const btnMenos = stepper.querySelector(
            ".catalogo-stepper-minus"
        );

        const btnMas = stepper.querySelector(
            ".catalogo-stepper-plus"
        );

        if (btnMenos) {

            btnMenos.disabled =
                !permitePersonalizar ||
                cantidad <= 0;

        }

        if (btnMas) {

            btnMas.disabled =
                !permitePersonalizar ||
                (
                    maximo > 0 &&
                    totalSeleccionado >= maximo
                );

        }

    });

}


// =====================================================
// MANEJAR BOTONES + / -
// =====================================================

function manejarClickStepperCatalogo(event) {

    const boton = event.target.closest(
        ".catalogo-stepper-btn"
    );

    if (!boton)
        return;

    if (
        !elementosDOM.categoriasCatalogoMenu.contains(
            boton
        )
    ) {
        return;
    }

    if (boton.disabled)
        return;

    const categoriaId = Number(
        boton.dataset.stepperCategoriaId
    );

    const productoId = Number(
        boton.dataset.stepperProductoId
    );

    const categoria = almuerzoActual?.categoriasMenu?.find(
        item => Number(item.id) === categoriaId
    );

    if (!categoria)
        return;

    const contador =
        elementosDOM.categoriasCatalogoMenu.querySelector(
            `.catalogo-stepper-value[data-categoria-id="${categoriaId}"][data-producto-id="${productoId}"]`
        );

    if (!contador)
        return;

    let cantidadActual = Math.max(
        0,
        Number(contador.dataset.cantidad || 0)
    );

    const maximo = Number(
        categoria.max_selecciones || 0
    );

    // =============================================
    // AUMENTAR
    // =============================================

    if (
        boton.dataset.stepperAction === "increment"
    ) {

        const contadores =
            elementosDOM.categoriasCatalogoMenu.querySelectorAll(
                `.catalogo-stepper-value[data-categoria-id="${categoriaId}"]`
            );

        const totalSeleccionado = Array.from(
            contadores
        ).reduce(
            (total, item) => {

                return total + Number(
                    item.dataset.cantidad || 0
                );

            },
            0
        );

        if (
            maximo > 0 &&
            totalSeleccionado >= maximo
        ) {

            mostrarToast(
                `La categoría ${categoria.nombre} permite máximo ${maximo} selección(es).`,
                "warning"
            );

            return;

        }

        cantidadActual++;

    }

    // =============================================
    // DISMINUIR
    // =============================================

    else if (
        boton.dataset.stepperAction === "decrement"
    ) {

        cantidadActual = Math.max(
            0,
            cantidadActual - 1
        );

    } else {

        return;

    }

    // =============================================
    // ACTUALIZAR CONTADOR
    // =============================================

    contador.dataset.cantidad = cantidadActual;

    contador.textContent = cantidadActual;

    // Actualizar disponibilidad de todos los
    // botones pertenecientes a esta categoría.
    actualizarEstadoStepperCategoria(categoria);

    // Recalcular precio y componentes seleccionados.
    actualizarSeleccionCatalogo();

}


function manejarCambioCategoriaCatalogo(event) {

    const control = event.target;

    if (!control?.dataset?.categoriaId)
        return;

    const categoriaId = control.dataset.categoriaId;

    const categoria = almuerzoActual?.categoriasMenu?.find(
        item =>
            Number(item.id) === Number(categoriaId)
    );

    if (!categoria)
        return;

    const max = Number(
        categoria.max_selecciones || 0
    );

    // =============================================
    // CONTROL DE CANTIDADES REPETIDAS
    // =============================================

    if (control.type === "number") {

        let cantidad = Math.max(
            0,
            parseInt(control.value || "0", 10) || 0
        );

        const controles = elementosDOM.categoriasCatalogoMenu
            .querySelectorAll(
                `input[type="number"][data-categoria-id="${categoriaId}"]`
            );

        let otrasCantidades = 0;

        controles.forEach(input => {

            if (input !== control) {

                otrasCantidades += Math.max(
                    0,
                    parseInt(input.value || "0", 10) || 0
                );

            }

        });

        if (max > 0) {

            const disponible = Math.max(
                0,
                max - otrasCantidades
            );

            if (cantidad > disponible) {

                cantidad = disponible;

                mostrarToast(
                    `La categoría ${categoria.nombre} permite máximo ${max} selección(es).`,
                    "warning"
                );

            }

        }

        control.value = cantidad;

    }

    // =============================================
    // CONTROL DE CHECKBOX
    // =============================================

    if (
        control.type === "checkbox" &&
        control.checked &&
        max > 0
    ) {

        const seleccionados = elementosDOM.categoriasCatalogoMenu
            .querySelectorAll(
                `input[type="checkbox"][data-categoria-id="${categoriaId}"]:checked`
            ).length;

        if (seleccionados > max) {

            control.checked = false;

            mostrarToast(
                `La categoría ${categoria.nombre} permite máximo ${max} selección(es).`,
                "warning"
            );

            return;

        }

    }

    actualizarSeleccionCatalogo();

}


function actualizarSeleccionCatalogo() {

    if (!almuerzoActual?.catalogoItemId)
        return;

    const seleccionados = [];

    (almuerzoActual.categoriasMenu || []).forEach(categoria => {

        const controles =
            elementosDOM.categoriasCatalogoMenu.querySelectorAll(
                `[data-categoria-id="${categoria.id}"]`
            );

        controles.forEach(control => {

            // =====================================
            // SELECT: MAXIMO 1
            // =====================================

            if (control.tagName === "SELECT") {

                if (!control.value)
                    return;

                const producto = categoria.productos.find(
                    item =>
                        Number(item.producto_id) ===
                        Number(control.value)
                );

                if (producto) {

                    seleccionados.push(
                        crearComponenteCatalogo(
                            categoria,
                            producto
                        )
                    );

                }

                return;

            }

            // =====================================
            // STEPPER: PRODUCTOS REPETIBLES
            // =====================================

            if (
                control.classList.contains(
                    "catalogo-stepper-value"
                )
            ) {

                const cantidad = Math.max(
                    0,
                    parseInt(
                        control.dataset.cantidad || "0",
                        10
                    ) || 0
                );

                if (cantidad <= 0)
                    return;

                const producto = categoria.productos.find(
                    item =>
                        Number(item.producto_id) ===
                        Number(control.dataset.productoId)
                );

                if (!producto)
                    return;

                const componente = crearComponenteCatalogo(
                    categoria,
                    producto
                );

                // Una sola fila con la cantidad acumulada.
                componente.cantidad = cantidad;

                componente.subtotal_adicional = Number(
                    (
                        Number(componente.precio_adicional_unitario || 0) *
                        cantidad
                    ).toFixed(2)
                );

                seleccionados.push(componente);

                return;

            }

            // =====================================
            // CHECKBOX: SIN REPETICIONES
            // =====================================

            if (
                control.type === "checkbox" &&
                control.checked
            ) {

                const producto = categoria.productos.find(
                    item =>
                        Number(item.producto_id) ===
                        Number(control.value)
                );

                if (producto) {

                    seleccionados.push(
                        crearComponenteCatalogo(
                            categoria,
                            producto
                        )
                    );

                }

            }

        });

    });

    almuerzoActual.componentesSeleccionados =
        seleccionados;

    almuerzoActual.calcularPrecio();

    actualizarResumenActual();

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

    if (almuerzo.catalogoItemId) {

        elementosDOM.panelConstruir.classList.remove("active");

        elementosDOM.panelConstruir.classList.add("hidden");

        elementosDOM.panelMenus.classList.remove("hidden");

        elementosDOM.panelMenus.classList.add("active");

        elementosDOM.tarjetasTipoPedido.forEach(card => {

            card.classList.toggle(
                "active",
                card.dataset.panel === "panelMenus"
            );

        });

    }

}

function desplazarAComponentesPedido(almuerzo = almuerzoActual) {

    requestAnimationFrame(() => {

        let destino = null;

        if (almuerzo?.catalogoItemId) {

            // Menú comercial: llevar al usuario
            // a las categorías de su composición.
            destino =
                elementosDOM.categoriasCatalogoMenu
                    ?.querySelector(".catalogo-categoria")
                || elementosDOM.categoriasCatalogoMenu;

        } else {

            // Adición: llevar a los selectores actuales.
            destino = elementosDOM.camposAdicion;

        }

        if (!destino)
            return;

        const posicion =
            destino.getBoundingClientRect().top +
            window.scrollY -
            110;

        window.scrollTo({

            top: Math.max(0, posicion),

            behavior: "smooth"

        });

    });

}

function editarAlmuerzo(id) {

    const almuerzo = almuerzosPedido.find(

        item => item.id === id

    );

    if (!almuerzo)
        return;

    editandoId = id;

    almuerzoActual = almuerzo.duplicar();

    if (almuerzoActual.catalogoItemId) {

        elementosDOM.camposAdicion.classList.add("hidden");

        elementosDOM.categoriasCatalogoMenu.classList.remove("hidden");

        renderizarCategoriasCatalogoMenu(almuerzoActual);

    } else {

        elementosDOM.camposAdicion.classList.remove("hidden");

        elementosDOM.categoriasCatalogoMenu.classList.add("hidden");

    }

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

    desplazarAComponentesPedido(almuerzoActual);

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

                ${almuerzo.catalogoItemId

            ? generarComponentesCatalogoCard(almuerzo)

            : `

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

                    `
        }

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

    if (!almuerzoActual)
        return;

    almuerzoActual.calcularPrecio();

    elementosDOM.lblTipoPedido.textContent =
        almuerzoActual.nombre;

    elementosDOM.lblEstadoPedido.textContent =
        almuerzoActual.catalogoItemId
            ? "Menú del catálogo"
            : "Adición al pedido";

    const resumenDinamico =
        elementosDOM.resumenCatalogoMenu;

    const resumenLegacy = [
        elementosDOM.resSopa,
        elementosDOM.resProteina,
        elementosDOM.resSeco,
        elementosDOM.resEnsalada,
        elementosDOM.resJugo
    ];

    if (almuerzoActual.catalogoItemId) {

        resumenLegacy.forEach(elemento => {
            elemento.closest(".builder-item")?.classList.add("hidden");
        });

        resumenDinamico.classList.remove("hidden");

        resumenDinamico.innerHTML = "";

        if (!almuerzoActual.componentesSeleccionados.length) {

            const mensaje = document.createElement("p");

            mensaje.textContent =
                "Todavía no hay componentes seleccionados.";

            resumenDinamico.appendChild(mensaje);

        }

        almuerzoActual.componentesSeleccionados.forEach(componente => {

            const fila = document.createElement("div");

            fila.className = "builder-item";

            const categoria = document.createElement("span");

            categoria.textContent =
                `${componente.categoria_nombre}: `;

            const producto = document.createElement("strong");

            const cantidad = Number(
                componente.cantidad || 1
            );

            producto.textContent = cantidad > 1
                ? `${componente.producto_nombre} × ${cantidad}`
                : componente.producto_nombre;

            fila.appendChild(categoria);

            fila.appendChild(producto);

            resumenDinamico.appendChild(fila);

        });

    } else {

        resumenDinamico.classList.add("hidden");

        resumenLegacy.forEach(elemento => {
            elemento.closest(".builder-item")?.classList.remove("hidden");
        });

        elementosDOM.resSopa.textContent =
            almuerzoActual.sopa?.nombre || "Sin seleccionar";

        elementosDOM.resProteina.textContent =
            almuerzoActual.proteina?.nombre || "Sin seleccionar";

        elementosDOM.resSeco.textContent =
            almuerzoActual.seco?.nombre || "Sin seleccionar";

        elementosDOM.resEnsalada.textContent =
            almuerzoActual.ensalada?.nombre || "Sin seleccionar";

        elementosDOM.resJugo.textContent =
            almuerzoActual.jugo?.nombre || "Sin seleccionar";

        actualizarEstadoResumen(elementosDOM.resSopa);

        actualizarEstadoResumen(elementosDOM.resProteina);

        actualizarEstadoResumen(elementosDOM.resSeco);

        actualizarEstadoResumen(elementosDOM.resEnsalada);

        actualizarEstadoResumen(elementosDOM.resJugo);

    }

    elementosDOM.lblSubtotal.textContent =
        formatearMoneda(almuerzoActual.precio);

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


function generarComponentesCatalogoCard(almuerzo) {

    return (almuerzo.componentesSeleccionados || [])
        .map(componente => `

            <div class="pedido-componente">

                <label>
                    ${escaparHTML(componente.categoria_nombre)}
                </label>

                <span>
                    ${escaparHTML(componente.producto_nombre)}
                    ${
                        Number(componente.cantidad || 1) > 1
                        ? ` × ${Number(componente.cantidad)}`
                        : ""
                    }
                </span>

            </div>

        `)
        .join("");

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
        item.catalogoItemId ||
        item.modo === MODOS.MENU
    ).length;

    const cantidadAdiciones = almuerzosPedido.filter(item =>
        !item.catalogoItemId &&
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

        // =====================================
        // ARTICULO DEL CATALOGO
        // =====================================

        if (almuerzo.catalogoItemId) {

            detalles.push({

                tipo_item: almuerzo.tipoCatalogo,

                catalogo_item_id: almuerzo.catalogoItemId,

                cantidad: 1,

                precio: almuerzo.precio,

                observaciones: almuerzo.observaciones,

                componentes: (
                    almuerzo.componentesSeleccionados || []
                ).map(componente => ({

                    menu_categoria_id:
                        componente.menu_categoria_id,

                    producto_id:
                        componente.producto_id,

                    cantidad:
                        componente.cantidad || 1

                }))

            });

            return;

        }

        // =====================================
        // ADICIONES EXISTENTES
        // =====================================

        const componentes = [];

        [
            almuerzo.sopa,
            almuerzo.proteina,
            almuerzo.seco,
            almuerzo.ensalada,
            almuerzo.jugo
        ].forEach(item => {

            if (!item)
                return;

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

    /*
     * ==========================================
     * LIMPIAR ITEMS DEL PEDIDO
     * ==========================================
     */

    limpiarPedido();


    /*
     * ==========================================
     * CLIENTE
     * ==========================================
     */

    if (
        elementosDOM.cliente
    ) {

        elementosDOM.cliente.value = "";

    }

    clienteSeleccionado = null;


    /*
     * ==========================================
     * SERVICIO
     * ==========================================
     *
     * El formulario vuelve a LLEVAR.
     */

    if (
        elementosDOM.tipoServicio
    ) {

        elementosDOM.tipoServicio.value =
            "LLEVAR";

    }

    tipoServicio = "LLEVAR";


    /*
     * ==========================================
     * MESA
     * ==========================================
     *
     * Al volver a LLEVAR, Mesa debe quedar
     * oculta y completamente limpia.
     */

    if (
        elementosDOM.grupoMesa
    ) {

        elementosDOM.grupoMesa
            .classList.add("hidden");

    }

    if (
        elementosDOM.mesa
    ) {

        elementosDOM.mesa.value = "";

    }

    mesaSeleccionada = null;


    /*
     * ==========================================
     * DIRECCIÓN
     * ==========================================
     */

    if (
        elementosDOM.grupoDireccion
    ) {

        elementosDOM.grupoDireccion
            .classList.add("hidden");

    }

    limpiarDirecciones();


    /*
     * ==========================================
     * REAPLICAR ESTADO DEL SERVICIO
     * ==========================================
     */

    actualizarResumenActual();

}

function validarAlmuerzo() {

    const faltantes = [];

    // =====================================
    // MENU DEL CATALOGO
    // =====================================

    if (almuerzoActual?.catalogoItemId) {

        const categorias =
            almuerzoActual.categoriasMenu || [];

        const componentes =
            almuerzoActual.componentesSeleccionados || [];

        if (!categorias.length) {

            return [
                "El menú no tiene categorías configuradas."
            ];

        }

        categorias.forEach(categoria => {

            const seleccionados = componentes.filter(
                componente =>
                    Number(componente.menu_categoria_id) ===
                    Number(categoria.id)
            ).length;

            let minimo = Number(
                categoria.min_selecciones || 0
            );

            const maximo = Number(
                categoria.max_selecciones || 0
            );

            if (categoria.obligatorio && minimo < 1) {
                minimo = 1;
            }

            if (
                categoria.obligatorio &&
                seleccionados < Math.max(1, minimo)
            ) {

                faltantes.push(
                    `${categoria.nombre}: mínimo ${Math.max(1, minimo)} selección(es)`
                );

            }

            if (
                maximo > 0 &&
                seleccionados > maximo
            ) {

                faltantes.push(
                    `${categoria.nombre}: máximo ${maximo} selección(es)`
                );

            }

        });

        return faltantes;

    }

    // =====================================
    // ADICIONES ACTUALES
    // =====================================

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

            if (almuerzo.catalogoItemId) {

                return total +
                    (almuerzo.componentesSeleccionados || []).length;

            }

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

window.editarAlmuerzo = editarAlmuerzo;

window.duplicarAlmuerzo = duplicarAlmuerzo;

window.eliminarAlmuerzo = eliminarAlmuerzo;

window.cancelarEdicion = cancelarEdicion;

window.debugPedido = debugPedido;

document.addEventListener(

    "DOMContentLoaded",

    init

);






