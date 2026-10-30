
import { apiFetch } from "./api.js";
import { TablaUI } from "./tablas.js";

// =====================================================
// CONFIGURACION Y ESTADO
// =====================================================

const STORAGE_PAGE_SIZE = "usuarios_page_size";

let tablaUsuarios = null;

let usuariosPagina = [];

let usuarioEditandoId = null;

let timeoutBusqueda = null;

let solicitudActual = 0;


// =====================================================
// HELPERS
// =====================================================

function getEl(id) {
    return document.getElementById(id);
}


function setText(id, texto) {

    const elemento = getEl(id);

    if (elemento) {
        elemento.textContent = texto;
    }

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


// =====================================================
// INICIALIZACION
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {

    if (!getEl("tablaUsuarios")) {
        return;
    }

    // =============================================
    // TABLA UI
    // =============================================

    tablaUsuarios = new TablaUI({

        nombre: "usuarios",

        callback: () => cargarUsuarios(),

        tabla: "#tablaUsuariosTabla",

        pageSize: "#pageSizeUsuarios",

        btnAnterior: "#btnPaginaAnteriorUsuarios",

        btnSiguiente: "#btnPaginaSiguienteUsuarios",

        numeros: "#numerosPaginacionUsuarios",

        resumen: "#resumenPaginacionUsuarios",

        info: "#infoPaginacionUsuarios"

    }).init();


    // =============================================
    // TAMAÑO DE PAGINA GUARDADO
    // =============================================

    const pageSizeGuardado =
        Number(
            localStorage.getItem(STORAGE_PAGE_SIZE)
        ) || 10;

    tablaUsuarios.actualizarDesdeBackend({

        page: 1,

        page_size: pageSizeGuardado,

        total: 0,

        total_pages: 1,

        sort_by: "id",

        sort_order: "desc"

    });


    // =============================================
    // FORMULARIO
    // =============================================

    const form = getEl("formUsuario");

    if (form) {

        form.addEventListener(
            "submit",
            guardarUsuario
        );

    }

    // =============================================
    // NUEVO USUARIO
    // =============================================

    getEl("btnNuevoUsuario")?.addEventListener(
        "click",
        mostrarFormularioUsuario
    );

    // =============================================
    // CANCELAR
    // =============================================

    getEl("btnCancelarUsuario")?.addEventListener(
        "click",
        cancelarEdicion
    );

    // =============================================
    // BUSQUEDA
    // =============================================

    getEl("busqueda")?.addEventListener(
        "input",
        filtrarUsuarios
    );

    // =============================================
    // FILTRO DE ESTADO
    // =============================================

    getEl("verInactivos")?.addEventListener(
        "change",
        () => {

            tablaUsuarios.reiniciarPaginacion();

            cargarUsuarios();

        }
    );

    // =============================================
    // GUARDAR PAGE SIZE
    // =============================================

    getEl("pageSizeUsuarios")?.addEventListener(
        "change",
        (e) => {

            localStorage.setItem(
                STORAGE_PAGE_SIZE,
                e.target.value
            );

        }
    );

    // =============================================
    // COMPATIBILIDAD CON CREAR_USUARIO.HTML
    // =============================================

    const url = new URL(window.location.href);

    if (url.searchParams.get("accion") === "nuevo") {

        url.searchParams.delete("accion");

        window.history.replaceState(
            {},
            "",
            url.pathname + url.search + url.hash
        );

        mostrarFormularioUsuario();

    }

    // =============================================
    // CARGAR INFORMACION
    // =============================================

    await cargarUsuarios();

});


// =====================================================
// CARGAR USUARIOS
// =====================================================

async function cargarUsuarios() {

    if (!tablaUsuarios) {
        return;
    }

    const solicitud = ++solicitudActual;

    mostrarLoader();

    const busqueda =
        getEl("busqueda")?.value.trim() || "";

    const verInactivos =
        getEl("verInactivos")?.checked || false;

    const params = new URLSearchParams({

        page: String(tablaUsuarios.page),

        limit: String(tablaUsuarios.pageSize),

        sort_by: tablaUsuarios.sortBy,

        sort_order: tablaUsuarios.sortOrder,

        inactivos: verInactivos
            ? "true"
            : "false",

        search: busqueda

    });

    try {

        const res = await apiFetch(
            `/usuarios?${params.toString()}`
        );

        // =============================================
        // VALIDAR RESPUESTA
        // =============================================

        if (!res) {
            return;
        }

        if (res.status === "error") {

            mostrarMensaje(
                res.message || "Error cargando usuarios.",
                "error"
            );

            return;

        }

        // Evitar que una búsqueda anterior sobrescriba
        // el resultado de una búsqueda más reciente.

        if (solicitud !== solicitudActual) {
            return;
        }

        const resultado = res.data || {};

        usuariosPagina = resultado.items || [];

        tablaUsuarios.actualizarDesdeBackend(
            resultado
        );

        pintarTabla(usuariosPagina);

    }

    catch (error) {

        if (solicitud !== solicitudActual) {
            return;
        }

        console.error(
            "ERROR CARGANDO USUARIOS:",
            error
        );

        mostrarMensaje(
            error.message || "No fue posible cargar los usuarios.",
            "error"
        );

        const tbody = getEl("tablaUsuarios");

        if (tbody) {

            tbody.innerHTML = `
                <tr>
                    <td colspan="5" class="usuarios-empty">
                        No fue posible cargar los registros.
                    </td>
                </tr>
            `;

        }

    }

}


// =====================================================
// PINTAR TABLA
// =====================================================

function pintarTabla(usuarios) {

    const tbody = getEl("tablaUsuarios");

    if (!tbody) {
        return;
    }

    tbody.innerHTML = "";

    // =============================================
    // SIN REGISTROS
    // =============================================

    if (!usuarios || usuarios.length === 0) {

        const verInactivos =
            getEl("verInactivos")?.checked;

        tbody.innerHTML = `
            <tr>
                <td colspan="5" class="usuarios-empty">
                    ${
                        verInactivos
                            ? "No hay usuarios inactivos."
                            : "No hay usuarios activos."
                    }
                </td>
            </tr>
        `;

        return;

    }

    // =============================================
    // REGISTROS
    // =============================================

    const filas = usuarios.map(u => {

        const id = Number(u.id);

        const activo = Number(u.activo) === 1;

        const nombre = escaparHTML(u.nombre);

        const usuario = escaparHTML(u.usuario);

        const perfil = escaparHTML(
            String(u.perfil || "").toUpperCase()
        );

        return `

            <tr>

                <td data-label="Nombre">
                    ${nombre}
                </td>

                <td data-label="Usuario">
                    ${usuario}
                </td>

                <td data-label="Perfil">
                    ${perfil}
                </td>

                <td data-label="Estado">

                    ${
                        activo
                            ? `
                                <span class="badge active">
                                    Activo
                                </span>
                            `
                            : `
                                <span class="badge inactive">
                                    Inactivo
                                </span>
                            `
                    }

                </td>

                <td
                    data-label="Acciones"
                    class="usuarios-actions"
                >

                    <button
                        type="button"
                        class="btn-action btn-edit"
                        title="Editar usuario"
                        aria-label="Editar usuario ${nombre}"
                        onclick="editarUsuario(${id})"
                    >
                        ✏️
                    </button>

                    ${
                        activo
                            ? `
                                <button
                                    type="button"
                                    class="btn-action btn-deactivate"
                                    onclick="toggleUsuario(${id}, 1)"
                                    title="Desactivar usuario"
                                >
                                    Desactivar
                                </button>
                            `
                            : `
                                <button
                                    type="button"
                                    class="btn-action btn-activate"
                                    onclick="toggleUsuario(${id}, 0)"
                                    title="Activar usuario"
                                >
                                    Activar
                                </button>
                            `
                    }

                </td>

            </tr>

        `;

    }).join("");

    tbody.innerHTML = filas;

}


// =====================================================
// MOSTRAR FORMULARIO NUEVO USUARIO
// =====================================================

function mostrarFormularioUsuario() {

    usuarioEditandoId = null;

    const form = getEl("formUsuario");

    if (form) {
        form.reset();
    }

    const password = getEl("password");

    if (password) {

        password.required = true;

        password.placeholder =
            "Contraseña de mínimo 12 caracteres";

    }

    setText(
        "formTitle",
        "Nuevo Usuario"
    );

    setText(
        "formDescription",
        "Registra los datos de acceso y el perfil del usuario."
    );

    setText(
        "passwordHelp",
        "La contraseña debe tener mínimo 12 caracteres."
    );

    setText(
        "btnGuardarUsuario",
        "Guardar Usuario"
    );

    getEl("formContainer")?.classList.remove(
        "hidden"
    );

    getEl("nombre")?.focus();

    getEl("formContainer")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

}


// =====================================================
// EDITAR USUARIO
// =====================================================

window.editarUsuario = function (id) {

    const usuario = usuariosPagina.find(
        u => Number(u.id) === Number(id)
    );

    if (!usuario) {

        mostrarMensaje(
            "No se encontró el usuario seleccionado.",
            "warning"
        );

        return;
    }

    usuarioEditandoId = Number(usuario.id);

    // =============================================
    // MOSTRAR FORMULARIO
    // =============================================

    getEl("formContainer")?.classList.remove(
        "hidden"
    );

    // =============================================
    // CARGAR INFORMACION
    // =============================================

    getEl("nombre").value =
        usuario.nombre || "";

    getEl("usuario").value =
        usuario.usuario || "";

    getEl("password").value = "";

    getEl("perfil").value =
        usuario.perfil || "ventas";

    // =============================================
    // CONTRASEÑA OPCIONAL EN EDICION
    // =============================================

    const password = getEl("password");

    password.required = false;

    password.placeholder =
        "Nueva contraseña (opcional)";

    // =============================================
    // TEXTOS
    // =============================================

    setText(
        "formTitle",
        `Editar Usuario #${usuario.id}`
    );

    setText(
        "formDescription",
        "Actualiza los datos de acceso del usuario."
    );

    setText(
        "passwordHelp",
        "Deja el campo vacío para conservar la contraseña actual. Para cambiarla utiliza mínimo 12 caracteres."
    );

    setText(
        "btnGuardarUsuario",
        "Actualizar Usuario"
    );

    // =============================================
    // DESPLAZAMIENTO
    // =============================================

    getEl("formContainer")?.scrollIntoView({
        behavior: "smooth",
        block: "start"
    });

};


// =====================================================
// GUARDAR / ACTUALIZAR USUARIO
// =====================================================

async function guardarUsuario(e) {

    e.preventDefault();

    const nombre =
        getEl("nombre")?.value.trim() || "";

    const usuario =
        getEl("usuario")?.value.trim().toLowerCase() || "";

    const passwordOriginal =
        getEl("password")?.value || "";

    const perfil =
        getEl("perfil")?.value || "";

    const esEdicion =
        usuarioEditandoId !== null;

    // =============================================
    // VALIDAR NOMBRE
    // =============================================

    if (!nombre) {

        mostrarMensaje(
            "El nombre completo es obligatorio.",
            "warning"
        );

        getEl("nombre")?.focus();

        return;
    }

    // =============================================
    // VALIDAR USUARIO
    // =============================================

    if (!usuario) {

        mostrarMensaje(
            "El nombre de usuario es obligatorio.",
            "warning"
        );

        getEl("usuario")?.focus();

        return;
    }

    if (/\s/.test(usuario)) {

        mostrarMensaje(
            "El nombre de usuario no puede contener espacios.",
            "warning"
        );

        getEl("usuario")?.focus();

        return;
    }

    // =============================================
    // VALIDAR PASSWORD
    // =============================================

    if (
        passwordOriginal !== "" &&
        passwordOriginal !== passwordOriginal.trim()
    ) {

        mostrarMensaje(
            "La contraseña no debe tener espacios al inicio o al final.",
            "warning"
        );

        getEl("password")?.focus();

        return;
    }

    if (!esEdicion && passwordOriginal.length < 12) {

        mostrarMensaje(
            "La contraseña debe tener mínimo 12 caracteres.",
            "warning"
        );

        getEl("password")?.focus();

        return;
    }

    if (
        esEdicion &&
        passwordOriginal !== "" &&
        passwordOriginal.length < 12
    ) {

        mostrarMensaje(
            "La nueva contraseña debe tener mínimo 12 caracteres.",
            "warning"
        );

        getEl("password")?.focus();

        return;
    }

    // =============================================
    // VALIDAR PERFIL
    // =============================================

    if (!["admin", "ventas"].includes(perfil)) {

        mostrarMensaje(
            "Selecciona un perfil válido.",
            "warning"
        );

        return;
    }

    // =============================================
    // DATOS
    // No se envía activo.
    // El backend conserva el estado actual.
    // =============================================

    const data = {

        nombre,

        usuario,

        password: passwordOriginal,

        perfil

    };

    const boton = getEl("btnGuardarUsuario");

    const textoOriginal =
        boton?.textContent || "Guardar Usuario";

    try {

        if (boton) {

            boton.disabled = true;

            boton.textContent =
                esEdicion
                    ? "Actualizando..."
                    : "Guardando...";

        }

        // =========================================
        // CREAR
        // =========================================

        let res;

        if (!esEdicion) {

            res = await apiFetch(
                "/usuarios",
                "POST",
                data
            );

        }

        // =========================================
        // EDITAR
        // =========================================

        else {

            res = await apiFetch(
                `/usuarios/${usuarioEditandoId}`,
                "PUT",
                data
            );

        }

        if (!res) {
            return;
        }

        if (res.status === "error") {

            mostrarMensaje(
                res.message || "No fue posible guardar el usuario.",
                "error"
            );

            return;
        }

        mostrarMensaje(
            esEdicion
                ? "Usuario actualizado correctamente."
                : "Usuario creado correctamente.",
            "success"
        );

        // =========================================
        // ACTUALIZAR LISTADO
        // =========================================

        cancelarEdicion();

        if (!esEdicion) {

            // El usuario nuevo se crea activo.
            // Mostrarlo al finalizar el registro.

            if (getEl("verInactivos")?.checked) {

                getEl("verInactivos").checked = false;

            }

        }

        tablaUsuarios.reiniciarPaginacion();

        await cargarUsuarios();

    }

    catch (error) {

        console.error(
            "ERROR GUARDANDO USUARIO:",
            error
        );

        mostrarMensaje(
            error.message || "Error guardando usuario.",
            "error"
        );

    }

    finally {

        if (boton) {

            boton.disabled = false;

            boton.textContent =
                textoOriginal;

        }

    }

}


// =====================================================
// ACTIVAR / DESACTIVAR
// =====================================================

window.toggleUsuario = async function (id, activo) {

    const nuevoEstado = Number(activo) === 1 ? 0 : 1;

    const accion = nuevoEstado === 1
        ? "activar"
        : "desactivar";

    const confirmado = confirm(
        `¿Estás seguro de que deseas ${accion} este usuario?`
    );

    if (!confirmado) {
        return;
    }

    try {

        const res = await apiFetch(
            `/usuarios/${id}/activar`,
            "PUT",
            {
                activo: nuevoEstado
            }
        );

        if (!res) {
            return;
        }

        if (res.status === "error") {

            mostrarMensaje(
                res.message || "No fue posible cambiar el estado.",
                "error"
            );

            return;

        }

        mostrarMensaje(
            res.message || "Estado actualizado correctamente.",
            "success"
        );

        await cargarUsuarios();

    }

    catch (error) {

        console.error(
            "ERROR CAMBIANDO ESTADO:",
            error
        );

        mostrarMensaje(
            error.message || "No fue posible cambiar el estado del usuario.",
            "error"
        );

    }

};


// =====================================================
// CANCELAR FORMULARIO
// =====================================================

function cancelarEdicion() {

    usuarioEditandoId = null;

    const form = getEl("formUsuario");

    if (form) {
        form.reset();
    }

    const password = getEl("password");

    if (password) {

        password.required = true;

        password.placeholder =
            "Contraseña de mínimo 12 caracteres";

    }

    setText(
        "formTitle",
        "Nuevo Usuario"
    );

    setText(
        "formDescription",
        "Registra los datos de acceso y el perfil del usuario."
    );

    setText(
        "passwordHelp",
        "La contraseña debe tener mínimo 12 caracteres."
    );

    setText(
        "btnGuardarUsuario",
        "Guardar Usuario"
    );

    getEl("formContainer")?.classList.add(
        "hidden"
    );

}


// =====================================================
// BUSQUEDA
// =====================================================

function filtrarUsuarios() {

    clearTimeout(timeoutBusqueda);

    timeoutBusqueda = setTimeout(() => {

        if (!tablaUsuarios) {
            return;
        }

        tablaUsuarios.reiniciarPaginacion();

        cargarUsuarios();

    }, 300);

}


// =====================================================
// LOADER
// =====================================================

function mostrarLoader() {

    const tbody = getEl("tablaUsuarios");

    if (!tbody) {
        return;
    }

    tbody.innerHTML = `
        <tr>
            <td colspan="5" class="usuarios-empty">
                Cargando usuarios...
            </td>
        </tr>
    `;

}


// =====================================================
// MENSAJES
// =====================================================

function mostrarMensaje(msg, tipo = "success") {

    document
        .querySelectorAll(".toast")
        .forEach(t => t.remove());

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

    toast.textContent =
        `${iconos[tipo] || ""} ${msg}`;

    document.body.appendChild(toast);

    requestAnimationFrame(() => {

        toast.classList.add("show");

    });

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => toast.remove(), 300);

    }, tiempos[tipo] || 4000);

}


// =====================================================
// FUNCIONES DISPONIBLES PARA EL HTML
// =====================================================

window.mostrarFormularioUsuario =
    mostrarFormularioUsuario;

window.cancelarEdicion =
    cancelarEdicion;

window.filtrarUsuarios =
    filtrarUsuarios;
