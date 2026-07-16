import { apiFetch } from "./api.js";

let productos = [];

document.addEventListener("DOMContentLoaded", () => {
    cargarProductos();
});


// =============================
// CARGAR PRODUCTOS
// =============================
async function cargarProductos() {
    try {
        const res = await apiFetch("/productos?page=1&limit=100&inactivos=false");

        // 🔥 PROTECCIÓN
        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando productos ❌", "error");
            return;
        }

        productos = (res.data || []).filter(p =>
            p.tipo === "INSUMO" ||
            p.tipo === "LICORES" ||
            p.tipo === "BEBIDAS"
        );

    } catch (error) {
        console.error("Error productos:", error);
        mostrarMensaje("Error cargando productos ❌", "error");
    }
}


// =============================
// AGREGAR PRODUCTO
// =============================
window.agregarProducto = function () {

    const container = document.getElementById("productosCompra");
    const mensaje = document.getElementById("mensajeVacio");

    if (mensaje) mensaje.style.display = "none";

    const row = document.createElement("div");
    row.className = "compra-grid header-grid compra-item";

    row.innerHTML = `
        <select class="producto">
            <option value="">Seleccione</option>
            ${productos.map(p => `
                <option value="${p.id}">
                    ${p.nombre}
                </option>
            `).join("")}
        </select>

        <input type="number" class="cantidad text-center" placeholder="0">

        <input type="number" class="precio text-center" placeholder="0">

        <div class="subtotal text-right">$0</div>

        <button class="btn-remove">✖</button>
    `;

    const cantidad = row.querySelector(".cantidad");
    const precio = row.querySelector(".precio");

    cantidad.addEventListener("input", calcularTotal);
    precio.addEventListener("input", calcularTotal);

    row.querySelector(".btn-remove").addEventListener("click", () => {
        row.remove();

        if (container.children.length === 0 && mensaje) {
            mensaje.style.display = "block";
        }

        calcularTotal();
    });

    container.appendChild(row);
};


// =============================
// CALCULAR TOTAL
// =============================
function calcularTotal() {

    let total = 0;

    document.querySelectorAll(".compra-item").forEach(row => {

        const cantidad = parseFloat(row.querySelector(".cantidad").value);
        const precio = parseFloat(row.querySelector(".precio").value);

        const subtotal = (!isNaN(cantidad) && !isNaN(precio))
            ? cantidad * precio
            : 0;

        row.querySelector(".subtotal").innerText = formatoMoneda(subtotal);

        total += subtotal;
    });

    document.getElementById("totalCompra").innerText = formatoMoneda(total);
}


// =============================
// GUARDAR COMPRA
// =============================
window.guardarCompra = async function () {

    const proveedor = document.getElementById("proveedor").value;
    const filas = document.querySelectorAll("#productosCompra .compra-item");

    if (!proveedor) {
        mostrarMensaje("Ingresa proveedor ⚠️", "warning");
        return;
    }

    if (filas.length === 0) {
        mostrarMensaje("Agrega productos ⚠️", "warning");
        return;
    }

    let detalles = [];

    for (let f of filas) {

        const producto_id = f.querySelector(".producto").value;
        const cantidad = parseFloat(f.querySelector(".cantidad").value);
        const precio = parseFloat(f.querySelector(".precio").value);

        if (!producto_id || cantidad <= 0 || precio <= 0) {
            mostrarMensaje("Datos incompletos o inválidos ⚠️", "warning");
            return;
        }

        detalles.push({ producto_id, cantidad, precio });
    }

    try {

        const res = await apiFetch("/compras", "POST", {
            proveedor,
            usuario: "admin",
            detalles
        });

        if (!res || res.status === "error") {
            mostrarMensaje(res?.message || "Error en compra ❌", "error");
            return;
        }

        mostrarMensaje("Compra registrada correctamente ✅", "success");

        document.getElementById("productosCompra").innerHTML = "";
        document.getElementById("totalCompra").innerText = "$0";
        document.getElementById("proveedor").value = "";
        document.getElementById("mensajeVacio").style.display = "block";

    } catch (error) {
        console.error("Error compra:", error);
        mostrarMensaje("Error guardando compra ❌", "error");
    }
};


// =============================
// UTILIDADES
// =============================
function formatoMoneda(valor) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(valor || 0);
}


// =============================
// TOAST
// =============================
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
document.addEventListener("DOMContentLoaded", () => {

    if (document.getElementById("tablaCompras")) {
        cargarCompras();
    }
});


// =============================
// CARGAR COMPRAS
// =============================
async function cargarCompras() {

    try {

        const res = await apiFetch("/compras");

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando compras ❌", "error");
            return;
        }

        const tabla = document.getElementById("tablaCompras");
        tabla.innerHTML = "";

        (res.data || []).forEach(c => {

            tabla.innerHTML += `
                <tr onclick="verDetalle(${c.id})" style="cursor:pointer">
                    <td>${c.id}</td>
                    <td>${c.proveedor || ""}</td>
                    <td>${formatearFecha(c.fecha)}</td>
                    <td>${formatoMoneda(c.total)}</td>
                    <td>${c.usuario || ""}</td>
                </tr>
            `;
        });

    } catch (error) {
        console.error("Error compras:", error);
        mostrarMensaje("Error cargando compras ❌", "error");
    }
}


// =============================
window.verDetalle = async function (id) {

    try {

        const res = await apiFetch(`/compras/${id}`);

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando detalle ❌", "error");
            return;
        }

        const modal = document.getElementById("modalCompra");
        const body = document.getElementById("modalBody");

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
                            <td>${d.nombre}</td>
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
        console.error("Error detalle:", error);
        mostrarMensaje("Error cargando detalle ❌", "error");
    }
};

window.cerrarModal = function () {
    document.getElementById("modalCompra").classList.add("hidden");
};

document.addEventListener("click", function (e) {

    const modal = document.getElementById("modalCompra");

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