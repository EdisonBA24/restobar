/*
=========================================================
ERP RESPONSIVE V3
Layout Global
=========================================================
*/

document.addEventListener("DOMContentLoaded", () => {

    const body = document.body;

    const sidebar = document.querySelector(".sidebar");

    const menuToggle = document.getElementById("menuToggle");

    const overlay = document.getElementById("sidebarOverlay");

    if (!sidebar || !menuToggle || !overlay) return;

    const MOBILE_BREAKPOINT = 992;

    function abrirMenu() {

        body.classList.add("sidebar-open");

    }

    function cerrarMenu() {

        body.classList.remove("sidebar-open");

    }

    function toggleMenu() {

        body.classList.toggle("sidebar-open");

    }

    menuToggle.addEventListener("click", toggleMenu);

    overlay.addEventListener("click", cerrarMenu);

    /*
    =========================================
    Cerrar al hacer click en una opción
    =========================================
    */

    sidebar.querySelectorAll(".submenu li").forEach(item => {

        item.addEventListener("click", () => {

            if (window.innerWidth <= MOBILE_BREAKPOINT) {
                cerrarMenu();
            }

        });

    });

    /*
    =========================================
    Tecla ESC
    =========================================
    */

    document.addEventListener("keydown", (e) => {

        if (e.key === "Escape") {

            cerrarMenu();

        }

    });

    /*
    =========================================
    Al volver a escritorio
    =========================================
    */

    window.addEventListener("resize", () => {

        if (window.innerWidth > MOBILE_BREAKPOINT) {

            cerrarMenu();

        }

    });

});

