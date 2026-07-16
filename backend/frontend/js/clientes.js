import { apiFetch } from "./api.js";

let currentPage = 1;
const limit = 5;
let editandoId = null;
let clientesGlobal = [];

// 🔥 BASE DINÁMICA (LOCAL vs PRODUCCIÓN)
const BASE_URL = window.location.hostname.includes("localhost")
    ? "http://127.0.0.1:5000/api"
    : "https://restobar.onrender.com"; // 🔥 CAMBIA ESTO

function getEl(id) {
    return document.getElementById(id);
}

function setText(id, text) {
    const el = getEl(id);
    if (el) el.innerText = text;
}

document.addEventListener("DOMContentLoaded", () => {

    if (getEl("tablaClientes")) {
        cargarClientes();
    }

    const form = getEl("formCliente");
    if (form) {
        form.addEventListener("submit", guardarCliente);
    }

    const chk = getEl("verInactivos");
    if (chk) {
        chk.addEventListener("change", () => {
            currentPage = 1;
            cargarClientes();
        });
    }
});

async function cargarClientes() {

    mostrarLoader();

    const verInactivos = getEl("verInactivos")?.checked;

    try {
        const res = await apiFetch(
            `/clientes?page=${currentPage}&limit=${limit}&inactivos=${verInactivos ? "true" : "false"}`
        );

        clientesGlobal = res?.data || [];
        pintarTabla(clientesGlobal);

    } catch (error) {
        console.error("Error cargando clientes:", error);
        mostrarMensaje("Error cargando clientes ❌", "error");
    }
}

function escaparTexto(texto) {
    return (texto || "").replace(/'/g, "\\'");
}

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
                <td>${c.direccion || ""}</td>
                <td>
                    ${c.activo
                        ? '<span class="badge active">Activo</span>'
                        : '<span class="badge inactive">Inactivo</span>'}
                </td>
                <td class="acciones">

                    <button class="btn-action btn-edit"
                        onclick="editar(${c.id}, '${escaparTexto(c.nombre)}', '${escaparTexto(c.documento)}', '${escaparTexto(c.telefono)}', '${escaparTexto(c.direccion)}')">
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

window.editar = function (id, nombre, documento, telefono, direccion) {

    editandoId = id;

    getEl("nombre").value = nombre || "";
    getEl("documento").value = documento || "";
    getEl("telefono").value = telefono || "";
    getEl("direccion").value = direccion || "";

    setText("formTitle", "Editar Cliente");
    setText("btnGuardar", "Actualizar");

    getEl("formContainer")?.classList.remove("hidden");
};

window.cancelarEdicion = function () {
    editandoId = null;

    getEl("formCliente").reset();

    setText("btnGuardar", "Guardar");
    setText("formTitle", "Nuevo Cliente");

    getEl("formContainer")?.classList.add("hidden");
};

async function guardarCliente(e) {

    e.preventDefault();

    const data = {
        nombre: getEl("nombre").value,
        documento: getEl("documento").value,
        telefono: getEl("telefono").value,
        direccion: getEl("direccion").value
    };

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

        cancelarEdicion();
        cargarClientes();

    } catch (error) {
        console.error("Error guardando cliente:", error);
        mostrarMensaje(error.message || "Error en cliente", "error");
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
    currentPage++;
    cargarClientes();
};

window.prevPage = function () {
    if (currentPage > 1) {
        currentPage--;
        cargarClientes();
    }
};

window.filtrarClientes = async function () {

    const texto = getEl("busqueda").value.trim();

    if (!texto) {
        cargarClientes();
        return;
    }

    try {
        const res = await apiFetch(`/clientes?page=1&limit=100&search=${texto}`);
        pintarTabla(res.data || []);
    } catch (error) {
        console.error(error);
        mostrarMensaje("Error filtrando ❌", "error");
    }
};
