
import { apiFetch } from "./api.js";


// =====================================================
// MODO TACTIL
// =====================================================

if ("ontouchstart" in window) {

    document.body.classList.add("touch-mode");

}


// =====================================================
// USUARIO Y PERMISOS DE NAVEGACION
// =====================================================

document.addEventListener("DOMContentLoaded", () => {

    const rawUser = localStorage.getItem("usuario");

    if (!rawUser) {

        window.location.href = "login.html";

        return;

    }

    let user;

    try {

        user = JSON.parse(rawUser);

    } catch (error) {

        localStorage.removeItem("usuario");

        window.location.href = "login.html";

        return;

    }

    const perfil = String(
        user.perfil || ""
    ).trim().toUpperCase();


    // =============================================
    // OCULTAR OPCIONES ADMIN
    // =============================================

    if (perfil !== "ADMIN") {

        document.querySelectorAll(".solo-admin").forEach(element => {

            element.remove();

        });

    } else {

        insertarMenuCatalogo();

    }


    // =============================================
    // MOSTRAR USUARIO
    // =============================================

    const nombreEl = document.getElementById(
        "nombreUsuario"
    );

    if (nombreEl) {

        nombreEl.innerText = `👤 ${user.nombre}`;

    }

});


// =====================================================
// INSERTAR CATALOGO COMERCIAL
//
// Disponible solo para ADMIN.
// No modifica los menus existentes.
// =====================================================

function insertarMenuCatalogo() {

    const menu = document.querySelector(
        ".sidebar > ul"
    );

    if (!menu) return;

    if (menu.querySelector("[data-catalogo-entry]")) {
        return;
    }

    const item = document.createElement("li");

    item.className = "menu-item solo-admin";

    item.dataset.catalogoEntry = "true";

    item.innerHTML = `

        <div class="menu-title">

            <span>🗂️ Catálogo Comercial</span>

            <span class="menu-arrow">▾</span>

        </div>

        <ul class="submenu">

            <li data-catalogo-link>
                🏷️ Administración del catálogo
            </li>

        </ul>

    `;

    // Ubicar después de Productos si existe.
    const menuProductos = Array.from(
        menu.querySelectorAll(":scope > .menu-item")
    ).find(element =>
        element.textContent.toLowerCase().includes("productos")
    );

    if (menuProductos) {

        menuProductos.insertAdjacentElement(
            "afterend",
            item
        );

    } else {

        menu.appendChild(item);

    }

}


// =====================================================
// NAVEGACION AL CATALOGO
// =====================================================

document.addEventListener("click", event => {

    const catalogLink = event.target.closest(
        "[data-catalogo-link]"
    );

    if (catalogLink) {

        window.location.href = "/pages/catalogo.html";

    }

});


// =====================================================
// MENU LATERAL
// CONTROL DE SUBMENUS
// =====================================================

document.addEventListener("click", event => {

    const title = event.target.closest(
        ".menu-title"
    );

    if (!title) return;

    const menuItem = title.closest(
        ".menu-item"
    );

    const submenu = menuItem?.querySelector(
        ":scope > .submenu"
    );

    if (!submenu) return;

    const isOpen = submenu.classList.contains("open");

    document.querySelectorAll(".submenu.open").forEach(element => {

        element.classList.remove("open");

    });

    if (!isOpen) {

        submenu.classList.add("open");

    }

});


// =====================================================
// LOGOUT
// =====================================================

window.logout = async function () {

    try {

        await apiFetch(
            "/logout",
            "POST"
        );

    } catch (error) {

        console.error(
            "Logout error:",
            error
        );

    }

    localStorage.removeItem("usuario");

    window.location.href = "login.html";

};
