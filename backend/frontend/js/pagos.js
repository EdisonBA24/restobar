import { apiFetch } from "./api.js";

let modo = "";

// =============================
// INIT
// =============================
document.addEventListener("DOMContentLoaded", () => {

    if (document.getElementById("usuario_id")) {
        cargarUsuarios();
    }

    if (document.getElementById("tablaPagos")) {
        modo = "consultar";
        cargarPagos();
    }

});

// =============================
// 👥 CARGAR EMPLEADOS
// =============================
async function cargarUsuarios() {

    try {

        const res = await apiFetch("/usuarios/select");

        if (!res || res.status === "error") {

            mostrarMensaje(
                "Error cargando empleados",
                "error"
            );

            return;

        }

        const select = document.getElementById("usuario_id");

        select.innerHTML = `
            <option value="">
                Seleccione un empleado
            </option>
        `;

        console.table(res.data);

        res.data.forEach(usuario => {

            console.log(usuario.id, usuario.nombre);

            select.innerHTML += `
                <option value="${usuario.id}">
                    ${usuario.nombre}
                </option>
            `;

        });

    } catch (e) {

        console.error(e);

        mostrarMensaje(
            "Error cargando empleados",
            "error"
        );

    }

}


// =============================
// 💾 GUARDAR PAGO
// =============================
window.guardarPago = async function () {

    const usuario_id = document.getElementById("usuario_id").value;
    const monto = parseFloat(document.getElementById("monto").value);
    const concepto = document.getElementById("concepto").value.trim();
    const fecha = document.getElementById("fecha").value;

    if (!usuario_id || isNaN(monto) || monto <= 0 || !concepto || !fecha) {
        mostrarMensaje("Completa todos los campos correctamente ⚠️", "warning");
        return;
    }

    try {

        const res = await apiFetch("/pagos", "POST", {
            usuario_id,
            monto,
            concepto,
            fecha
        });

        if (!res || res.status === "error") {
            mostrarMensaje(res?.message || "Error guardando pago ❌", "error");
            return;
        }

        mostrarMensaje("Pago registrado correctamente ✅");

        setTimeout(() => {
            window.location.href = "../pages/pagos.html";
        }, 1000);

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

        if (!res || res.status === "error") {
            mostrarMensaje("Error cargando pagos ❌", "error");
            return;
        }

        const tabla = document.getElementById("tablaPagos");
        tabla.innerHTML = "";

        const data = res.data || [];

        if (data.length === 0) {
            tabla.innerHTML = `<tr><td colspan="4">Sin registros</td></tr>`;
            return;
        }

        data.forEach(p => {

            tabla.innerHTML += `
                <tr>
                    <td>${p.empleado}</td>
                    <td>${formatoMoneda(p.monto)}</td>
                    <td>${p.concepto}</td>
                    <td>${formatearFecha(p.fecha)}</td>
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