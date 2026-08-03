import { apiFetch } from "./api.js";
import { TablaUI } from "./tablas.js";

const STORAGE_PAGE_SIZE = "clientes_page_size";

let tablaClientes = null;
let editandoId = null;
let clientesGlobal = [];
let direccionesCliente = [];

function getEl(id) {
    return document.getElementById(id);
}

function setText(id, text) {
    const el = getEl(id);
    if (el) el.innerText = text;
}

function limpiarFormularioCliente() {

    editandoId = null;

    direccionesCliente = [];

    getEl("formCliente")?.reset();

    renderizarDirecciones();

    setText("formTitle", "Nuevo Cliente");

    setText("btnGuardar", "Guardar");

}

function bloquearBotonGuardar() {

    const btn = getEl("btnGuardar");

    if (!btn) return;

    btn.disabled = true;
    btn.dataset.textoOriginal = btn.textContent;
    btn.textContent = "Guardando...";

}

function desbloquearBotonGuardar() {

    const btn = getEl("btnGuardar");

    if (!btn) return;

    btn.disabled = false;
    btn.textContent = btn.dataset.textoOriginal || "Guardar";

}

window.mostrarFormularioCliente = async function (esEdicion = false) {

    if (!esEdicion) {

        limpiarFormularioCliente();

    }

    getEl("formContainer")?.classList.remove("hidden");

}

function ocultarFormularioCliente() {

    limpiarFormularioCliente();

    getEl("formContainer")?.classList.add("hidden");

}

function obtenerClientePorId(id) {

    return clientesGlobal.find(cliente => cliente.id === id) || null;

}

function obtenerDatosFormulario() {

    return {

        nombre: getEl("nombre")?.value.trim() || "",

        documento: getEl("documento")?.value.trim() || "",

        telefono: getEl("telefono")?.value.trim() || "",

        email: getEl("email")?.value.trim() || "",

        barrio: getEl("barrio")?.value.trim() || "",

        direcciones: direccionesCliente.map(direccion => ({
            id: direccion.id,
            nombre: direccion.nombre.trim(),
            direccion: direccion.direccion.trim(),
            barrio: direccion.barrio.trim(),
            referencia: direccion.referencia.trim(),
            principal: direccion.principal,
            activo: direccion.activo
        }))

    };

}

function validarDirecciones() {

    // Si aún no existen direcciones, no validar.
    // Cuando el negocio obligue al menos una dirección,
    // aquí cambiaremos esta regla.
    if (direccionesCliente.length === 0) {
        return true;
    }

    let cantidadPrincipales = 0;

    for (const direccion of direccionesCliente) {

        if (!direccion.nombre.trim()) {
            mostrarMensaje("Cada dirección debe tener un nombre (Casa, Trabajo, etc.).", "warning");
            return false;
        }

        if (!direccion.direccion.trim()) {
            mostrarMensaje("La dirección no puede estar vacía.", "warning");
            return false;
        }

        if (direccion.principal) {
            cantidadPrincipales++;
        }

    }

    if (cantidadPrincipales > 1) {
        mostrarMensaje("Solo puede existir una dirección principal.", "warning");
        return false;
    }

    return true;

}

function crearDireccionVacia() {

    return {

        id: null,

        nombre: "",

        direccion: "",

        barrio: "",

        referencia: "",

        principal: false,

        activo: true

    };

}

document.addEventListener("DOMContentLoaded", () => {

    if (getEl("tablaClientes")) {

        const pageSizeGuardado =
            Number(localStorage.getItem(STORAGE_PAGE_SIZE)) || 10;

        tablaClientes = new TablaUI({

            nombre: "clientes",

            callback: () => cargarClientes(),

            tabla: "#tablaClientesTabla",

            pageSize: "#pageSizeClientes",

            btnAnterior: "#btnPaginaAnterior",

            btnSiguiente: "#btnPaginaSiguiente",

            numeros: "#numerosPaginacion",

            resumen: "#resumenPaginacion",

            info: "#infoPaginacion"

        }).init();

        tablaClientes.actualizarDesdeBackend({

            page: 1,

            page_size: pageSizeGuardado,

            total: 0,

            total_pages: 1,

            sort_by: "id",

            sort_order: "desc"

        });

        cargarClientes();

    }

    const form = getEl("formCliente");
    if (form) {
        form.addEventListener("submit", guardarCliente);
    }

    const btnNuevo = getEl("btnNuevoCliente");

    if (btnNuevo) {

        btnNuevo.addEventListener("click", () => {

            mostrarFormularioCliente();

        });

    }

    const btnAgregarDireccion = getEl("btnAgregarDireccion");

    if (btnAgregarDireccion) {

        btnAgregarDireccion.addEventListener("click", agregarDireccion);

    }

    const chk = getEl("verInactivos");
    if (chk) {
        chk.addEventListener("change", () => {

            tablaClientes.reiniciarPaginacion();

            cargarClientes();
        });
    }

    renderizarDirecciones();

});

async function cargarClientes() {

    if (!tablaClientes) {
        console.error("TablaUI no inicializada.");
        return;
    }

    mostrarLoader();

    const verInactivos = getEl("verInactivos")?.checked;
    const texto = getEl("busqueda")?.value.trim() || "";

    try {

        const params = new URLSearchParams({
            page: tablaClientes.page,
            limit: tablaClientes.pageSize,
            sort_by: tablaClientes.sortBy,
            sort_order: tablaClientes.sortOrder,
            inactivos: verInactivos ? "true" : "false",
            search: texto
        });

        const res = await apiFetch(`/clientes?${params}`);

        const resultado = res.data;

        tablaClientes.actualizarDesdeBackend(resultado);

        clientesGlobal = resultado.items || [];

        pintarTabla(clientesGlobal);

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error cargando clientes",
            "error"
        );
    }
}

function escaparTexto(texto) {
    return (texto || "").replace(/'/g, "\\'");
}

function renderizarDirecciones() {

    const contenedor = getEl("contenedorDirecciones");

    if (!contenedor) return;

    contenedor.innerHTML = "";

    if (direccionesCliente.length === 0) {

        contenedor.innerHTML = `

        <div class="empty-direcciones">

            <div class="empty-icon">

                📍

            </div>

            <h4>

                Aún no hay direcciones

            </h4>

            <p>

                Agregue la primera dirección del cliente para comenzar.

            </p>

        </div>

        `;

        return;

    }

    direccionesCliente.forEach((direccion, index) => {

        contenedor.innerHTML += crearTarjetaDireccion(direccion, index);

    });

}

function crearTarjetaDireccion(direccion, index) {

    return `

        <div class="direccion-card">

            <div class="direccion-header">

                <div class="direccion-header-left">

                <h4>

                ${direccion.nombre
            ? direccion.nombre
            : `Dirección ${index + 1}`
        }

                </h4>

                ${direccion.principal
            ? `<span class="badge-principal">Principal</span>`
            : ""
        }

                </div>

            <button
            type="button"
            class="btn-eliminar-direccion"
            onclick="eliminarDireccion(${index})"
            title="Eliminar dirección">

            🗑

            </button>

        </div>

            <div class="form-grid">

                <div class="form-group">

                    <label>Nombre</label>

                    <input
                        type="text"
                        value="${direccion.nombre}"

                        onchange="actualizarDireccion(${index}, 'nombre', this.value)"

                        placeholder="Casa, Trabajo...">

                </div>

                <div class="form-group full">

                    <label>Dirección</label>

                    <input
                        type="text"
                        value="${direccion.direccion}"

                        onchange="actualizarDireccion(${index}, 'direccion', this.value)">

                </div>

                <div class="form-group">

                    <label>Barrio</label>

                    <input
                        type="text"
                        value="${direccion.barrio}"

                        onchange="actualizarDireccion(${index}, 'barrio', this.value)">

                </div>

                <div class="form-group">

                    <label>Referencia</label>

                    <input
                        type="text"
                        value="${direccion.referencia}"

                        oninput="actualizarDireccion(${index}, 'referencia', this.value)">

                </div>

                <div class="form-group full">

                    <label>

                        <input
                            type="checkbox"

                            ${direccion.principal ? "checked" : ""}

                            onchange="marcarDireccionPrincipal(${index})">

                        Dirección principal

                    </label>

                </div>

            </div>

        </div>

    `;

}

window.actualizarDireccion = function (index, campo, valor) {

    direccionesCliente[index][campo] = valor;

};

window.eliminarDireccion = function (index) {

    direccionesCliente.splice(index, 1);

    renderizarDirecciones();

};

window.marcarDireccionPrincipal = function (index) {

    direccionesCliente.forEach((direccion, i) => {

        direccion.principal = i === index;

    });

    renderizarDirecciones();

};

function pintarTabla(clientes) {

    const tbody = getEl("tablaClientes");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (clientes.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6">Sin clientes</td></tr>`;
        return;
    }

    clientes.forEach(c => {

        tbody.innerHTML += `
            <tr>
                <td>${c.nombre || ""}</td>
                <td>${c.documento || ""}</td>
                <td>${c.telefono || ""}</td>
                <td>
                    ${c.direccion_principal
                ? `<strong>${c.nombre_direccion_principal}</strong><br>${c.direccion_principal}`
                : ""
            }
                </td>
                <td>
                    ${c.activo
                ? '<span class="badge active">Activo</span>'
                : '<span class="badge inactive">Inactivo</span>'}
                </td>
                <td class="acciones">

                    <button class="btn-action btn-edit"
                        onclick="editar(${c.id})">
                    ✏️
                    </button>

                    ${c.activo
                ? `<button class="btn-action btn-deactivate" onclick="eliminar(${c.id})">Desactivar</button>`
                : `<button class="btn-action btn-activate" onclick="activar(${c.id})">Activar</button>`
            }

                </td>
            </tr>
        `;
    });
}

window.editar = async function (id) {

    try {

        const result = await apiFetch(`/clientes/${id}`);

        if (!result || result.status !== "success") {

            mostrarMensaje(
                result?.message || "No fue posible cargar el cliente.",
                "error"
            );

            return;
        }

        const cliente = result.data;

        editandoId = cliente.id;

        getEl("nombre").value = cliente.nombre || "";
        getEl("documento").value = cliente.documento || "";
        getEl("telefono").value = cliente.telefono || "";
        getEl("email").value = cliente.email || "";

        direccionesCliente = (cliente.direcciones || []).map(d => ({
            id: d.id,
            nombre: d.nombre || "",
            direccion: d.direccion || "",
            barrio: d.barrio || "",
            referencia: d.referencia || "",
            principal: Number(d.principal) === 1,
            activo: !!d.activo
        }));

        renderizarDirecciones();

        setText("formTitle", "Editar Cliente");
        setText("btnGuardar", "Actualizar");

        mostrarFormularioCliente(true);

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "No fue posible obtener la información del cliente.",
            "error"
        );
    }

};

window.cancelarEdicion = function () {

    ocultarFormularioCliente();

};

window.agregarDireccion = function () {

    direccionesCliente.push(
        crearDireccionVacia()
    );

    renderizarDirecciones();

};

async function guardarCliente(e) {

    e.preventDefault();

    if (!validarDirecciones()) {
        return;
    }

    // Validar nombres repetidos
    const nombres = direccionesCliente.map(d =>
        d.nombre.trim().toLowerCase()
    );

    if (new Set(nombres).size !== nombres.length) {

        mostrarMensaje(
            "No puede registrar dos direcciones con el mismo nombre.",
            "warning"
        );

        return;
    }

    // Validar direcciones repetidas
    const direcciones = direccionesCliente.map(d =>
        d.direccion.trim().toLowerCase()
    );

    if (new Set(direcciones).size !== direcciones.length) {

        mostrarMensaje(
            "No puede registrar dos direcciones iguales para el mismo cliente.",
            "warning"
        );

        return;
    }

    bloquearBotonGuardar();

    const data = obtenerDatosFormulario();

    try {

        let res;

        if (editandoId) {
            res = await apiFetch(`/clientes/${editandoId}`, "PUT", data);
        } else {
            res = await apiFetch("/clientes", "POST", data);
        }

        if (res?.status === "error") {
            mostrarMensaje(res.message || "Error guardando cliente", "error");
            return;
        }

        mostrarMensaje("Cliente guardado correctamente ✅", "success");

        ocultarFormularioCliente();

        await cargarClientes();

    } catch (error) {
        console.error("Error guardando cliente:", error);
        mostrarMensaje(error.message || "Error en cliente", "error");
    } finally {
        desbloquearBotonGuardar();
    }
}

window.eliminar = async function (id) {
    try {
        await apiFetch(`/clientes/${id}`, "DELETE");
        mostrarMensaje("Cliente desactivado ✅");
        cargarClientes();
    } catch (error) {
        console.error(error);
        mostrarMensaje("Error desactivando ❌", "error");
    }
};

window.activar = async function (id) {
    try {
        await apiFetch(`/clientes/${id}/activar`, "PUT");
        mostrarMensaje("Cliente activado ✅");
        cargarClientes();
    } catch (error) {
        console.error(error);
        mostrarMensaje("Error activando ❌", "error");
    }
};

function mostrarLoader() {
    const tabla = getEl("tablaClientes");
    if (tabla) {
        tabla.innerHTML = `<tr><td colspan="6">Cargando...</td></tr>`;
    }
}

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

window.nextPage = function () {

    tablaClientes.paginaSiguiente();

};

window.prevPage = function () {

    tablaClientes.paginaAnterior();

};

window.filtrarClientes = function () {

    tablaClientes.reiniciarPaginacion();

    cargarClientes();

};