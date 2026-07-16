import { apiFetch } from "./api.js";

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
}