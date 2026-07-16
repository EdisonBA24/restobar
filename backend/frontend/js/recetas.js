import { apiFetch } from "./api.js";

let detalle = [];
let insumosGlobal = [];
let modo = ""; // crear | consultar

document.addEventListener("DOMContentLoaded", () => {

    if (document.getElementById("ingredientesContainer")) {
        modo = "crear";
    }

    if (document.getElementById("tablaReceta") && !document.getElementById("ingredientesContainer")) {
        modo = "consultar";
    }

    if (document.getElementById("productoReceta")) {
        cargarProductosReceta();
    }

    cargarInsumosGlobal();
});


// =============================
// PRODUCTOS RECETA
// =============================
async function cargarProductosReceta() {

    try {

        const res = await apiFetch("/productos");

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando productos ❌", "error");
            return;
        }

        const select = document.getElementById("productoReceta");
        if (!select) return;

        select.innerHTML = "<option value=''>Seleccione receta</option>";

        (res.data || [])
            .filter(p => p.tipo === "RECETA")
            .forEach(p => {
                select.innerHTML += `<option value="${p.id}">${p.nombre}</option>`;
            });

        select.addEventListener("change", cargarReceta);

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando productos ❌", "error");
    }
}


// =============================
// INSUMOS
// =============================
async function cargarInsumosGlobal() {

    try {

        const res = await apiFetch("/productos?page=1&limit=1000&inactivos=false");

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando insumos ❌", "error");
            return;
        }

        insumosGlobal = (res.data || []).filter(p => p.tipo === "INSUMO");

        console.log("🧪 INSUMOS CARGADOS:", insumosGlobal.length);

        // 🔥 RE-RENDER SI YA HABÍA RECETA
        if (detalle && detalle.length > 0) {
            if (modo === "consultar") renderConsulta();
            if (modo === "crear") renderEditable();
        }

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando insumos ❌", "error");
    }
}


// =============================
// CARGAR RECETA
// =============================
async function cargarReceta() {

    const producto_id = document.getElementById("productoReceta")?.value;
    if (!producto_id) return;

    try {

        const res = await apiFetch(`/recetas/${producto_id}`);

        console.log("🧪 RESPUESTA RECETA:", res);

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando receta ❌", "error");
            return;
        }

        detalle = (res.detalle?.detalle || []).map(item => ({
            ...item,
            unidad: item.unidad || "Gr"
        }));

        console.log("📦 DETALLE CARGADO:", detalle);

        // 🔥 ASEGURAR INSUMOS
        if (!insumosGlobal || insumosGlobal.length === 0) {
            console.log("⏳ Esperando insumos...");
            await cargarInsumosGlobal();
        }

        if (modo === "crear") {
            document.getElementById("bloqueIngredientes")?.classList.remove("hidden");
            renderEditable();
        }

        if (modo === "consultar") {
            renderConsulta();
        }

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando receta ❌", "error");
    }
}


// =============================
// RENDER CONSULTA
// =============================
function renderConsulta() {

    const tabla = document.getElementById("tablaReceta");
    if (!tabla) return;

    tabla.innerHTML = "";

    if (!detalle || detalle.length === 0) {
        tabla.innerHTML = `<tr><td colspan="3">Sin datos</td></tr>`;
        return;
    }

    detalle.forEach(item => {

        const insumo = insumosGlobal.find(p => p.id == item.insumo_id);

        tabla.innerHTML += `
            <tr>
                <td>${insumo ? insumo.nombre : "⚠️ No encontrado"}</td>
                <td>${item.cantidad}</td>
                <td>${formatearUnidad(item.unidad)}</td>
            </tr>
        `;
    });
}


// =============================
// RENDER EDITABLE
// =============================
function renderEditable() {

    const container = document.getElementById("ingredientesContainer");
    if (!container) return;

    container.innerHTML = "";

    detalle.forEach((item, i) => {

        container.innerHTML += `
            <div class="form-grid">
                <select onchange="cambiarInsumo(${i}, this.value)">
                    <option value="">Seleccione insumo</option>
                    ${insumosGlobal.map(p => `
                        <option value="${p.id}" ${p.id == item.insumo_id ? "selected" : ""}>
                            ${p.nombre}
                        </option>
                    `).join("")}
                </select>

                <input type="number" value="${item.cantidad}"
                    onchange="cambiarCantidad(${i}, this.value)">

                <select onchange="cambiarUnidad(${i}, this.value)">
                    <option value="Gr" ${item.unidad == "Gr" ? "selected" : ""}>Gr</option>
                    <option value="Kg" ${item.unidad == "Kg" ? "selected" : ""}>Kg</option>
                    <option value="Und" ${item.unidad == "Und" ? "selected" : ""}>Und</option>
                </select>

                <button onclick="eliminarIngrediente(${i})">❌</button>
            </div>
        `;
    });
}


// =============================
// ACCIONES
// =============================
window.agregarIngrediente = function () {

    detalle.push({
        insumo_id: "",
        cantidad: 0,
        unidad: "Gr"
    });

    renderEditable();
};

window.cambiarInsumo = function (i, val) {
    detalle[i].insumo_id = parseInt(val);
};

window.cambiarCantidad = function (i, val) {
    detalle[i].cantidad = parseFloat(val) || 0;
};

window.cambiarUnidad = function(i, val) {
    detalle[i].unidad = val;
};

window.eliminarIngrediente = function (i) {
    detalle.splice(i, 1);
    renderEditable();
};


// =============================
// GUARDAR
// =============================
window.guardarReceta = async function () {

    const producto_id = document.getElementById("productoReceta")?.value;

    if (!producto_id) {
        mostrarMensaje("Seleccione receta ⚠️", "warning");
        return;
    }

    if (detalle.length === 0) {
        mostrarMensaje("Agregue ingredientes ⚠️", "warning");
        return;
    }

    if (detalle.some(d => !d.insumo_id || d.cantidad <= 0)) {
        mostrarMensaje("Complete correctamente los ingredientes ⚠️", "warning");
        return;
    }

    try {

        const res = await apiFetch("/recetas", "POST", {
            producto_id,
            detalle
        });

        if (!res || res.status === "error") {
            mostrarMensaje(res?.message || "Error guardando receta ❌", "error");
            return;
        }

        mostrarMensaje("Receta guardada exitosamente ✅", "success");

        detalle = [];
        renderEditable();

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error guardando receta ❌", "error");
    }
};


// =============================
// UTILIDADES
// =============================
function formatearUnidad(u) {
    if (u === "Gr") return "Gr";
    if (u === "Kg") return "Kg";
    if (u === "Und") return "Und";
    return u;
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