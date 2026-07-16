const API = window.location.hostname === "localhost"
    ? "http://127.0.0.1:5000"
    : "https://restobar.onrender.com"; // 🔥 MEJORA: dinámico


// =============================
// 🔥 ABRIR REPORTE
// =============================
async function abrirReporte(tipo) {

    let url = `${API}/api/reportes/${tipo}`;

    if (tipo === "ventas") {

        const inicio = document.getElementById("fecha_inicio")?.value || document.getElementById("inicio")?.value;
        const fin = document.getElementById("fecha_fin")?.value || document.getElementById("fin")?.value;

        if (inicio && fin) {
            url += `?inicio=${encodeURIComponent(inicio)}&fin=${encodeURIComponent(fin)}`; // 🔥 FIX seguridad URL
        }
    }

    try {

        mostrarLoader(); // 🔥 UX

        const res = await fetch(url, {
            credentials: "include"
        });

        if (res.status === 401) {
            localStorage.removeItem("usuario");
            window.location.href = "login.html";
            return;
        }

        if (!res.ok) {
            mostrarMensaje("Error en backend ❌", "error");
            limpiarTabla();
            return;
        }

        const data = await res.json();

        window.dataGlobal = data || []; // 🔥 FIX null safe

        renderTabla(window.dataGlobal);

    } catch (e) {
        console.error(e);
        mostrarMensaje("Error cargando datos ❌", "error");
        limpiarTabla();
    }
}


// =============================
// 💰 FORMATO MONEDA
// =============================
function formatoMoneda(valor) {
    return new Intl.NumberFormat("es-CO", {
        style: "currency",
        currency: "COP"
    }).format(valor || 0);
}


// =============================
// 📊 TABLA
// =============================
function renderTabla(data) {

    const contenedor = document.getElementById("contenido");

    if (!contenedor) return;

    if (!data || data.length === 0) {
        contenedor.innerHTML = "Sin datos";
        return;
    }

    let html = "<table border='1'><tr>";

    Object.keys(data[0]).forEach(k => {
        html += `<th>${k}</th>`;
    });

    html += "</tr>";

    data.forEach(row => {
        html += "<tr>";

        Object.entries(row).forEach(([key, value]) => {

            const k = key.toLowerCase();

            // 💰 MONEDA
            if (k.includes("costo") || k.includes("precio") || k.includes("utilidad") || k.includes("total") || k.includes("valor")) {
                value = formatoMoneda(value);
            }

            // 📅 FECHA
            if (k.includes("fecha") && value) {
                const f = new Date(value);
                if (!isNaN(f)) {
                    value = `${String(f.getDate()).padStart(2, "0")}/${String(f.getMonth() + 1).padStart(2, "0")}/${f.getFullYear()}`;
                }
            }

            // %
            if (k.includes("margen")) {
                value = `${value} %`;
            }

            // stock
            if (k.includes("stock")) {
                value = Number(value).toLocaleString("es-CO");
            }

            html += `<td>${value ?? ""}</td>`; // 🔥 FIX null
        });

        html += "</tr>";
    });

    html += "</table>";

    html += `
        <br>
        <button onclick='exportarExcel()'>Exportar Excel</button>
    `;

    contenedor.innerHTML = html;
}


// =============================
// 📥 EXPORTAR EXCEL
// =============================
async function exportarExcel() {

    if (!window.dataGlobal || window.dataGlobal.length === 0) {
        mostrarMensaje("Primero debes cargar datos ⚠️", "warning");
        return;
    }

    const dataLimpia = window.dataGlobal.map(row => {

        const nuevo = {};

        Object.entries(row).forEach(([k, v]) => {

            if (typeof v === "string") {

                let limpio = v.replace(/\$/g, "")
                    .replace(/\./g, "")
                    .replace(/,/g, "")
                    .replace("%", "")
                    .trim();

                if (!isNaN(limpio) && limpio !== "") {
                    v = Number(limpio);
                }
            }

            nuevo[k] = v;
        });

        return nuevo;
    });

    try {

        const res = await fetch(`${API}/api/reportes/exportar`, {
            method: "POST",
            credentials: "include",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
                data: dataLimpia,
                nombre: "reporte"
            })
        });

        if (res.status === 401) {
            localStorage.removeItem("usuario");
            window.location.href = "login.html";
            return;
        }

        if (!res.ok) {
            mostrarMensaje("Error generando Excel ❌", "error");
            return;
        }

        const blob = await res.blob();

        if (!blob || blob.size === 0) {
            mostrarMensaje("Archivo vacío ❌", "error");
            return;
        }

        const url = window.URL.createObjectURL(blob);

        const a = document.createElement("a");
        a.href = url;
        a.download = "reporte.xlsx";

        document.body.appendChild(a);
        a.click();
        a.remove();

        window.URL.revokeObjectURL(url); // 🔥 liberar memoria

    } catch (e) {
        console.error(e);
        mostrarMensaje("Error exportando Excel ❌", "error");
    }
}


// =============================
// 🔄 LOADER
// =============================
function mostrarLoader() {
    const contenedor = document.getElementById("contenido");
    if (contenedor) {
        contenedor.innerHTML = "Cargando...";
    }
}

function limpiarTabla() {
    const contenedor = document.getElementById("contenido");
    if (contenedor) {
        contenedor.innerHTML = "";
    }
}


// =============================
// 🔔 TOAST
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