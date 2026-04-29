import { apiFetch } from "./api.js";

if ('ontouchstart' in window) {
    document.body.classList.add("touch-mode");
}

// =============================
// 🔐 USUARIO LOGUEADO (SINGLE SOURCE)
// =============================
document.addEventListener("DOMContentLoaded", () => {

    const rawUser = localStorage.getItem("usuario");

    if (!rawUser) {
        window.location.href = "login.html";
        return;
    }

    let user;

    try {
        user = JSON.parse(rawUser);
    } catch (err) {
        localStorage.removeItem("usuario");
        window.location.href = "login.html";
        return;
    }

    // =============================
    // 🔒 ROLES
    // =============================
    if (user.perfil !== "admin") {
        document.querySelectorAll(".solo-admin").forEach(el => el.remove());
    }

    // =============================
    // 👤 MOSTRAR USUARIO
    // =============================
    const nombreEl = document.getElementById("nombreUsuario");
    if (nombreEl) {
        nombreEl.innerText = `👤 ${user.nombre}`;
    }
});


// =============================
// 📌 MENÚ (FIX CLICK BUG)
// =============================
document.addEventListener("click", function (e) {

    const title = e.target.closest(".menu-title");
    if (!title) return;

    const menuItem = title.closest(".menu-item");
    const submenu = menuItem?.querySelector(":scope > .submenu");

    if (!submenu) return;

    const isOpen = submenu.classList.contains("open");

    // cerrar todos los submenus abiertos
    document.querySelectorAll(".submenu.open").forEach(s => {
        s.classList.remove("open");
    });

    // abrir el actual si no estaba abierto
    if (!isOpen) {
        submenu.classList.add("open");
    }
});


// =============================
// 🚪 LOGOUT
// =============================
window.logout = async function () {

    try {
        await apiFetch("/logout", "POST");
    } catch (e) {
        console.error("Logout error:", e);
    }

    localStorage.removeItem("usuario");
    window.location.href = "login.html";
};