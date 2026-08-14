import { apiFetch } from "./api.js";

let usuarios = [];
let usuarioEditando = null;

// =============================
// HELPERS
// =============================
function getEl(id) {
    return document.getElementById(id);
}

function setText(id, text) {
    const el = getEl(id);
    if (el) el.innerText = text;
}

function escaparHTML(texto) {
    return (texto || "")
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
}


// =============================
// INIT
// =============================
document.addEventListener("DOMContentLoaded", () => {

    if (getEl("tablaUsuarios")) {
        cargarUsuarios();
    }

    const form = getEl("formUsuario");

    if (form) {
        form.addEventListener("submit", guardarUsuario);
    }
});


// =============================
// CARGAR USUARIOS
// =============================
async function cargarUsuarios() {

    try {

        mostrarLoader();

        const res = await apiFetch("/usuarios");

        usuarios = res?.data || [];

        const tabla = getEl("tablaUsuarios");

        if (!tabla) return;

        tabla.innerHTML = "";

        if (usuarios.length === 0) {
            tabla.innerHTML = `<tr><td colspan="5">Sin usuarios</td></tr>`;
            return;
        }

        usuarios.forEach(u => {

            tabla.innerHTML += `
                <tr>
                    <td>${escaparHTML(u.nombre)}</td>
                    <td>${escaparHTML(u.usuario)}</td>
                    <td>${escaparHTML(u.perfil || "")}</td>
                    <td>${u.activo ? "🟢 Activo" : "🔴 Inactivo"}</td>
                    <td>
                        <button class="btn-edit" onclick="editarUsuario(${u.id})">✏️</button>
                        <button class="btn-delete" onclick="toggleUsuario(${u.id}, ${u.activo})">
                            ${u.activo ? "🚫" : "✅"}
                        </button>
                    </td>
                </tr>
            `;
        });

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error cargando usuarios ❌", "error");
    }
}


// =============================
// GUARDAR (CREAR / EDITAR)
// =============================
async function guardarUsuario(e) {

    e.preventDefault();

    const data = {
        nombre: getEl("nombre")?.value.trim(),
        usuario: getEl("usuario")?.value.trim(),
        password: getEl("password")?.value.trim(),
        perfil: getEl("perfil")?.value,
        activo: getEl("activo")?.value
    };

    // =============================
    // VALIDACIONES
    // =============================

    if (!data.nombre || !data.usuario) {
        mostrarMensaje("Completa los campos obligatorios ⚠️", "warning");
        return;
    }

    // 🔥 evitar espacios raros
    data.usuario = data.usuario.replace(/\s+/g, "");

    // 🔥 VALIDAR DUPLICADO
    const duplicado = usuarios.find(u =>
        (u.usuario || "").toLowerCase() === data.usuario.toLowerCase() &&
        u.id !== usuarioEditando
    );

    if (duplicado) {
        mostrarMensaje("Usuario ya existe ⚠️", "warning");
        return;
    }

    try {

        if (usuarioEditando) {

            await apiFetch(`/usuarios/${usuarioEditando}`, "PUT", data);
            mostrarMensaje("Usuario actualizado ✅");

        } else {

            if (!data.password) {
                mostrarMensaje("La contraseña es obligatoria ⚠️", "warning");
                return;
            }

            if (data.password.length < 4) {
                mostrarMensaje("La contraseña debe tener mínimo 4 caracteres ⚠️", "warning");
                return;
            }

            await apiFetch("/usuarios", "POST", data);
            mostrarMensaje("Usuario creado ✅");

            // redirigir a la lista de usuarios después de 1 segundo
            setTimeout(() => {
                window.location.href = "../pages/usuarios.html";
            }, 1000);
        }

        cancelarEdicion();
        cargarUsuarios();

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error guardando usuario ❌", "error");
    }
}


// =============================
// EDITAR
// =============================
window.editarUsuario = function (id) {

    const u = usuarios.find(x => x.id === id);

    if (!u) return;

    usuarioEditando = id;

    getEl("formContainer")?.classList.remove("hidden");

    getEl("nombre").value = u.nombre || "";
    getEl("usuario").value = u.usuario || "";
    getEl("password").value = ""; // 🔥 seguridad
    getEl("perfil").value = u.perfil || "ventas";
    getEl("activo").value = u.activo ? "1" : "0";

    setText("formTitle", "Editar Usuario");
};


// =============================
// ACTIVAR / DESACTIVAR
// =============================
window.toggleUsuario = async function (id, activo) {

    try {

        if (!confirm("¿Cambiar estado del usuario?")) return;

        await apiFetch(`/usuarios/${id}/activar`, "PUT", {
            activo: activo ? 0 : 1
        });

        mostrarMensaje("Estado actualizado ✅");

        cargarUsuarios();

    } catch (error) {
        console.error(error);
        mostrarMensaje("Error actualizando estado ❌", "error");
    }
};


// =============================
// CANCELAR EDICIÓN
// =============================
window.cancelarEdicion = function () {

    usuarioEditando = null;

    const form = getEl("formUsuario");
    if (form) form.reset();

    getEl("formContainer")?.classList.add("hidden");

    setText("formTitle", "Nuevo Usuario");
};


// =============================
// LOADER
// =============================
function mostrarLoader() {
    const tabla = getEl("tablaUsuarios");
    if (tabla) {
        tabla.innerHTML = `<tr><td colspan="5">Cargando...</td></tr>`;
    }
}


// =============================
// MENSAJES
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