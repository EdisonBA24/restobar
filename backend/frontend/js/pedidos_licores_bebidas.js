import { apiFetch } from "./api.js";

let productos = [];
let modo = "";
let pedidoActual = null;

document.addEventListener("DOMContentLoaded", () => {

    if (document.getElementById("productosPedido")) {
        modo = "crear";
        cargarProductos();
    }

    if (document.getElementById("tablaPedidos")) {
        modo = "consultar";
        cargarPedidos();
    }

    const btnFacturar = document.getElementById("btnFacturar");

    if (btnFacturar) {
        btnFacturar.addEventListener("click", facturarPedido);
    }

});

// =============================
// CARGAR PRODUCTOS
// =============================
async function cargarProductos() {

    const categoria = document.body.dataset.categoria;

    const res = await apiFetch("/productos?page=1&limit=100&inactivos=false");

    productos = res.data.filter(p =>
        (p.tipo === "LICORES" || p.tipo === "BEBIDAS")
    );
}

// =============================
// AGREGAR PRODUCTO
// =============================
window.agregarProducto = function () {

    const container = document.getElementById("productosPedido");
    const mensaje = document.getElementById("mensajeVacio");

    if (mensaje) mensaje.style.display = "none";

    const row = document.createElement("div");
    row.className = "compra-item";

    row.innerHTML = `
        <select class="producto">
            ${productos.map(p => `
                <option value="${p.id}" data-precio="${p.precio_venta}">
                    ${p.nombre}
                </option>
            `).join("")}
        </select>

        <input type="number" class="cantidad" placeholder="0">
        <input type="number" class="precio" readonly>
        <div class="subtotal">$0</div>
        <button class="btn-remove">✖</button>
    `;

    const select = row.querySelector(".producto");
    const precioInput = row.querySelector(".precio");
    const cantidadInput = row.querySelector(".cantidad");

    const actualizar = () => {
        const option = select.options[select.selectedIndex];
        const precio = parseFloat(option.dataset.precio || 0);
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
    };

    actualizar();
    container.appendChild(row);
};

// =============================
function calcularTotal() {

    let total = 0;

    document.querySelectorAll(".compra-item").forEach(row => {

        const cantidad = parseFloat(row.querySelector(".cantidad").value) || 0;
        const precio = parseFloat(row.querySelector(".precio").value) || 0;

        total += cantidad * precio;
    });

    document.getElementById("totalPedido").innerText = formatoMoneda(total);
}

// =============================
// GUARDAR PEDIDO (🔥 FIX)
// =============================
window.guardarPedido = async function () {

    const filas = document.querySelectorAll(".compra-item");

    if (filas.length === 0) {
        mostrarMensaje("Agrega productos ⚠️", "warning");
        return;
    }

    let detalles = [];

    for (let f of filas) {

        const cantidad = parseFloat(f.querySelector(".cantidad").value);
        const precio = parseFloat(f.querySelector(".precio").value);

        if (cantidad <= 0 || precio <= 0) {
            mostrarMensaje("Datos inválidos ⚠️", "warning");
            return;
        }

        detalles.push({
            producto_id: f.querySelector(".producto").value,
            cantidad,
            precio
        });
    }

    try {

        const res = await apiFetch("/pedidos", "POST", {
            mesa: document.getElementById("mesa")?.value || "General",
            tipo: document.getElementById("tipoServicio")?.value || "MESA",
            cliente: document.getElementById("cliente")?.value || "General",
            cliente_id: document.getElementById("cliente")?.dataset.id || null,
            estado: "pendiente",
            detalles
        });

        if (res.status === "error") {
            mostrarMensaje(res.message, "error");
            return;
        }

        mostrarMensaje("Pedido registrado ✅", "success");

        // Redirigir a la lista de pedidos después de 1 segundo
        setTimeout(() => {
            window.location.href = "../pages/pedidos.html";
        }, 1000);

        document.getElementById("productosPedido").innerHTML = "";
        document.getElementById("totalPedido").innerText = "$0";

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error en pedido ❌", "error");
    }
};

// =============================
// CONSULTAR PEDIDOS
// =============================
async function cargarPedidos() {

    const res = await apiFetch("/pedidos");

    const tabla = document.getElementById("tablaPedidos");
    tabla.innerHTML = "";

    res.data.forEach(p => {

        let colorEstado = "";
        let badge = "";

        if (p.estado === "facturado") {
            colorEstado = "#d4edda";
            badge = "🟢 FACTURADO";
        } else {
            colorEstado = "#fff3cd";
            badge = "🟡 PENDIENTE";
        }

        tabla.innerHTML += `
            <tr onclick="verDetallePedido(${p.id}, '${p.estado}')" style="cursor:pointer; background:${colorEstado}">
                <td>${p.tipo}</td>
                <td>${p.mesa}</td>
                <td>${p.cliente || ""}</td>
                <td>${formatearFecha(p.fecha)}</td>
                <td>${formatoMoneda(p.total)}</td>
                <td>${p.usuario || ""}</td>
                <td>${badge}</td>
            </tr>
        `;
    });
}

// =============================
// DETALLE
// =============================
window.verDetallePedido = async function (id, estado) {

    pedidoActual = id;
    window.metodoSeleccionado = null;

    const res = await apiFetch(`/pedidos/${id}`);

    const modal = document.getElementById("modalCompra");
    const body = document.getElementById("modalBody");
    const btnFacturar = document.getElementById("btnFacturar");

    const header = `
        <div style="margin-bottom:10px;">
            <strong>Pedido #${id}</strong>
        </div>
    `;

    const detalle = `
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
                ${res.data.map(d => `
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

    body.innerHTML = header + detalle;

    if (btnFacturar) {
        btnFacturar.style.display = estado === "facturado" ? "none" : "inline-block";
    }

    modal.classList.remove("hidden");
};

// =============================
// FACTURAR (🔥 FIX)
// =============================
async function facturarPedido() {

    if (!pedidoActual) return;

    if (!window.metodoSeleccionado) {
        if (typeof abrirModalPago === "function") {
            abrirModalPago();
        } else {
            mostrarMensaje("Selecciona método de pago ⚠️", "warning");
        }
        return;
    }

    try {

        const data = await apiFetch(`/pedidos/${pedidoActual}/facturar`, "POST", {
            metodo_pago: window.metodoSeleccionado
        });

        if (data.status === "error") {
            mostrarMensaje(data.message, "error");
            return;
        }

        mostrarMensaje("Pedido facturado correctamente ✅", "success");

        document.getElementById("modalCompra").classList.add("hidden");

        window.metodoSeleccionado = null;

        if (modo === "consultar") {
            cargarPedidos();
        }

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error al facturar ❌", "error");
    }
}

// =============================
// UTILIDADES (TODO IGUAL)
// =============================
function formatoMoneda(v) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(v || 0);
}

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

window.metodoSeleccionado = null;

/* 🔥 TODO TU BLOQUE DE CLIENTES SIGUE EXACTAMENTE IGUAL DESDE AQUÍ HACIA ABAJO */
/* NO SE MODIFICA NADA */

// =============================
// 🔥 AUTOCOMPLETE CLIENTES (FIX REAL)
// =============================
let clientesCache = [];

async function cargarClientesAutocomplete() {
    const res = await apiFetch("/clientes?page=1&limit=100");
    clientesCache = res.data || [];
}

document.addEventListener("DOMContentLoaded", () => {

    const input = document.getElementById("cliente");

    if (input) {

        cargarClientesAutocomplete();

        input.addEventListener("input", function () {

            const valor = this.value.toLowerCase();
            const lista = document.getElementById("listaClientes");

            this.dataset.id = ""; // 🔥 FIX

            if (!valor) {
                lista.classList.add("hidden");
                return;
            }

            const filtrados = clientesCache.filter(c =>
                (c.nombre || "").toLowerCase().includes(valor) ||
                (c.documento || "").toLowerCase().includes(valor)
            );

            if (filtrados.length === 0) {

                lista.innerHTML = `
                    <div class="item-cliente no-result">
                        Cliente no encontrado
                    </div>
                    <div class="item-cliente crear-nuevo"
                        onclick="abrirCrearCliente()">
                        ➕ Crear cliente nuevo
                    </div>
                `;

            } else {

                lista.innerHTML = filtrados.map(c => `
                    <div class="item-cliente"
                        onclick="seleccionarCliente('${c.nombre}', ${c.id})">
                        ${c.nombre} - ${c.documento || ""}
                    </div>
                `).join("");
            }

            lista.classList.remove("hidden");
        });
    }
});

// =============================
// 🔥 GUARDAR CLIENTE RÁPIDO (FIX)
// =============================
window.guardarClienteRapido = async function () {

    const nombre = document.getElementById("nuevoNombre")?.value;
    const documento = document.getElementById("nuevoDocumento")?.value;
    const telefono = document.getElementById("nuevoTelefono")?.value;
    const direccion = document.getElementById("nuevoDireccion")?.value;
    const duplicado = validarClienteDuplicado();

    if (duplicado) {
    const confirmar = confirm(
        `El cliente ya existe (${duplicado.nombre}). ¿Deseas continuar?`
    );

    if (!confirmar) return;
}

    if (!nombre) {
        mostrarMensaje("El nombre es obligatorio ⚠️", "warning");
        return;
    }

    const data = {
        nombre,
        documento,
        telefono,
        direccion
    };

    try {

        const res = await apiFetch("/clientes", "POST", data);

        if (res.status === "error") {
            mostrarMensaje(res.message || "Error creando cliente ❌", "error");
            return;
        }

        mostrarMensaje("Cliente creado correctamente ✅", "success");

        // 🔥 recargar cache
        await cargarClientesAutocomplete();

        // 🔥 buscar cliente recién creado (por nombre)
        const nuevo = clientesCache.find(c =>
            (c.nombre || "").toLowerCase() === nombre.toLowerCase()
        );

        if (nuevo) {
            seleccionarCliente(nuevo.nombre, nuevo.id);
        } else {
            // fallback si no lo encuentra
            document.getElementById("cliente").value = nombre;
        }

        cerrarModalCliente();

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error al guardar cliente ❌", "error");
    }
};

window.abrirCrearCliente = function () {

    const nombre = document.getElementById("cliente").value;

    document.getElementById("nuevoNombre").value = nombre;

    document.getElementById("modalCliente").classList.remove("hidden");
};

window.cerrarModalCliente = function () {
    document.getElementById("modalCliente").classList.add("hidden");
};

// =============================
// 🔥 VALIDAR CLIENTE DUPLICADO
// =============================
function validarClienteDuplicado() {

    const nombre = document.getElementById("nuevoNombre")?.value.toLowerCase();
    const documento = document.getElementById("nuevoDocumento")?.value;

    if (!nombre && !documento) return;

    const duplicado = clientesCache.find(c =>
        (nombre && (c.nombre || "").toLowerCase() === nombre) ||
        (documento && (c.documento || "") === documento)
    );

    const warning = document.getElementById("warningCliente");

    if (duplicado) {

        warning.innerHTML = `⚠️ Cliente ya existe: <b>${duplicado.nombre}</b>`;
        warning.classList.remove("hidden");

        return duplicado;

    } else {
        warning.classList.add("hidden");
        return null;
    }
}