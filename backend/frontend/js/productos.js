import { apiFetch } from "./api.js";
import { TablaUI } from "./tablas.js";

const STORAGE_PAGE_SIZE = "productos_page_size";

let tablaProductos = null;

let editandoId = null;

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

function limpiarFormularioProducto() {

    editandoId = null;

    const form = getEl("formProducto");

    if (form)
        form.reset();

    aplicarTipoUI(
        getEl("tipo")
    );

    setText(
        "formTitle",
        "Nuevo Producto"
    );

    const btn = getEl("btnGuardar");

    if (btn)
        btn.innerText = "Guardar";

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

// =============================
// INIT
// =============================
document.addEventListener("DOMContentLoaded", () => {

    if (getEl("tablaProductos")) {

        const pageSizeGuardado =
            Number(
                localStorage.getItem(STORAGE_PAGE_SIZE)
            ) || 10;

        tablaProductos = new TablaUI({

            nombre: "productos",

            callback: () => cargarProductos(),

            tabla: "#tablaProductosTabla",

            pageSize: "#pageSizeProductos",

            btnAnterior: "#btnPaginaAnterior",

            btnSiguiente: "#btnPaginaSiguiente",

            numeros: "#numerosPaginacion",

            resumen: "#resumenPaginacion",

            info: "#infoPaginacion"

        }).init();

        tablaProductos.actualizarDesdeBackend({

            page: 1,

            page_size: pageSizeGuardado,

            total: 0,

            total_pages: 1,

            sort_by: "id",

            sort_order: "desc"

        });

        cargarProductos();

    }

    if (getEl("unidad")) {
        cargarUnidades();
    }

    const form = getEl("formProducto");
    if (form) {
        form.addEventListener("submit", guardarProducto);
    }

    const btnNuevo = getEl("btnNuevo");

    if (btnNuevo) {

        btnNuevo.addEventListener(
            "click",
            mostrarFormulario
        );

    }

    const chk = getEl("verInactivos");
    if (chk) {
        chk.addEventListener("change", () => {

            tablaProductos.reiniciarPaginacion();

            cargarProductos();

        });
    }

    const tipoSelect = getEl("tipo");
    if (tipoSelect) tipoSelect.dispatchEvent(new Event("change"));

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

    if (!tablaProductos) {
        console.error("TablaUI no inicializada.");
        return;
    }

    mostrarLoader();

    const verInactivos = getEl("verInactivos")?.checked;
    const texto = getEl("busqueda")?.value.trim() || "";

    try {

        const params = new URLSearchParams({

            page: tablaProductos.page,

            limit: tablaProductos.pageSize,

            sort_by: tablaProductos.sortBy,

            sort_order: tablaProductos.sortOrder,

            inactivos: verInactivos
                ? "true"
                : "false",

            search: texto

        });

        const res = await apiFetch(`/productos?${params}`);

        const resultado = res.data;

        tablaProductos.actualizarDesdeBackend(resultado);

        const productos = resultado.items || [];

        pintarTabla(productos);

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error cargando productos",
            "error"
        );
    } finally {

        // futuro loader global

    }

}


// =============================
// TABLA
// =============================
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

                    <button
                        class="btn-action btn-edit"
                        onclick="editar(${p.id})">
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
// EDITAR
// =============================
window.editar = async function (id) {

    try {

        mostrarLoader();

        const res = await apiFetch(`/productos/${id}`);

        if (!res || res.status === "error") {

            mostrarMensaje(
                "Error obteniendo el producto ❌",
                "error"
            );

            return;

        }

        const p = res.data;

        editandoId = p.id;

        getEl("nombre").value = p.nombre || "";

        getEl("codigo").value = p.codigo || "";

        getEl("categoria").value = p.categoria || "";

        getEl("unidad").value = p.unidad_id || "";

        getEl("tipo").value = p.tipo || "";

        getEl("precio_venta").value = p.precio_venta || 0;

        getEl("stock").value = p.stock || 0;

        aplicarTipoUI(getEl("tipo"));

        setText(
            "formTitle",
            "Editar Producto"
        );

        const btn = getEl("btnGuardar");

        if (btn)
            btn.innerText = "Actualizar";

        getEl("formContainer")
            ?.classList.remove("hidden");

    } catch (error) {

        console.error(error);

        mostrarMensaje(
            "Error obteniendo producto ❌",
            "error"
        );

    }

};


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
// CANCELAR
// =============================
window.cancelarEdicion = function () {

    limpiarFormularioProducto();

    getEl("formContainer")
        ?.classList.add("hidden");

};


window.mostrarFormulario = function () {

    limpiarFormularioProducto();

    getEl("formContainer")
        ?.classList.remove("hidden");

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

        bloquearBotonGuardar();

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

        await cargarProductos();

    } catch (error) {
        console.error("ERROR REAL:", error);
        mostrarMensaje(error.message || "Error guardando producto", "error");
    } finally {
        desbloquearBotonGuardar();
    }
}


// =============================
// ESTADO
// =============================
window.eliminar = async function (id) {
    if (!confirm("¿Desactivar producto?")) return;

    await apiFetch(`/productos/${id}`, "DELETE");
    mostrarMensaje("Producto eliminado correctamente ✅", "success");
    await cargarProductos();
};

window.activar = async function (id) {
    await apiFetch(`/productos/${id}/activar`, "PUT");
    mostrarMensaje("Producto activado correctamente ✅", "success");
    await cargarProductos();
};


// =============================
// FILTRO
// =============================
window.filtrarProductos = function () {

    tablaProductos.reiniciarPaginacion();

    cargarProductos();

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


// =============================
// PAGINACIÓN
// =============================
window.nextPage = function () {

    tablaProductos.paginaSiguiente();

};

window.prevPage = function () {

    tablaProductos.paginaAnterior();

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
