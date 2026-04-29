// =============================
// 🔐 PROTEGER RUTAS (PRO)
// =============================
import { apiFetch } from "./api.js";

(async function () {

    const esLogin = window.location.pathname.includes("login.html");

    try {
        // 🔥 validar sesión real con backend
        const res = await apiFetch("/session");

        const usuario = localStorage.getItem("usuario");

        // ❌ no hay sesión válida
        if (!res || res.status !== "success") {
            localStorage.removeItem("usuario");

            if (!esLogin) {
                window.location.replace("login.html");
            }
            return;
        }

        // ✅ hay sesión válida
        if (usuario && esLogin) {
            window.location.replace("dashboard.html");
        }

    } catch (error) {
        console.error("Error validando sesión:", error);
        window.location.replace("login.html");
    }

})();