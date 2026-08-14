import { apiFetch } from "./api.js";

let productos = [];
let modo = ""; // crear | consultar

// =============================
// HELPERS
// =============================
function getEl(id) {
    return document.getElementById(id);
}

function escaparHTML(texto) {
    return (texto || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}


// =============================
document.addEventListener("DOMContentLoaded", () => {

    if (getEl("productosVenta")) {
        modo = "crear";
        cargarProductos();
    }

    if (getEl("tablaVentas")) {
        modo = "consultar";
        cargarVentas();
    }

});


// =============================
// CARGAR PRODUCTOS
// =============================
async function cargarProductos() {

    try {

        const categoria = document.body.dataset.categoria;

        const res = await apiFetch("/productos?page=1&limit=100&inactivos=false");

        productos = (res.data || []).filter(p =>
            p.tipo === "RECETA" &&
            (!categoria || p.categoria === categoria)
        );

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando productos ❌", "error");
    }
}


// =============================
// AGREGAR PRODUCTO
// =============================
window.agregarProducto = function () {

    const container = getEl("productosVenta");
    const mensaje = getEl("mensajeVacio");

    if (!container) return;

    if (mensaje) mensaje.style.display = "none";

    const row = document.createElement("div");
    row.className = "compra-item";

    row.innerHTML = `
        <select class="producto">
            ${productos.map(p => `
                <option value="${p.id}" data-precio="${p.precio_venta}">
                    ${escaparHTML(p.nombre)}
                </option>
            `).join("")}
        </select>

        <input type="number" class="cantidad" placeholder="0" min="0">

        <input type="number" class="precio" readonly>

        <div class="subtotal">$0</div>

        <button class="btn-remove">✖</button>
    `;

    const select = row.querySelector(".producto");
    const precioInput = row.querySelector(".precio");
    const cantidadInput = row.querySelector(".cantidad");

    const actualizar = () => {

        const option = select.options[select.selectedIndex];
        const precio = parseFloat(option?.dataset?.precio || 0);
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

        if (container.children.length === 0 && mensaje) {
            mensaje.style.display = "block";
        }
    };

    actualizar();

    container.appendChild(row);
};


// =============================
function calcularTotal() {

    let total = 0;

    document.querySelectorAll(".compra-item").forEach(row => {

        const cantidad = parseFloat(row.querySelector(".cantidad")?.value) || 0;
        const precio = parseFloat(row.querySelector(".precio")?.value) || 0;

        total += cantidad * precio;
    });

    const totalEl = getEl("totalVenta");
    if (totalEl) {
        totalEl.innerText = formatoMoneda(total);
    }
}


// =============================
// GUARDAR
// =============================
window.guardarVenta = async function () {

    const filas = document.querySelectorAll(".compra-item");

    if (filas.length === 0) {
        mostrarMensaje("Agrega productos ⚠️", "warning");
        return;
    }

    let detalles = [];

    for (let f of filas) {

        const cantidad = parseFloat(f.querySelector(".cantidad")?.value);
        const precio = parseFloat(f.querySelector(".precio")?.value);

        if (!cantidad || cantidad <= 0 || !precio || precio <= 0) {
            mostrarMensaje("Datos inválidos ⚠️", "warning");
            return;
        }

        detalles.push({
            producto_id: f.querySelector(".producto")?.value,
            cantidad,
            precio
        });
    }

    try {

        // 🔥 VALIDAR STOCK
        //const validacion = await apiFetch("/ventas/validar-stock", "POST", { detalles });

        //if (validacion?.status === "error") {
        //    mostrarMensaje(validacion.message || "Error de stock ❌", "error");
        //    return;
        //

        // 🔥 USAR apiFetch (consistencia)
        const res = await apiFetch("/ventas", "POST", {
            cliente: getEl("cliente")?.value || "General",
            metodo_pago: getEl("metodo_pago")?.value || "Efectivo",
            usuario: "admin",
            detalles
        });

        if (res?.status === "error") {
            mostrarMensaje(res.message || "Error en la venta ❌", "error");
            return;
        }

        mostrarMensaje("Venta registrada ✅", "success");

        // 🔥 LIMPIAR UI
        getEl("productosVenta").innerHTML = "";
        getEl("totalVenta").innerText = "$0";

        const mensaje = getEl("mensajeVacio");
        if (mensaje) mensaje.style.display = "block";

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error en la venta ❌", "error");
    }
};


// =============================
// CONSULTAR VENTAS
// =============================
async function cargarVentas() {

    try {

        const res = await apiFetch("/ventas");

        const tabla = getEl("tablaVentas");
        if (!tabla) return;

        tabla.innerHTML = "";

        (res.data || []).forEach(v => {

            tabla.innerHTML += `
                <tr onclick="verDetalleVenta(${v.id})" style="cursor:pointer">
                    <td>${escaparHTML(v.cliente || "")}</td>
                    <td>${formatearFecha(v.fecha)}</td>
                    <td>${formatoMoneda(v.total)}</td>
                    <td>${escaparHTML(v.usuario || "")}</td>
                </tr>
            `;
        });

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando ventas ❌", "error");
    }
}


// =============================
// MODAL DETALLE
// =============================
window.verDetalleVenta = async function (id) {

    try {

        const res = await apiFetch(`/ventas/${id}`);

        const modal = getEl("modalCompra");
        const body = getEl("modalBody");

        if (!modal || !body) return;

        body.innerHTML = `
            <table class="table">
                <thead>
                    <tr>
                        <th>Producto</th>
                        <th>Cantidad</th>
                        <th>Precio</th>
                        <th>Subtotal</th>
                    </tr>
                </thead>
                <tbody>
                    ${(res.data || []).map(d => `
                        <tr>
                            <td>${escaparHTML(d.nombre)}</td>
                            <td>${d.cantidad}</td>
                            <td>${formatoMoneda(d.precio)}</td>
                            <td>${formatoMoneda(d.cantidad * d.precio)}</td>
                        </tr>
                    `).join("")}
                </tbody>
            </table>
        `;

        modal.classList.remove("hidden");

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando detalle ❌", "error");
    }
};


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


// =============================
// TOAST
// =============================
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
window.cerrarModal = function () {
    getEl("modalCompra")?.classList.add("hidden");
};

document.addEventListener("click", function (e) {

    const modal = getEl("modalCompra");

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