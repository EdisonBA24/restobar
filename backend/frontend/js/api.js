// 🔥 DETECCIÓN INTELIGENTE DE ENTORNO
const isLocal = window.location.hostname.includes("localhost")
    || window.location.hostname.includes("127.0.0.1");

const API_URL =
    location.hostname === "localhost" ||
        location.hostname === "127.0.0.1"
        ? "http://127.0.0.1:5000/api"
        : `${location.origin}/api`;

// ==============================
// 🔥 FETCH CENTRALIZADO
// ==============================
export async function apiFetch(url, method = "GET", data = null) {

    const options = {
        method,
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        }
    };

    if (data) {
        options.body = JSON.stringify(data);
    }

    try {
        const res = await fetch(`${API_URL}${url}`, options);

        // 🔐 sesión expirada por status
        if (res.status === 401 || res.status === 403) {
            console.warn("Sesión expirada (status)");

            localStorage.removeItem("usuario");
            window.location.href = "login.html";
            return;
        }

        // ❌ error backend (IMPORTANTE)
        if (!res.ok) {
            const text = await res.text();
            let message = `Error ${res.status}`;

            try {
                const errorJson = JSON.parse(text);
                message = errorJson.message || message;
            } catch (_) {
                message = text || message;
            }

            console.error("API ERROR:", res.status, text);

            throw new Error(message);
        }

        const json = await res.json();

        // 🔥 VALIDAR SESIÓN POR RESPUESTA (CLAVE)
        if (json.status === "unauthorized") {
            console.warn("Sesión expirada (respuesta)");

            localStorage.removeItem("usuario");
            window.location.href = "login.html";
            return;
        }

        return json;

    } catch (error) {
        console.error("FETCH ERROR:", error);
        throw error;
    }
}

// ==============================
// 🔥 VENTAS
// ==============================
export async function enviarVenta(data) {

    try {
        const res = await fetch(`${API_URL}/ventas`, {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify(data)
        });

        if (!res.ok) {
            const text = await res.text();
            console.error("ERROR VENTA:", text);
            throw new Error("Error enviando venta");
        }

        const json = await res.json();

        // 🔥 VALIDAR SESIÓN TAMBIÉN AQUÍ
        if (json.status === "unauthorized") {
            console.warn("Sesión expirada (venta)");

            localStorage.removeItem("usuario");
            window.location.href = "login.html";
            return;
        }

        return json;

    } catch (error) {
        console.error("FETCH ERROR VENTA:", error);
        throw error;
    }
}
