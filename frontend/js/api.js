// 🔥 DETECCIÓN INTELIGENTE DE ENTORNO
const isLocal = window.location.hostname.includes("localhost") 
             || window.location.hostname.includes("127.0.0.1");

const API_URL = isLocal
    ? "http://127.0.0.1:5000/api"
    : "https://restobar.onrender.com";

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

        // 🔐 sesión expirada
        if (res.status === 401) {
            localStorage.removeItem("usuario");
            window.location.href = "login.html";
            return;
        }

        // ❌ error backend (IMPORTANTE)
        if (!res.ok) {
            const text = await res.text();
            console.error("API ERROR:", res.status, text);

            throw new Error(`Error ${res.status}`);
        }

        return await res.json();

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

        return await res.json();

    } catch (error) {
        console.error("FETCH ERROR VENTA:", error);
        throw error;
    }
}