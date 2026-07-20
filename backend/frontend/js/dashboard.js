/*import { apiFetch } from "./api.js";

document.addEventListener("DOMContentLoaded", cargarDashboard);

async function cargarDashboard() {

    try {

        // 🔥 USAR apiFetch
        const json = await apiFetch("/dashboard");

        if (!json || json.status === "error") {
            console.error("Error backend");
            return;
        }

        const d = json.data;

        document.getElementById("ventas").innerText = formato(d.ventas_dia);
        document.getElementById("utilidad").innerText = formato(d.utilidad_dia);

        const tabla = document.getElementById("topProductos");
        tabla.innerHTML = "";

        d.top_productos.forEach(p => {
            tabla.innerHTML += `
                <tr>
                    <td>${p.producto}</td>
                    <td>${p.cantidad}</td>
                    <td>${formato(p.utilidad)}</td>
                </tr>
            `;
        });

    } catch (e) {
        console.error("ERROR DASHBOARD:", e);
    }
}

function formato(v) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(v || 0);
}*/

import { apiFetch } from "./api.js";

document.addEventListener("DOMContentLoaded", cargarDashboard);

async function cargarDashboard() {

    try {

        const json = await apiFetch("/dashboard");

        if (!json || json.status === "error") {
            console.error("Error obteniendo dashboard");
            return;
        }

        const d = json.data || {};

        // =============================
        // KPIs
        // =============================

        document.getElementById("ventas").innerText =
            formato(d.ventas_dia || 0);

        document.getElementById("cantidadVentas").innerText =
            (d.cantidad_ventas || 0).toLocaleString("es-CO");

        // =============================
        // TOP PRODUCTOS
        // =============================

        const tabla = document.getElementById("topProductos");

        tabla.innerHTML = "";

        (d.top_productos || []).forEach(p => {

            tabla.innerHTML += `
                <tr>
                    <td>${p.producto}</td>
                    <td>${p.cantidad}</td>
                    <td>${formato(p.ventas)}</td>
                </tr>
            `;

        });

    } catch (error) {

        console.error("ERROR DASHBOARD:", error);

    }

}

function formato(valor) {

    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(valor || 0);

}