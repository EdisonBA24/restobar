import { apiFetch } from "./api.js";

let modo = "";

// =============================
// INIT
// =============================
document.addEventListener("DOMContentLoaded", () => {

    if (document.getElementById("tablaPagos")) {
        modo = "consultar";
        cargarPagos();
    }

});

// =============================
// 💾 GUARDAR PAGO
// =============================
window.guardarPago = async function () {

    const empleado = document.getElementById("empleado").value.trim();
    const monto = parseFloat(document.getElementById("monto").value);
    const concepto = document.getElementById("concepto").value.trim();
    const fecha = document.getElementById("fecha").value;

    // 🔥 VALIDACIÓN MEJORADA
    if (!empleado || isNaN(monto) || monto <= 0 || !concepto || !fecha) {
        mostrarMensaje("Completa todos los campos correctamente ⚠️", "warning");
        return;
    }

    try {

        const res = await apiFetch("/pagos", "POST", {
            empleado,
            monto,
            concepto,
            fecha
        });

        // 🔥 MANEJO DEFENSIVO
        if (!res || res.status === "error") {
            mostrarMensaje(res?.message || "Error guardando pago ❌", "error");
            return;
        }

        mostrarMensaje("Pago registrado correctamente ✅");

        // limpiar form
        document.getElementById("empleado").value = "";
        document.getElementById("monto").value = "";
        document.getElementById("concepto").value = "";
        document.getElementById("fecha").value = "";

    } catch (e) {
        console.error(e);
        mostrarMensaje("Error en servidor ❌", "error");
    }
};

// =============================
// 📄 CARGAR PAGOS
// =============================
async function cargarPagos() {

    try {

        const res = await apiFetch("/pagos");

        // 🔥 PROTECCIÓN
        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando pagos ❌", "error");
            return;
        }

        const tabla = document.getElementById("tablaPagos");
        tabla.innerHTML = "";

        const data = res.data || []; // 🔥 FIX

        if (data.length === 0) {
            tabla.innerHTML = `<tr><td colspan="5">Sin registros</td></tr>`;
            return;
        }

        data.forEach(p => {

            tabla.innerHTML += `
                <tr>
                    <td>${p.empleado}</td>
                    <td>${formatoMoneda(p.monto)}</td>
                    <td>${p.concepto}</td>
                    <td>${formatearFecha(p.fecha)}</td>
                    <td>${p.usuario || ""}</td>
                </tr>
            `;
        });

    } catch (e) {
        console.error(e);
        mostrarMensaje("Error cargando pagos ❌", "error");
    }
}

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