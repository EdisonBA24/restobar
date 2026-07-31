import { apiFetch } from "./api.js";
// IMPORTACION TABLAS.JS
import { TablaUI } from "./tablas.js";

// ELIMINAR DESPUES DE MIGRAR TABLAS.JS
// let currentPage = 1;
// const limit = 5;

let editandoId = null;
let proveedoresGlobal = [];

//SE AGREGAR AL IMPORTA TABLAS.JS
const STORAGE_PAGE_SIZE = "proveedores_page_size";

let tablaProveedores = null;

function getEl(id) {
    return document.getElementById(id);
}

function setText(id, text) {
    const el = getEl(id);
    if (el) el.innerText = text;
}

function limpiarFormularioProveedor() {

    editandoId = null;

    getEl("formProveedor")?.reset();

    setText("formTitle", "Nuevo Proveedor");

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

window.mostrarFormularioProveedor = async function (esEdicion = false) {

    if (!esEdicion) {

        limpiarFormularioProveedor();

    }

    getEl("formContainer")?.classList.remove("hidden");

}

function ocultarFormularioProveedor() {

    limpiarFormularioProveedor();

    getEl("formContainer")?.classList.add("hidden");

}

function obtenerProveedorPorId(id) {

    return proveedoresGlobal.find(
        proveedor => proveedor.id === id
    ) || null;

}

function obtenerDatosFormulario() {

    return {

        nombre: getEl("nombre")?.value.trim() || "",

        nit: getEl("nit")?.value.trim() || "",

        contacto: getEl("contacto")?.value.trim() || "",

        telefono: getEl("telefono")?.value.trim() || "",

        email: getEl("email")?.value.trim() || "",

        ciudad: getEl("ciudad")?.value.trim() || "",

        direccion: getEl("direccion")?.value.trim() || "",

        observaciones: getEl("observaciones")?.value.trim() || ""

    };

}

document.addEventListener("DOMContentLoaded", () => {

    //SE AGREGA AL IMPORTA TABLAS.JS
    const pageSizeGuardado =
        Number(localStorage.getItem(STORAGE_PAGE_SIZE)) || 10;

    tablaProveedores = new TablaUI({

        nombre: "proveedores",

        callback: () => cargarProveedores(),

        tabla: "#tablaProveedores",

        pageSize: "#pageSizeProveedores",

        btnAnterior: "#btnPaginaAnterior",

        btnSiguiente: "#btnPaginaSiguiente",

        numeros: "#numerosPaginacion",

        resumen: "#resumenPaginacion",

        info: "#infoPaginacion"

    }).init();

    tablaProveedores.setEstado({

        page: 1,

        page_size: pageSizeGuardado,

        total: 0,

        total_pages: 1,

        sort_by: "nombre",

        sort_order: "asc"

    });

    if (getEl("tablaProveedores")) {
        cargarProveedores();
    }

    const form = getEl("formProveedor");
    if (form) {
        form.addEventListener("submit", guardarProveedor);
    }

    const btnNuevo = getEl("btnNuevoProveedor");

    if (btnNuevo) {

        btnNuevo.addEventListener("click", () => {

            mostrarFormularioProveedor();

        });

    }

    const chk = getEl("verInactivos");
    if (chk) {
        chk.addEventListener("change", () => {
            // ELIMINAR DESPUES DE MIGRAR TABLAS.JS
            // currentPage = 1;
            // cargarProveedores();
            tablaProveedores.reiniciarPaginacion();

            cargarProveedores();
        });
    }

});

async function cargarProveedores() {

    mostrarLoader();

    const verInactivos = getEl("verInactivos")?.checked;

    try {
        const res = await apiFetch(
            `/proveedores?page=${/*currentPage*/tablaProveedores.page}&limit=${/*limit*/tablaProveedores.pageSize}&inactivos=${verInactivos ? "true" : "false"}`
        );

        // Próxima fase:
        // TablaUI actualizará aquí page, total y total_pages
        // desde la respuesta del backend.

        // proveedoresGlobal = res?.data || [];
        // pintarTabla(proveedoresGlobal);

        const resultado = res?.data || {};

        // TEMPORAL
        // Cuando el backend entregue la misma estructura que Compras,
        // solo habrá que descomentar estas líneas.

        tablaProveedores.actualizarDesdeBackend(resultado);

        proveedoresGlobal = resultado.items || [];

        pintarTabla(proveedoresGlobal);

    } catch (error) {
        mostrarMensaje("Error cargando proveedores ❌", "error");
    }
}

function escaparTexto(texto) {
    return (texto || "").replace(/'/g, "\\'");
}

function pintarTabla(proveedores) {

    const tbody = getEl("tablaProveedores");

    if (!tbody) return;

    tbody.innerHTML = "";

    if (proveedores.length === 0) {

        tbody.innerHTML = `
            <tr>
                <td colspan="7">Sin proveedores registrados</td>
            </tr>
        `;

        return;

    }

    proveedores.forEach(p => {

        tbody.innerHTML += `
            <tr>

                <td>${p.nombre || ""}</td>

                <td>${p.nit || ""}</td>

                <td>${p.contacto || ""}</td>

                <td>${p.telefono || ""}</td>

                <td>${p.ciudad || ""}</td>

                <td>
                    ${p.activo
                ? '<span class="badge active">Activo</span>'
                : '<span class="badge inactive">Inactivo</span>'
            }
                </td>

                <td class="acciones">

                    <button
                        class="btn-action btn-edit"
                        onclick="editar(${p.id})">
                        ✏️
                    </button>

                    ${p.activo
                ? `<button class="btn-action btn-deactivate" onclick="eliminar(${p.id})">Desactivar</button>`
                : `<button class="btn-action btn-activate" onclick="activar(${p.id})">Activar</button>`
            }

                </td>

            </tr>
        `;

    });

}

window.editar = async function (id) {

    try {

        const result = await apiFetch(`/proveedores/${id}`);

        if (!result || result.status !== "success") {

            mostrarMensaje(
                result?.message || "No fue posible cargar el proveedor.",
                "error"
            );

            return;
        }

        const proveedor = result.data;

        editandoId = proveedor.id;

        getEl("nombre").value = proveedor.nombre || "";

        getEl("nit").value = proveedor.nit || "";

        getEl("contacto").value = proveedor.contacto || "";

        getEl("telefono").value = proveedor.telefono || "";

        getEl("email").value = proveedor.email || "";

        getEl("ciudad").value = proveedor.ciudad || "";

        getEl("direccion").value = proveedor.direccion || "";

        getEl("observaciones").value = proveedor.observaciones || "";

        setText("formTitle", "Editar Proveedor");
        setText("btnGuardar", "Actualizar");

        mostrarFormularioProveedor(true);

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "No fue posible obtener la información del proveedor.",
            "error"
        );
    }

};

window.cancelarEdicion = function () {

    ocultarFormularioProveedor();

};

async function guardarProveedor(e) {

    e.preventDefault();

    bloquearBotonGuardar();

    const data = obtenerDatosFormulario();

    console.log(data);

    if (!data.nombre) {

        mostrarMensaje(
            "El nombre del proveedor es obligatorio.",
            "warning"
        );

        desbloquearBotonGuardar();

        return;

    }

    try {

        let res;

        if (editandoId) {
            res = await apiFetch(`/proveedores/${editandoId}`, "PUT", data);
        } else {
            res = await apiFetch("/proveedores", "POST", data);
        }

        if (res?.status === "error") {
            mostrarMensaje(res.message || "Error guardando proveedor", "error");
            return;
        }

        mostrarMensaje("Proveedor guardado correctamente ✅", "success");

        ocultarFormularioProveedor();

        await cargarProveedores();

    } catch (error) {
        console.error("Error guardando proveedor:", error);
        mostrarMensaje(error.message || "Error en proveedor", "error");
    } finally {
        desbloquearBotonGuardar();
    }
}

window.eliminar = async function (id) {
    try {
        await apiFetch(`/proveedores/${id}`, "DELETE");
        mostrarMensaje("Proveedor desactivado ✅");
        cargarProveedores();
    } catch (error) {
        console.error(error);
        mostrarMensaje("Error desactivando ❌", "error");
    }
};

window.activar = async function (id) {
    try {
        await apiFetch(`/proveedores/${id}/activar`, "PUT");
        mostrarMensaje("Proveedor activado ✅");
        cargarProveedores();
    } catch (error) {
        console.error(error);
        mostrarMensaje("Error activando ❌", "error");
    }
};

function mostrarLoader() {
    const tabla = getEl("tablaProveedores");
    if (tabla) {
        tabla.innerHTML = `<tr><td colspan="7">Cargando...</td></tr>`;
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
    // ELIMINAR DESPUES DE MIGRAR TABLAS.JS
    // currentPage++;
    // cargarProveedores();
    tablaProveedores.paginaSiguiente();
};

window.prevPage = function () {
    // ELIMINAR DESPUES DE MIGRAR TABLAS.JS
    // if (currentPage > 1) {
    //    currentPage--;
    //    cargarProveedores();
    // }
    tablaProveedores.paginaAnterior();
};

window.filtrarProveedores = async function () {

    const texto = getEl("busqueda").value.trim();

    if (!texto) {
        cargarProveedores();
        return;
    }

    try {
        const res = await apiFetch(`/proveedores?page=1&limit=100&search=${texto}`);
        pintarTabla(res.data || []);
    } catch (error) {
        console.error(error);
        mostrarMensaje("Error filtrando ❌", "error");
    }
};
