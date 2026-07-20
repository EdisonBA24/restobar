// =============================
// 🌐 CONFIGURACIÓN
// =============================

// Utiliza siempre el mismo origen donde está cargada la aplicación
const API = "";

// Datos completos del reporte
window.dataGlobal = [];

// Configuración de paginación
const REGISTROS_POR_PAGINA = 10;
let paginaActual = 1;

// =============================
// 🚀 INICIALIZACIÓN AUTOMÁTICA
// =============================
document.addEventListener("DOMContentLoaded", () => {

    const pagina = window.location.pathname.toLowerCase();

    if (pagina.includes("reporte_inventario")) {
        abrirReporte("inventario");
    }
    else if (pagina.includes("reporte_ventas")) {
        abrirReporte("ventas");
    }
    else if (pagina.includes("reporte_costos")) {
        abrirReporte("costos");
    }

});


// =============================
// 🚀 ABRIR REPORTE
// =============================
async function abrirReporte(tipo) {

    let url = `${API}/api/reportes/${tipo}`;

    if (tipo === "ventas") {

        const inicio =
            document.getElementById("fecha_inicio")?.value ||
            document.getElementById("inicio")?.value;

        const fin =
            document.getElementById("fecha_fin")?.value ||
            document.getElementById("fin")?.value;

        if (inicio && fin) {
            url += `?inicio=${encodeURIComponent(inicio)}&fin=${encodeURIComponent(fin)}`;
        }
    }

    try {

        mostrarLoader();

        const res = await fetch(url, {
            credentials: "include"
        });

        if (res.status === 401) {

            localStorage.removeItem("usuario");
            window.location.href = "../pages/login.html";
            return;
        }

        if (!res.ok) {

            mostrarMensaje("Error consultando el reporte", "error");
            limpiarTabla();
            return;
        }

        const data = await res.json();

        window.dataGlobal = Array.isArray(data) ? data : [];

        paginaActual = 1;

        renderTabla(window.dataGlobal);

    } catch (error) {

        console.error(error);

        window.dataGlobal = [];

        limpiarTabla();

        mostrarMensaje("Error cargando el reporte", "error");
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
// 📊 RENDER TABLA
// =============================
function renderTabla(data) {

    const thead = document.getElementById("thead");
    const tbody = document.getElementById("tbody");

    if (!thead || !tbody) return;

    thead.innerHTML = "";
    tbody.innerHTML = "";

    if (!data || data.length === 0) {

        tbody.innerHTML = `
            <tr>
                <td colspan="100%" class="text-center">
                    Sin datos
                </td>
            </tr>
        `;

        renderPaginacion(0);

        return;
    }

    // =============================
    // PAGINACIÓN
    // =============================
    const inicio = (paginaActual - 1) * REGISTROS_POR_PAGINA;
    const fin = inicio + REGISTROS_POR_PAGINA;

    const datosPagina = data.slice(inicio, fin);

    // =============================
    // ENCABEZADOS
    // =============================
    const columnas = Object.keys(data[0]);

    let header = "<tr>";

    columnas.forEach(columna => {
        header += `<th>${columna}</th>`;
    });

    header += "</tr>";

    thead.innerHTML = header;

    // =============================
    // FILAS
    // =============================
    let filas = "";

    datosPagina.forEach(row => {

        filas += "<tr>";

        columnas.forEach(columna => {

            let value = row[columna];
            const key = columna.toLowerCase();

            // 💰 Moneda
            if (
                key.includes("precio") ||
                key.includes("costo") ||
                key.includes("valor") ||
                key.includes("utilidad") ||
                key.includes("total")
            ) {

                value = formatoMoneda(value);
            }

            // 📅 Fecha
            else if (key.includes("fecha") && value) {

                const fecha = new Date(value);

                if (!isNaN(fecha)) {

                    value =
                        `${String(fecha.getDate()).padStart(2, "0")}/` +
                        `${String(fecha.getMonth() + 1).padStart(2, "0")}/` +
                        `${fecha.getFullYear()}`;
                }
            }

            // %
            else if (key.includes("margen")) {

                value = `${value} %`;
            }

            // Stock
            else if (key.includes("stock")) {

                value = Number(value || 0).toLocaleString("es-CO");
            }

            filas += `<td>${value ?? ""}</td>`;

        });

        filas += "</tr>";

    });

    tbody.innerHTML = filas;

    // =============================
    // PAGINACIÓN
    // =============================
    renderPaginacion(data.length);

}

// =============================
// 📄 PAGINACIÓN
// =============================
function renderPaginacion(totalRegistros) {

    const contenedor = document.getElementById("paginacion");

    if (!contenedor) return;

    contenedor.innerHTML = "";

    // Si no hay datos o solo existe una página
    const totalPaginas = Math.ceil(totalRegistros / REGISTROS_POR_PAGINA);

    if (totalPaginas <= 1) {
        return;
    }

    let html = "";

    // =============================
    // BOTÓN ANTERIOR
    // =============================
    html += `
        <button
            class="btn-page"
            ${paginaActual === 1 ? "disabled" : ""}
            onclick="cambiarPagina(${paginaActual - 1})">
            ◀ Anterior
        </button>
    `;

    // =============================
    // NÚMEROS DE PÁGINA
    // =============================
    for (let i = 1; i <= totalPaginas; i++) {

        html += `
            <button
                class="btn-page ${i === paginaActual ? "active" : ""}"
                onclick="cambiarPagina(${i})">
                ${i}
            </button>
        `;
    }

    // =============================
    // BOTÓN SIGUIENTE
    // =============================
    html += `
        <button
            class="btn-page"
            ${paginaActual === totalPaginas ? "disabled" : ""}
            onclick="cambiarPagina(${paginaActual + 1})">
            Siguiente ▶
        </button>
    `;

    // =============================
    // INFORMACIÓN
    // =============================
    html += `
        <span class="page-info">
            Página ${paginaActual} de ${totalPaginas}
            (${totalRegistros} registros)
        </span>
    `;

    contenedor.innerHTML = html;
}

// =============================
// 📄 CAMBIAR PÁGINA
// =============================
function cambiarPagina(pagina) {

    const totalPaginas = Math.ceil(
        window.dataGlobal.length / REGISTROS_POR_PAGINA
    );

    if (pagina < 1 || pagina > totalPaginas) {
        return;
    }

    paginaActual = pagina;

    renderTabla(window.dataGlobal);
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

function mostrarEstadoTabla(mensaje) {

    const thead = document.getElementById("thead");
    const tbody = document.getElementById("tbody");

    if (!thead || !tbody) return;

    thead.innerHTML = "";

    tbody.innerHTML = `
        <tr>
            <td colspan="100%" class="text-center">
                ${mensaje}
            </td>
        </tr>
    `;
}


function mostrarLoader() {
    mostrarEstadoTabla("Cargando...");
}

function limpiarTabla() {
    window.dataGlobal = [];
    mostrarEstadoTabla("Sin datos");
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

window.abrirReporte = abrirReporte;
window.exportarExcel = exportarExcel;
window.cambiarPagina = cambiarPagina;