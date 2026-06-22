import { apiFetch } from "./api.js";

let currentPage = 1;
const limit = 5;
let editandoId = null;
let productosGlobal = [];

// =============================
// HELPERS SEGUROS
// =============================
function getEl(id) {
    return document.getElementById(id);
}

function setText(id, text) {
    const el = getEl(id);
    if (el) el.innerText = text;
}

// =============================
// INIT
// =============================
document.addEventListener("DOMContentLoaded", () => {

    const tipoSelect = getEl("tipo");
    if (tipoSelect) tipoSelect.dispatchEvent(new Event("change"));

    if (getEl("tablaProductos")) {
        cargarProductos();
    }

    if (getEl("unidad")) {
        cargarUnidades();
    }

    const form = getEl("formProducto");
    if (form) {
        form.addEventListener("submit", guardarProducto);
    }

    const chk = getEl("verInactivos");
    if (chk) {
        chk.addEventListener("change", () => {
            currentPage = 1;
            cargarProductos();
        });
    }

    if (tipoSelect) {
        tipoSelect.addEventListener("change", function () {

            const precioInput = getEl("precio_venta");
            const container = getEl("container_precio");

            if (!precioInput) return;

            if (this.value === "INSUMO") {
                precioInput.value = "";
                precioInput.disabled = true;
                precioInput.placeholder = "No aplica para insumos";

                if (container) container.style.display = "none";

            } else {
                precioInput.disabled = false;
                precioInput.placeholder = "Precio venta";

                if (container) container.style.display = "block";
            }
        });

        aplicarTipoUI(tipoSelect);
    }
});


// =============================
// CARGAR PRODUCTOS
// =============================
async function cargarProductos() {
    mostrarLoader();

    try {
        const verInactivos = getEl("verInactivos")?.checked;

        const res = await apiFetch(
            `/productos?page=${currentPage}&limit=${limit}&inactivos=${verInactivos ? "true" : "false"}`
        );

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando productos ❌", "error");
            return;
        }

        productosGlobal = res.data || [];
        pintarTabla(productosGlobal);

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando productos ❌", "error");
    }
}


// =============================
// TABLA
// =============================
function escaparTexto(texto) {
    return (texto || "").replace(/'/g, "\\'");
}

function pintarTabla(productos) {

    const tbody = getEl("tablaProductos");
    if (!tbody) return;

    tbody.innerHTML = "";

    if (!productos || productos.length === 0) {
        tbody.innerHTML = `<tr><td colspan="10">Sin productos</td></tr>`;
        return;
    }

    productos.forEach(p => {

        tbody.innerHTML += `
            <tr>
                <td style="text-align: center;">${p.nombre || ""}</td>
                <td style="text-align: center;">${p.codigo || ""}</td>
                <td style="text-align: center;">${p.stock ?? ""}</td>
                <td style="text-align: center;">${p.categoria || ""}</td>
                <td style="text-align: center;">${formatearFecha(p.fecha_creacion || "")}</td>
                <td style="text-align: center;">${p.unidad_nombre || ""} (${p.abreviatura || ""})</td>
                <td style="text-align: center;">${p.tipo || ""}</td>
                <td style="text-align: center;">${formatoMoneda(p.precio_venta || 0)}</td>
                <td style="text-align: center;">
                    ${p.activo
                ? '<span class="badge active">Activo</span>'
                : '<span class="badge inactive">Inactivo</span>'}
                </td>
                <td class="acciones">

                    <button class="btn-action btn-edit"
                        onclick="editar(${p.id}, 
                        '${escaparTexto(p.nombre)}', '${escaparTexto(p.codigo)}', '${escaparTexto(p.categoria)}', ${p.unidad_id || 0}, '${p.tipo}',
                        ${p.precio_venta || 0})">
                        ✏️
                    </button>

                    ${p.activo
                ? `<button class="btn-action btn-deactivate" onclick="eliminar(${p.id})">Desactivar</button>`
                : `<button class="btn-action btn-activate" onclick="activar(${p.id})">Activar</button>`
            }

                    <button class="btn-action btn-activate" onclick="verCosto(${p.id})">Costos</button>

                </td>
            </tr>
        `;
    });
}


// =============================
// FORMATO
// =============================
function formatoMoneda(valor) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(valor || 0);
}


// =============================
// EDITAR
// =============================
window.editar = function (id, nombre, codigo, categoria, unidad_id, tipo, precio_venta) {

    editandoId = id;

    getEl("nombre") && (getEl("nombre").value = nombre || "");
    getEl("codigo") && (getEl("codigo").value = codigo || "");
    getEl("categoria") && (getEl("categoria").value = categoria || "");
    getEl("unidad") && (getEl("unidad").value = unidad_id || "");
    getEl("tipo") && (getEl("tipo").value = tipo || "");
    getEl("precio_venta") && (getEl("precio_venta").value = precio_venta || 0);
    aplicarTipoUI(getEl("tipo"));

    setText("formTitle", "Editar Producto");
    setText("btnGuardar", "Actualizar");

    getEl("formContainer")?.classList.remove("hidden");
};


// =============================
// CANCELAR
// =============================
window.cancelarEdicion = function () {
    editandoId = null;

    const form = getEl("formProducto");
    if (form) form.reset();

    setText("btnGuardar", "Guardar");
    setText("formTitle", "Nuevo Producto");

    getEl("formContainer")?.classList.add("hidden");
};


// =============================
// GUARDAR
// =============================
async function guardarProducto(e) {

    e.preventDefault();

    const tipo = getEl("tipo")?.value;
    const precio = parseFloat(getEl("precio_venta")?.value);

    if (tipo !== "INSUMO") {
        if (isNaN(precio) || precio <= 0) {
            mostrarMensaje("El precio de venta es obligatorio ⚠️", "warning");
            return;
        }
    }

    const data = {
        nombre: getEl("nombre")?.value,
        codigo: getEl("codigo")?.value,
        categoria: getEl("categoria")?.value,
        unidad_id: getEl("unidad")?.value,
        tipo: tipo,
        precio_venta: tipo === "INSUMO" ? 0 : precio,
        stock: parseFloat(getEl("stock")?.value || 0)
    };

    try {

        const res = editandoId
            ? await apiFetch(`/productos/${editandoId}`, "PUT", data)
            : await apiFetch("/productos", "POST", data);

        if (res?.status === "error") {
            mostrarMensaje(res.message || "Error guardando producto ❌", "error");
            return;
        }

        mostrarMensaje(
            editandoId
                ? "Producto actualizado correctamente ✅"
                : "Producto creado correctamente ✅",
            "success"
        );

        cancelarEdicion();
        cargarProductos();

    } catch (error) {
        console.error("ERROR REAL:", error);
        mostrarMensaje(error.message || "Error guardando producto", "error");
    }
}


// =============================
// ESTADO
// =============================
window.eliminar = async function (id) {
    if (!confirm("¿Desactivar producto?")) return;

    await apiFetch(`/productos/${id}`, "DELETE");
    mostrarMensaje("Producto eliminado correctamente ✅", "success");
    cargarProductos();
};

window.activar = async function (id) {
    await apiFetch(`/productos/${id}/activar`, "PUT");
    mostrarMensaje("Producto activado correctamente ✅", "success");
    cargarProductos();
};


// =============================
// FILTRO
// =============================
window.filtrarProductos = async function () {

    const texto = getEl("busqueda")?.value.trim();

    if (!texto) {
        cargarProductos();
        return;
    }

    try {

        const res = await apiFetch(
            `/productos?page=1&limit=100&search=${encodeURIComponent(texto)}`
        );

        if (res?.status === "error") {
            mostrarMensaje("Error buscando productos ❌", "error");
            return;
        }

        pintarTabla(res.data || []);

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error buscando productos ❌", "error");
    }
};


// =============================
// UI
// =============================
function mostrarLoader() {
    const tabla = getEl("tablaProductos");
    if (tabla) {
        tabla.innerHTML = `<tr><td colspan="10">Cargando...</td></tr>`;
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


// =============================
// PAGINACIÓN
// =============================
window.nextPage = function () {
    currentPage++;
    cargarProductos();
};

window.prevPage = function () {
    if (currentPage > 1) {
        currentPage--;
        cargarProductos();
    }
};


// =============================
// UNIDADES
// =============================
async function cargarUnidades() {

    const select = getEl("unidad");
    if (!select) return;

    const res = await apiFetch("/unidades");

    if (!res || res.status === "error") return;

    select.innerHTML = "";

    res.data.forEach(u => {
        select.innerHTML += `
            <option value="${u.id}">
                ${u.nombre} (${u.abreviatura})
            </option>
        `;
    });
}


// =============================
function formatearFecha(fecha) {

    if (!fecha) return "";

    const f = new Date(fecha);

    const offset = 5 * 60;
    const local = new Date(f.getTime() + offset * 60000);

    const dia = String(local.getDate()).padStart(2, "0");
    const mes = String(local.getMonth() + 1).padStart(2, "0");
    const anio = local.getFullYear();

    const horas = String(local.getHours()).padStart(2, "0");
    const minutos = String(local.getMinutes()).padStart(2, "0");
    const segundos = String(local.getSeconds()).padStart(2, "0");

    return `${dia}/${mes}/${anio} ${horas}:${minutos}:${segundos}`;
}


// =============================
window.verCosto = async function (id) {

    const res = await apiFetch(`/costos/${id}`);

    if (!res || res.status === "error") {
        mostrarMensaje("Error obteniendo costos ❌", "error");
        return;
    }

    const c = res.data;

    mostrarMensaje(
        `💰 Costo: $${c.costo} | Utilidad: $${c.utilidad} | Margen: ${c.margen}%`,
        "success"
    );
};

// =============================
// 🔥 NUEVO: aplicar UI tipo
// =============================
function aplicarTipoUI(tipoSelect) {

    if (!tipoSelect) return;

    const precioInput = getEl("precio_venta");
    const container = getEl("container_precio");

    if (!precioInput) return;

    if (tipoSelect.value === "INSUMO") {
        precioInput.value = "";
        precioInput.disabled = true;
        precioInput.placeholder = "No aplica para insumos";

        if (container) container.style.display = "none";

    } else {
        precioInput.disabled = false;
        precioInput.placeholder = "Precio venta";

        if (container) container.style.display = "block";
    }
}
