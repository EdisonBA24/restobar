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
        credentials: "include", // 🔥 CLAVE
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

        // ❌ error backend
        if (!res.ok) {
            const text = await res.text();
            console.error("API ERROR:", res.status, text);
            throw new Error(`Error ${res.status}`);
        }

        const json = await res.json();

        // 🔥 VALIDAR SESIÓN POR RESPUESTA
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
// 🔐 LOGIN (🔥 IMPORTANTE)
// ==============================
export async function login(usuario, password) {

    try {
        const res = await fetch(`${API_URL}/login`, {
            method: "POST",
            credentials: "include", // 🔥 CLAVE
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({ usuario, password })
        });

        if (!res.ok) {
            const text = await res.text();
            console.error("LOGIN ERROR:", text);
            throw new Error("Error en login");
        }

        const json = await res.json();

        // 🔥 VALIDAR RESPUESTA
        if (json.status !== "success") {
            throw new Error(json.message || "Credenciales inválidas");
        }

        // 🔥 GUARDAR USUARIO
        localStorage.setItem("usuario", JSON.stringify(json.data));

        return json;

    } catch (error) {
        console.error("ERROR LOGIN:", error);
        throw error;
    }
}

// ==============================
// 🔐 LOGOUT
// ==============================
export async function logout() {

    try {
        await fetch(`${API_URL}/logout`, {
            method: "POST",
            credentials: "include"
        });
    } catch (e) {
        console.warn("Error logout:", e);
    }

    localStorage.removeItem("usuario");
    window.location.href = "login.html";
}

// ==============================
// 🔥 VENTAS (SE MANTIENE)
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

        // 🔥 VALIDAR SESIÓN
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