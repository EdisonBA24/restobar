
import {
    apiFetch,
    API_URL
} from "./api.js";

// =====================================================
// ESTADO DEL CATALOGO
// =====================================================

const state = {

    user: null,

    lineas: [],

    categorias: [],

    items: [],

    productos: [],

    lineaId: null,

    itemActual: null,

    categoriaActual: null,

    itemPreciosId: null,

    debounce: null,

    menuConfigId: null,

    menuActual: null,

    menuCategorias: [],

    menuCategoriaActual: null,

    productosCategoriaMenu: [],

};


// =====================================================
// HELPERS
// =====================================================

function el(id) {
    return document.getElementById(id);
}


function escapeHTML(value) {

    return String(value ?? "").replace(/[&<>"']/g, char => ({
        "&": "&amp;",
        "<": "&lt;",
        ">": "&gt;",
        '"': "&quot;",
        "'": "&#039;"
    })[char]);

}


function money(value) {

    return new Intl.NumberFormat("es-CO", {

        style: "currency",

        currency: "COP",

        maximumFractionDigits: 0

    }).format(Number(value) || 0);

}


function showToast(message, type = "success") {

    const container = el("catalogoToastContainer");

    if (!container) return;

    const toast = document.createElement("div");

    toast.className = `catalogo-toast ${type}`;

    toast.textContent = message;

    container.appendChild(toast);

    requestAnimationFrame(() => {

        toast.classList.add("show");

    });

    setTimeout(() => {

        toast.classList.remove("show");

        setTimeout(() => toast.remove(), 250);

    }, 4500);

}


function setLoading(container, message = "Cargando información...") {

    if (!container) return;

    container.innerHTML = `
        <div class="catalogo-loading">
            ${escapeHTML(message)}
        </div>
    `;

}


function validateSuccess(response) {

    if (!response || response.status !== "success") {

        throw new Error(
            response?.message || "No fue posible completar la operación."
        );

    }

    return response.data;

}


function openModal(id) {

    el(id)?.classList.remove("hidden");

}


function closeModal(id) {

    el(id)?.classList.add("hidden");

}


function getLineId() {

    return Number(
        el("catalogoLinea")?.value
    ) || null;

}


// =====================================================
// VALIDAR ADMINISTRADOR
// =====================================================

function validarAdministrador() {

    const raw = localStorage.getItem("usuario");

    if (!raw) {

        window.location.href = "/pages/login.html";

        return false;

    }

    try {

        state.user = JSON.parse(raw);

    } catch (error) {

        localStorage.removeItem("usuario");

        window.location.href = "/pages/login.html";

        return false;

    }

    const perfil = String(
        state.user?.perfil || ""
    ).trim().toUpperCase();

    if (perfil !== "ADMIN") {

        document.querySelector("main").innerHTML = `

            <section class="card catalogo-no-access">

                <div>🔒</div>

                <h2>Acceso restringido</h2>

                <p>
                    La administración del catálogo comercial
                    está disponible únicamente para usuarios ADMIN.
                </p>

                <button
                    type="button"
                    class="btn-primary"
                    id="btnVolverDashboard"
                >
                    Volver al inicio
                </button>

            </section>

        `;

        el("btnVolverDashboard")?.addEventListener(
            "click",
            () => {
                window.location.href = "/pages/dashboard.html";
            }
        );

        return false;

    }

    return true;

}


// =====================================================
// INICIALIZACION
// =====================================================

document.addEventListener("DOMContentLoaded", async () => {

    if (!el("catalogoLinea")) return;

    if (!validarAdministrador()) return;

    inicializarEventos();

    await cargarProductosDisponibles();

    await cargarLineas();

});


// =====================================================
// EVENTOS
// =====================================================

function inicializarEventos() {

    el("catalogoLinea")?.addEventListener(
        "change",
        cambiarLinea
    );


    // Pestañas

    document.querySelectorAll(".catalogo-tab").forEach(tab => {

        tab.addEventListener(
            "click",
            () => cambiarTab(tab.dataset.tab)
        );

    });


    // Artículos

    el("btnNuevoItem")?.addEventListener(
        "click",
        () => abrirFormularioItem()
    );

    el("buscarItem")?.addEventListener(
        "input",
        filtrarItems
    );

    el("filtroTipoItem")?.addEventListener(
        "change",
        cargarItems
    );

    el("formItemCatalogo")?.addEventListener(
        "submit",
        guardarItem
    );


    // Categorías

    el("btnNuevaCategoria")?.addEventListener(
        "click",
        () => abrirFormularioCategoria()
    );

    el("formCategoriaCatalogo")?.addEventListener(
        "submit",
        guardarCategoria
    );


    // =====================================================
    // CONFIGURACION DE MENUS
    // =====================================================

    el("btnNuevaCategoriaMenu")?.addEventListener(
        "click",
        () => abrirFormularioCategoriaMenu()
    );

    el("formCategoriaMenu")?.addEventListener(
        "submit",
        guardarCategoriaMenu
    );

    el("menuCategoriaObligatoria")?.addEventListener(
        "change",
        event => {

            const minimo = el("menuCategoriaMin");

            if (!event.target.checked) {

                minimo.value = "0";

            } else if (Number(minimo.value) < 1) {

                minimo.value = "1";

            }

        }
    );

    el("menuCategoriasLista")?.addEventListener(
        "click",
        ejecutarAccionCategoriaMenu
    );


    // =====================================================
    // PRODUCTOS DE CATEGORIAS
    // =====================================================

    el("buscarProductosCategoriaMenu")?.addEventListener(
        "input",
        filtrarProductosCategoriaMenu
    );

    el("btnGuardarProductosCategoriaMenu")?.addEventListener(
        "click",
        guardarProductosCategoriaMenu
    );


    // Tipo de artículo

    el("itemTipo")?.addEventListener(
        "change",
        actualizarFormularioTipo
    );

    el("itemProducto")?.addEventListener(
        "change",
        seleccionarProducto
    );


    // Imagen

    el("itemImagenArchivo")?.addEventListener(
        "change",
        subirImagenSeleccionada
    );


    // Precios

    el("formPreciosCatalogo")?.addEventListener(
        "submit",
        guardarPrecios
    );

    el("btnVerHistorialPrecios")?.addEventListener(
        "click",
        cargarHistorialPrecios
    );


    // Cierre de modales

    document.querySelectorAll("[data-close-modal]").forEach(button => {

        button.addEventListener(
            "click",
            () => closeModal(button.dataset.closeModal)
        );

    });

    document.querySelectorAll(".catalogo-modal").forEach(modal => {

        modal.addEventListener(
            "click",
            event => {

                if (event.target === modal) {

                    modal.classList.add("hidden");

                }

            }
        );

    });

}


// =====================================================
// LINEAS COMERCIALES
// =====================================================

async function cargarLineas() {

    const select = el("catalogoLinea");

    try {

        const response = await apiFetch(
            "/catalogo/lineas?incluir_inactivas=true"
        );

        const data = validateSuccess(response);

        state.lineas = Array.isArray(data)
            ? data
            : [];

        select.innerHTML = "";

        if (!state.lineas.length) {

            select.innerHTML = `
                <option value="">
                    No hay líneas comerciales
                </option>
            `;

            return;

        }

        state.lineas.forEach(linea => {

            const option = document.createElement("option");

            option.value = linea.id;

            option.textContent = linea.nombre;

            option.disabled = !linea.activo;

            select.appendChild(option);

        });

        const primeraActiva = state.lineas.find(
            linea => linea.activo
        );

        if (!primeraActiva) {

            showToast(
                "No hay líneas comerciales activas.",
                "warning"
            );

            return;

        }

        select.value = primeraActiva.id;

        state.lineaId = Number(primeraActiva.id);

        actualizarDescripcionLinea();

        await cargarDatosLinea();

    } catch (error) {

        console.error(
            "ERROR CARGANDO LINEAS:",
            error
        );

        showToast(
            error.message,
            "error"
        );

    }

}


function actualizarDescripcionLinea() {

    const linea = state.lineas.find(
        item => Number(item.id) === getLineId()
    );

    el("catalogoLineaDescripcion").textContent =
        linea?.descripcion || "Administra los artículos de esta línea comercial.";

}


// =====================================================
// CAMBIAR LINEA
// =====================================================

async function cambiarLinea() {

    state.lineaId = getLineId();

    actualizarDescripcionLinea();

    await cargarDatosLinea();

}


async function cargarDatosLinea() {

    if (!state.lineaId) return;

    await Promise.all([

        cargarCategorias(),

        cargarItems()

    ]);

}


// =====================================================
// CATEGORIAS COMERCIALES
// =====================================================

async function cargarCategorias() {

    const container = el("catalogoCategoriasList");

    setLoading(container);

    try {

        const response = await apiFetch(
            `/catalogo/categorias?linea_id=${state.lineaId}&incluir_inactivas=true`
        );

        const data = validateSuccess(response);

        state.categorias = Array.isArray(data)
            ? data
            : [];

        renderCategorias();

        actualizarSelectCategorias();

    } catch (error) {

        console.error(
            "ERROR CARGANDO CATEGORIAS:",
            error
        );

        container.innerHTML = `
            <div class="catalogo-error">
                No fue posible cargar las categorías.
            </div>
        `;

        showToast(
            error.message,
            "error"
        );

    }

}


// =====================================================
// PINTAR CATEGORIAS
// =====================================================

function renderCategorias() {

    const container = el("catalogoCategoriasList");

    const empty = el("catalogoCategoriasEmpty");

    container.innerHTML = "";

    empty.classList.toggle(
        "hidden",
        state.categorias.length > 0
    );

    state.categorias.forEach(categoria => {

        const card = document.createElement("article");

        card.className = "catalogo-category-card";

        card.innerHTML = `

            <div class="catalogo-category-info">

                <div class="catalogo-category-icon">
                    ${categoria.imagen_url
                ? `<img src="${escapeHTML(categoria.imagen_url)}" alt="">`
                : "🏷️"
            }
                </div>

                <div>

                    <h4>
                        ${escapeHTML(categoria.nombre)}
                    </h4>

                    <span>
                        ${escapeHTML(categoria.codigo)}
                    </span>

                    <p>
                        ${escapeHTML(categoria.descripcion || "Sin descripción")}
                    </p>

                </div>

            </div>

            <div class="catalogo-category-status">

                <span class="${categoria.activo ? "status-active" : "status-inactive"}">
                    ${categoria.activo ? "Activa" : "Inactiva"}
                </span>

            </div>

            <div class="catalogo-card-actions">

                <button
                    type="button"
                    class="btn-small btn-edit"
                    data-action="edit"
                    data-id="${categoria.id}"
                >
                    ✏️ Editar
                </button>

                <button
                    type="button"
                    class="btn-small ${categoria.activo ? "btn-danger-soft" : "btn-success-soft"}"
                    data-action="toggle"
                    data-id="${categoria.id}"
                    data-active="${categoria.activo ? "true" : "false"}"
                >
                    ${categoria.activo ? "Desactivar" : "Activar"}
                </button>

            </div>

        `;

        container.appendChild(card);

    });


    container.querySelectorAll("[data-action]").forEach(button => {

        button.addEventListener(
            "click",
            ejecutarAccionCategoria
        );

    });

}


// =====================================================
// SELECT DE CATEGORIAS
// =====================================================

function actualizarSelectCategorias(selectedId = null) {

    const select = el("itemCategoria");

    if (!select) return;

    select.innerHTML = `
        <option value="">
            Sin categoría
        </option>
    `;

    state.categorias
        .filter(categoria => categoria.activo)
        .forEach(categoria => {

            const option = document.createElement("option");

            option.value = categoria.id;

            option.textContent = categoria.nombre;

            select.appendChild(option);

        });

    if (selectedId) {
        select.value = String(selectedId);
    }

}


// =====================================================
// FORMULARIO CATEGORIA
// =====================================================

function abrirFormularioCategoria(categoria = null) {

    state.categoriaActual = categoria;

    el("formCategoriaCatalogo").reset();

    el("categoriaCatalogoId").value =
        categoria?.id || "";

    el("categoriaCodigo").value =
        categoria?.codigo || "";

    el("categoriaNombre").value =
        categoria?.nombre || "";

    el("categoriaDescripcion").value =
        categoria?.descripcion || "";

    el("categoriaImagen").value =
        categoria?.imagen_url || "";

    el("categoriaOrden").value =
        categoria?.orden ?? 0;

    el("categoriaActiva").checked =
        categoria?.activo ?? true;

    el("tituloModalCategoria").textContent =
        categoria
            ? "Editar categoría comercial"
            : "Nueva categoría comercial";

    el("btnGuardarCategoria").textContent =
        categoria
            ? "Actualizar categoría"
            : "Guardar categoría";

    openModal("modalCategoriaCatalogo");

}


async function guardarCategoria(event) {

    event.preventDefault();

    const id = el("categoriaCatalogoId").value;

    const data = {

        linea_id: state.lineaId,

        codigo: el("categoriaCodigo").value.trim(),

        nombre: el("categoriaNombre").value.trim(),

        descripcion: el("categoriaDescripcion").value.trim(),

        imagen_url: el("categoriaImagen").value.trim() || null,

        orden: Number(
            el("categoriaOrden").value
        ) || 0,

        activo: el("categoriaActiva").checked

    };

    const button = el("btnGuardarCategoria");

    button.disabled = true;

    try {

        const endpoint = id
            ? `/catalogo/categorias/${id}`
            : "/catalogo/categorias";

        const method = id
            ? "PUT"
            : "POST";

        const response = await apiFetch(
            endpoint,
            method,
            data
        );

        validateSuccess(response);

        closeModal("modalCategoriaCatalogo");

        showToast(
            id
                ? "Categoría actualizada correctamente."
                : "Categoría creada correctamente."
        );

        await cargarCategorias();

    } catch (error) {

        console.error(
            "ERROR GUARDANDO CATEGORIA:",
            error
        );

        showToast(
            error.message,
            "error"
        );

    } finally {

        button.disabled = false;

    }

}


// =====================================================
// ACCIONES CATEGORIA
// =====================================================

async function ejecutarAccionCategoria(event) {

    const button = event.currentTarget;

    const id = Number(button.dataset.id);

    const action = button.dataset.action;

    const categoria = state.categorias.find(
        item => Number(item.id) === id
    );

    if (!categoria) return;

    if (action === "edit") {

        abrirFormularioCategoria(categoria);

        return;

    }

    if (action === "toggle") {

        const nuevoEstado = !categoria.activo;

        const confirmar = confirm(
            nuevoEstado
                ? `¿Deseas activar la categoría ${categoria.nombre}?`
                : `¿Deseas desactivar la categoría ${categoria.nombre}?`
        );

        if (!confirmar) return;

        try {

            const response = await apiFetch(

                `/catalogo/categorias/${id}/estado`,

                "PATCH",

                {
                    activo: nuevoEstado
                }

            );

            validateSuccess(response);

            showToast(
                "Estado de la categoría actualizado."
            );

            await cargarCategorias();

        } catch (error) {

            showToast(
                error.message,
                "error"
            );

        }

    }

}


// =====================================================
// PRODUCTOS EXISTENTES
// =====================================================

async function cargarProductosDisponibles() {

    try {

        const response = await apiFetch(
            "/productos/autocomplete?tipo=RECETA&activo=true"
        );

        const data = validateSuccess(response);

        state.productos = Array.isArray(data)
            ? data
            : [];

    } catch (error) {

        console.error(
            "ERROR CARGANDO PRODUCTOS EXISTENTES:",
            error
        );

        state.productos = [];

        showToast(
            "No fue posible cargar los productos del inventario.",
            "error"
        );

    }

}


function actualizarSelectProductos(selectedId = null) {

    const select = el("itemProducto");

    if (!select) return;

    select.innerHTML = `
        <option value="">
            Seleccione un producto
        </option>
    `;

    state.productos.forEach(producto => {

        const option = document.createElement("option");

        option.value = producto.id;

        option.textContent =
            `${producto.nombre} (${producto.tipo})`;

        option.dataset.nombre = producto.nombre;

        option.dataset.codigo = producto.codigo || "";

        select.appendChild(option);

    });

    if (selectedId) {
        select.value = String(selectedId);
    }

}


function seleccionarProducto() {

    const select = el("itemProducto");

    const option = select.options[select.selectedIndex];

    if (!option?.value) return;

    if (
        !el("itemNombre").value.trim() ||
        state.itemActual?.producto_id
    ) {

        el("itemNombre").value =
            option.dataset.nombre || "";

    }

    if (
        !el("itemCodigo").value.trim() ||
        state.itemActual?.producto_id
    ) {

        el("itemCodigo").value =
            option.dataset.codigo || "";

    }

    if (!el("itemImagen").value.trim()) {

        const product = state.productos.find(
            item => Number(item.id) === Number(option.value)
        );

        if (product?.imagen_url) {

            el("itemImagen").value = product.imagen_url;

            actualizarVistaPrevia();

        }

    }

}


// =====================================================
// LISTAR ARTICULOS
// =====================================================

async function cargarItems() {

    if (!state.lineaId) return;

    const container = el("catalogoItemsGrid");

    setLoading(container);

    const params = new URLSearchParams({

        linea_id: String(state.lineaId),

        page: "1",

        page_size: "100",

        incluir_inactivos: "true"

    });

    const tipo = el("filtroTipoItem").value;

    const search = el("buscarItem").value.trim();

    if (tipo) {
        params.set("tipo_item", tipo);
    }

    if (search) {
        params.set("search", search);
    }

    try {

        const response = await apiFetch(
            `/catalogo/items?${params.toString()}`
        );

        const data = validateSuccess(response);

        state.items = Array.isArray(data.items)
            ? data.items
            : [];

        renderItems();

    } catch (error) {

        console.error(
            "ERROR LISTANDO ARTICULOS:",
            error
        );

        container.innerHTML = `
            <div class="catalogo-error">
                No fue posible cargar los artículos.
            </div>
        `;

        showToast(
            error.message,
            "error"
        );

    }

}


// =====================================================
// BUSQUEDA
// =====================================================

function filtrarItems() {

    clearTimeout(state.debounce);

    state.debounce = setTimeout(
        cargarItems,
        300
    );

}


// =====================================================
// RENDERIZAR ARTICULOS
// =====================================================

function renderItems() {

    const container = el("catalogoItemsGrid");

    const empty = el("catalogoItemsEmpty");

    container.innerHTML = "";

    empty.classList.toggle(
        "hidden",
        state.items.length > 0
    );

    state.items.forEach(item => {

        const card = document.createElement("article");

        card.className = "catalogo-item-card";

        const imageUrl = String(
            item.imagen_url || ""
        ).trim();

        const safeImage = (
            /^https?:\/\//i.test(imageUrl)
        );

        const image = safeImage
            ? `
                <img
                    src="${escapeHTML(imageUrl)}"
                    alt="${escapeHTML(item.nombre)}"
                    loading="lazy"
                >
            `
            : `
                <div class="catalogo-item-placeholder">
                    ${item.tipo_item === "MENU" ? "🍽️" :
                item.tipo_item === "COMBO" ? "🍱" : "📦"}
                </div>
            `;

        const precio = item.precio_general !== null &&
            item.precio_general !== undefined
            ? money(item.precio_general)
            : "Sin precio general";

        const esMenuConfigurables = [
            "MENU",
            "COMBO"
        ].includes(
            String(item.tipo_item || "").toUpperCase()
        );

        const botonConfigurarMenu = esMenuConfigurables
            ? `
            <button
                type="button"
                class="btn-small btn-menu-config"
                data-action="configure"
                data-id="${item.id}"
            >
                🍽️ Configurar composición
            </button>
            `
            : "";

        card.innerHTML = `

            <div class="catalogo-item-image">

                ${image}

                <span class="catalogo-type-badge">
                    ${escapeHTML(item.tipo_item)}
                </span>

                ${item.destacado
                ? `<span class="catalogo-featured-badge">Destacado</span>`
                : ""
            }

            </div>


            <div class="catalogo-item-content">

                <div class="catalogo-item-heading">

                    <div>

                        <h4>
                            ${escapeHTML(item.nombre)}
                        </h4>

                        <span>
                            ${escapeHTML(item.codigo)}
                        </span>

                    </div>

                    <span class="${item.activo ? "status-active" : "status-inactive"}">
                        ${item.activo ? "Activo" : "Inactivo"}
                    </span>

                </div>


                <p class="catalogo-item-description">
                    ${escapeHTML(item.descripcion || "Sin descripción")}
                </p>


                <div class="catalogo-item-meta">

                    <span>
                        ${escapeHTML(item.categoria_nombre || "Sin categoría")}
                    </span>

                    <strong>
                        ${escapeHTML(precio)}
                    </strong>

                </div>


                <div class="catalogo-card-actions">

                    <button
                        type="button"
                        class="btn-small btn-edit"
                        data-action="edit"
                        data-id="${item.id}"
                    >
                        ✏️ Editar
                    </button>

                    ${botonConfigurarMenu}

                    <button
                        type="button"
                        class="btn-small btn-price"
                        data-action="price"
                        data-id="${item.id}"
                    >
                        💰 Precios
                    </button>

                    <button
                        type="button"
                        class="btn-small ${item.activo ? "btn-danger-soft" : "btn-success-soft"}"
                        data-action="toggle"
                        data-id="${item.id}"
                    >
                        ${item.activo ? "Desactivar" : "Activar"}
                    </button>

                </div>

            </div>

        `;

        const imageElement = card.querySelector("img");

        imageElement?.addEventListener(
            "error",
            () => {

                const placeholder = document.createElement("div");

                placeholder.className = "catalogo-item-placeholder";

                placeholder.textContent = "📦";

                imageElement.replaceWith(placeholder);

            }
        );

        container.appendChild(card);

    });


    container.querySelectorAll("[data-action]").forEach(button => {

        button.addEventListener(
            "click",
            ejecutarAccionItem
        );

    });

}


// =====================================================
// CAMBIAR PESTAÑA
// =====================================================

function cambiarTab(tab) {

    document.querySelectorAll(".catalogo-tab").forEach(button => {

        button.classList.toggle(
            "active",
            button.dataset.tab === tab
        );

    });

    el("panelItems").classList.toggle(
        "hidden",
        tab !== "items"
    );

    el("panelCategorias").classList.toggle(
        "hidden",
        tab !== "categorias"
    );

}


// =====================================================
// FORMULARIO DE ARTICULOS
// =====================================================
async function abrirFormularioItem(item = null) {

    state.itemActual = null;

    if (item?.id) {

        try {

            const response = await apiFetch(
                `/catalogo/items/${item.id}`
            );

            state.itemActual = validateSuccess(response);

        } catch (error) {

            showToast(
                error.message,
                "error"
            );

            return;

        }

    }

    const current = state.itemActual;

    el("formItemCatalogo").reset();

    el("itemCatalogoId").value =
        current?.id || "";

    el("itemTipo").value =
        current?.tipo_item || "MENU";

    el("itemCodigo").value =
        current?.codigo || "";

    el("itemNombre").value =
        current?.nombre || "";

    el("itemDescripcion").value =
        current?.descripcion || "";

    el("itemImagen").value =
        current?.imagen_url || "";

    el("itemOrden").value =
        current?.orden ?? 0;

    el("itemActivo").checked =
        current?.activo ?? true;

    el("itemDestacado").checked =
        current?.destacado ?? false;

    el("itemPermitePersonalizar").checked =
        current?.permite_personalizar ?? true;

    actualizarSelectCategorias(
        current?.categoria_id
    );

    actualizarSelectProductos(
        current?.producto_id
    );

    actualizarFormularioTipo();

    actualizarVistaPrevia();

    el("tituloModalItem").textContent =
        current
            ? "Editar artículo comercial"
            : "Nuevo artículo comercial";

    el("btnGuardarItem").textContent =
        current
            ? "Actualizar artículo"
            : "Guardar artículo";

    openModal("modalItemCatalogo");

}



// =====================================================
// CAMBIAR TIPO DE ARTICULO
// =====================================================

function actualizarFormularioTipo() {

    const tipo = el("itemTipo").value;

    const esProducto = tipo === "PRODUCTO";

    const esMenuCombo = (
        tipo === "MENU" ||
        tipo === "COMBO"
    );

    document
        .querySelector(".catalogo-producto-selector")
        ?.classList.toggle("hidden", !esProducto);

    el("itemPermitePersonalizarContainer")
        ?.classList.toggle("hidden", !esMenuCombo);

    el("itemProducto").required = esProducto;

    el("itemNombre").readOnly = esProducto;

    if (!esProducto) {

        el("itemNombre").readOnly = false;

    } else {

        seleccionarProducto();

    }

}


// =====================================================
// SUBIR IMAGEN A SUPABASE STORAGE
// =====================================================

async function subirImagenSeleccionada(event) {

    const input = event.currentTarget;

    const archivo = input.files?.[0];

    const estado = el("itemImagenEstado");

    if (!archivo)
        return;

    const formatosPermitidos = [
        "image/jpeg",
        "image/png",
        "image/webp"
    ];

    if (!formatosPermitidos.includes(archivo.type)) {

        showToast(
            "Formato no permitido. Utilice JPG, PNG o WebP.",
            "error"
        );

        input.value = "";

        return;

    }

    if (archivo.size > 20 * 1024 * 1024) {

        showToast(
            "La fotografía original supera los 20 MB.",
            "error"
        );

        input.value = "";

        return;

    }

    const formData = new FormData();

    formData.append(
        "imagen",
        archivo,
        archivo.name
    );

    input.disabled = true;

    if (estado) {

        estado.textContent =
            "Optimizando y cargando fotografía...";

    }

    try {

        const response = await fetch(
            `${API_URL}/catalogo/imagenes`,
            {
                method: "POST",

                credentials: "include",

                // No configurar Content-Type:
                // el navegador agrega automáticamente
                // el boundary del multipart/form-data.

                body: formData
            }
        );

        if (response.status === 401) {

            localStorage.removeItem("usuario");

            window.location.href = "/pages/login.html";

            return;

        }

        const resultado = await response.json();

        if (
            !response.ok ||
            resultado.status !== "success"
        ) {

            throw new Error(
                resultado.message ||
                "No fue posible cargar la fotografía."
            );

        }

        const url = resultado.data?.url;

        if (!url) {

            throw new Error(
                "Supabase no devolvió la URL de la fotografía."
            );

        }

        // Guardar URL para que guardarItem()
        // la persista en catalogo_items.imagen_url.

        el("itemImagen").value = url;

        actualizarVistaPrevia();

        const sizeKB = (
            Number(resultado.data.size_bytes || 0) / 1024
        ).toFixed(1);

        if (estado) {

            estado.textContent =
                `Fotografía optimizada y cargada: ${sizeKB} KB. Guarde el artículo para asociarla.`;

        }

        showToast(
            "Fotografía cargada correctamente."
        );

    } catch (error) {

        console.error(
            "ERROR SUBIENDO IMAGEN:",
            error
        );

        if (estado) {

            estado.textContent =
                error.message;

        }

        showToast(
            error.message,
            "error"
        );

    } finally {

        input.disabled = false;

        input.value = "";

    }

}


// =====================================================
// VISTA PREVIA IMAGEN
// =====================================================

function actualizarVistaPrevia() {

    const url = el("itemImagen").value.trim();

    const image = el("itemImagenPreview");

    const placeholder = el("itemImagenPlaceholder");

    if (!/^https?:\/\//i.test(url)) {

        image.classList.add("hidden");

        image.removeAttribute("src");

        placeholder.classList.remove("hidden");

        return;

    }

    image.src = url;

    image.classList.remove("hidden");

    placeholder.classList.add("hidden");

    image.onerror = () => {

        image.classList.add("hidden");

        placeholder.classList.remove("hidden");

    };

}


// =====================================================
// GUARDAR ARTICULO
// =====================================================

async function guardarItem(event) {

    event.preventDefault();

    const id = el("itemCatalogoId").value;

    const tipo = el("itemTipo").value;

    const productoId = tipo === "PRODUCTO"
        ? Number(el("itemProducto").value)
        : null;

    const data = {

        linea_id: state.lineaId,

        categoria_id: Number(
            el("itemCategoria").value
        ) || null,

        producto_id: productoId,

        codigo: el("itemCodigo").value.trim(),

        tipo_item: tipo,

        nombre: el("itemNombre").value.trim(),

        descripcion: el("itemDescripcion").value.trim(),

        imagen_url: el("itemImagen").value.trim() || null,

        activo: el("itemActivo").checked,

        destacado: el("itemDestacado").checked,

        orden: Number(
            el("itemOrden").value
        ) || 0,

        permite_personalizar:
            el("itemPermitePersonalizar").checked

    };

    const button = el("btnGuardarItem");

    button.disabled = true;

    try {

        const endpoint = id
            ? `/catalogo/items/${id}`
            : "/catalogo/items";

        const method = id
            ? "PUT"
            : "POST";

        const response = await apiFetch(
            endpoint,
            method,
            data
        );

        const result = validateSuccess(response);

        const itemId = id
            ? Number(id)
            : Number(result.id);

        closeModal("modalItemCatalogo");

        showToast(
            id
                ? "Artículo actualizado correctamente."
                : "Artículo creado correctamente."
        );

        await cargarItems();

        // Si es un nuevo menú o combo,
        // abrimos su configuración de precios.

        if (!id && (tipo === "MENU" || tipo === "COMBO")) {

            const item = state.items.find(
                registro => Number(registro.id) === itemId
            );

            await abrirModalPrecios(
                itemId,
                item?.nombre || data.nombre
            );

        }

    } catch (error) {

        console.error(
            "ERROR GUARDANDO ARTICULO:",
            error
        );

        showToast(
            error.message,
            "error"
        );

    } finally {

        button.disabled = false;

    }

}


// =====================================================
// ACCIONES DE ARTICULOS
// =====================================================

async function ejecutarAccionItem(event) {

    const button = event.currentTarget;

    const id = Number(button.dataset.id);

    const action = button.dataset.action;

    const item = state.items.find(
        registro => Number(registro.id) === id
    );

    if (!item) return;


    if (action === "edit") {

        await abrirFormularioItem(item);

        return;

    }


    if (action === "configure") {

        if (!["MENU", "COMBO"].includes(item.tipo_item)) {

            showToast(
                "La composición solo está disponible para menús y combos.",
                "warning"
            );

            return;

        }

        await abrirConfiguracionMenu(item);

        return;

    }


    if (action === "price") {

        await abrirModalPrecios(
            id,
            item.nombre
        );

        return;

    }


    if (action === "toggle") {

        const nuevoEstado = !item.activo;

        const confirmar = confirm(

            nuevoEstado

                ? `¿Deseas activar ${item.nombre}?`

                : `¿Deseas desactivar ${item.nombre}?`

        );

        if (!confirmar) return;

        try {

            const response = await apiFetch(

                `/catalogo/items/${id}/estado`,

                "PATCH",

                {
                    activo: nuevoEstado
                }

            );

            validateSuccess(response);

            showToast(
                "Estado del artículo actualizado."
            );

            await cargarItems();

        } catch (error) {

            showToast(
                error.message,
                "error"
            );

        }

    }

}


// =====================================================
// PRECIOS COMERCIALES
// =====================================================

async function abrirModalPrecios(itemId, nombre) {

    state.itemPreciosId = Number(itemId);

    el("nombreItemPrecios").textContent = nombre;

    el("motivoCambioPrecio").value = "";

    el("catalogoHistorialPrecios").classList.add("hidden");

    el("catalogoHistorialPreciosLista").innerHTML = "";

    const rows = document.querySelectorAll(
        ".catalogo-price-row"
    );

    rows.forEach(row => {

        row.dataset.exists = "false";

        const input = row.querySelector(".precio-servicio");

        const active = row.querySelector(".precio-activo");

        input.value = "";

        active.checked = true;

    });

    try {

        const response = await apiFetch(
            `/catalogo/items/${itemId}/precios`
        );

        const precios = validateSuccess(response);

        precios.forEach(precio => {

            const row = document.querySelector(
                `.catalogo-price-row[data-service="${precio.tipo_servicio}"]`
            );

            if (!row) return;

            row.dataset.exists = "true";

            row.querySelector(".precio-servicio").value =
                precio.precio;

            row.querySelector(".precio-activo").checked =
                Boolean(precio.activo);

        });

        openModal("modalPreciosCatalogo");

    } catch (error) {

        showToast(
            error.message,
            "error"
        );

    }

}


// =====================================================
// GUARDAR PRECIOS
// =====================================================


async function guardarPrecios(event) {

    event.preventDefault();

    if (!state.itemPreciosId) return;

    const button = el("btnGuardarPrecios");

    button.disabled = true;

    try {

        const precios = [];

        const motivo = el(
            "motivoCambioPrecio"
        ).value.trim();

        const rows = document.querySelectorAll(
            ".catalogo-price-row"
        );

        for (const row of rows) {

            const input = row.querySelector(
                ".precio-servicio"
            );

            const active = row.querySelector(
                ".precio-activo"
            );

            const value = input.value.trim();

            const exists = (
                row.dataset.exists === "true"
            );

            if (!value && !exists) {
                continue;
            }

            if (!value && exists) {

                throw new Error(
                    `El precio de ${row.dataset.service} no puede quedar vacío.`
                );

            }

            const price = Number(value);

            if (
                !Number.isFinite(price) ||
                price < 0
            ) {

                throw new Error(
                    `El precio de ${row.dataset.service} no es válido.`
                );

            }

            precios.push({

                tipo_servicio: row.dataset.service,

                precio: price,

                activo: active.checked,

                motivo

            });

        }

        if (!precios.length) {

            throw new Error(
                "Configura al menos un precio."
            );

        }

        const response = await apiFetch(

            `/catalogo/items/${state.itemPreciosId}/precios`,

            "PUT",

            {
                precios
            }

        );

        validateSuccess(response);

        showToast(
            "Precios guardados y registrados en el historial."
        );

        closeModal("modalPreciosCatalogo");

        await cargarItems();

    } catch (error) {

        console.error(
            "ERROR GUARDANDO PRECIOS:",
            error
        );

        showToast(
            error.message || "No fue posible guardar los precios.",
            "error"
        );

    } finally {

        button.disabled = false;

    }

}



// =====================================================
// HISTORIAL DE PRECIOS
// =====================================================

async function cargarHistorialPrecios() {

    if (!state.itemPreciosId) return;

    const container = el("catalogoHistorialPreciosLista");

    setLoading(container);

    el("catalogoHistorialPrecios").classList.remove("hidden");

    try {

        const response = await apiFetch(
            `/catalogo/items/${state.itemPreciosId}/historial-precios?limit=100`
        );

        const data = validateSuccess(response);

        if (!data.length) {

            container.innerHTML = `
                <div class="catalogo-history-empty">
                    Este artículo todavía no tiene modificaciones de precios.
                </div>
            `;

            return;

        }

        container.innerHTML = `

            <div class="catalogo-history-table-wrap">

                <table class="catalogo-history-table">

                    <thead>

                        <tr>

                            <th>Fecha</th>

                            <th>Modalidad</th>

                            <th>Anterior</th>

                            <th>Nuevo</th>

                            <th>Administrador</th>

                            <th>Motivo</th>

                        </tr>

                    </thead>

                    <tbody>

                        ${data.map(record => `

                            <tr>

                                <td>
                                    ${escapeHTML(record.fecha_cambio || "")}
                                </td>

                                <td>
                                    ${escapeHTML(record.tipo_servicio)}
                                </td>

                                <td>
                                    ${record.precio_anterior === null
                ? "Inicial"
                : money(record.precio_anterior)
            }
                                </td>

                                <td>
                                    <strong>
                                        ${money(record.precio_nuevo)}
                                    </strong>
                                </td>

                                <td>
                                    ${escapeHTML(record.usuario || "ADMIN")}
                                </td>

                                <td>
                                    ${escapeHTML(record.motivo || "-")}
                                </td>

                            </tr>

                        `).join("")}

                    </tbody>

                </table>

            </div>

        `;

    } catch (error) {

        container.innerHTML = `
            <div class="catalogo-error">
                No fue posible consultar el historial.
            </div>
        `;

        showToast(
            error.message,
            "error"
        );

    }

}



// =====================================================
// CONFIGURACION INTERNA DE MENUS
// =====================================================


// =====================================================
// ABRIR CONFIGURACION DEL MENU
// =====================================================

async function abrirConfiguracionMenu(item) {

    state.menuConfigId = Number(item.id);

    state.menuActual = item;

    state.menuCategorias = [];

    el("menuConfigTitulo").textContent =
        `Configurar: ${item.nombre}`;

    el("menuConfigEstado").textContent =
        item.activo ? "Menú activo" : "Menú inactivo";

    setLoading(
        el("menuCategoriasLista"),
        "Consultando categorías y productos..."
    );

    openModal("modalConfiguracionMenu");

    await cargarConfiguracionMenu();

}


// =====================================================
// CONSULTAR CONFIGURACION COMPLETA
// =====================================================

async function cargarConfiguracionMenu() {

    if (!state.menuConfigId) return;

    try {

        const response = await apiFetch(

            `/catalogo/items/${state.menuConfigId}/configuracion-menu?incluir_inactivas=true`

        );

        const data = validateSuccess(response);

        state.menuActual = data;

        state.menuCategorias = Array.isArray(
            data.categorias
        )
            ? data.categorias
            : [];

        el("menuConfigTitulo").textContent =
            `Configurar: ${data.nombre}`;

        renderCategoriasMenu();

    } catch (error) {

        console.error(
            "ERROR CONSULTANDO CONFIGURACION MENU:",
            error
        );

        el("menuCategoriasLista").innerHTML = `
            <div class="catalogo-error">
                ${escapeHTML(error.message)}
            </div>
        `;

        showToast(
            error.message,
            "error"
        );

    }

}


// =====================================================
// RENDERIZAR CATEGORIAS DEL MENU
// =====================================================

function renderCategoriasMenu() {

    const container = el("menuCategoriasLista");

    const empty = el("menuCategoriasEmpty");

    container.innerHTML = "";

    empty.classList.toggle(
        "hidden",
        state.menuCategorias.length > 0
    );

    if (!state.menuCategorias.length) {
        return;
    }

    state.menuCategorias.forEach(categoria => {

        const productos = Array.isArray(
            categoria.productos
        )
            ? categoria.productos
            : [];

        const activos = productos.filter(
            producto => Boolean(producto.activo)
        ).length;

        const card = document.createElement("article");

        card.className = "menu-categoria-card";

        card.innerHTML = `

            <div class="menu-categoria-top">

                <div>

                    <div class="menu-categoria-code">
                        ${escapeHTML(categoria.codigo)}
                    </div>

                    <h4>
                        ${escapeHTML(categoria.nombre)}
                    </h4>

                    <p>
                        ${escapeHTML(
            categoria.descripcion || "Sin descripción"
        )}
                    </p>

                </div>

                <span class="${categoria.activo ? "status-active" : "status-inactive"}">
                    ${categoria.activo ? "Activa" : "Inactiva"}
                </span>

            </div>


            <div class="menu-categoria-reglas">

                <span>
                    ${categoria.obligatorio ? "Obligatoria" : "Opcional"}
                </span>

                <span>
                    Mínimo: ${categoria.min_selecciones}
                </span>

                <span>
                    Máximo: ${categoria.max_selecciones}
                </span>

                <span>
                    ${activos} producto(s) activo(s)
                </span>

            </div>


            <div class="catalogo-card-actions">

                <button
                    type="button"
                    class="btn-small btn-edit"
                    data-menu-action="edit"
                    data-id="${categoria.id}"
                >
                    ✏️ Editar
                </button>

                <button
                    type="button"
                    class="btn-small btn-price"
                    data-menu-action="products"
                    data-id="${categoria.id}"
                >
                    📦 Productos
                </button>

                <button
                    type="button"
                    class="btn-small ${categoria.activo ? "btn-danger-soft" : "btn-success-soft"}"
                    data-menu-action="toggle"
                    data-id="${categoria.id}"
                >
                    ${categoria.activo ? "Desactivar" : "Activar"}
                </button>

            </div>

        `;

        container.appendChild(card);

    });

}


// =====================================================
// ABRIR FORMULARIO DE CATEGORIA
// =====================================================

function abrirFormularioCategoriaMenu(categoria = null) {

    if (!state.menuConfigId) {

        showToast(
            "Primero selecciona un menú.",
            "warning"
        );

        return;

    }

    state.menuCategoriaActual = categoria;

    el("formCategoriaMenu").reset();

    el("menuCategoriaId").value =
        categoria?.id || "";

    el("menuCategoriaCodigo").value =
        categoria?.codigo || "";

    el("menuCategoriaNombre").value =
        categoria?.nombre || "";

    el("menuCategoriaDescripcion").value =
        categoria?.descripcion || "";

    el("menuCategoriaMin").value =
        categoria?.min_selecciones ??
        (categoria?.obligatorio ? 1 : 0);

    el("menuCategoriaMax").value =
        categoria?.max_selecciones ?? 1;

    el("menuCategoriaObligatoria").checked =
        categoria?.obligatorio ?? true;

    el("menuCategoriaRepetidos").checked =
        categoria?.permitir_repetidos ?? false;

    el("menuCategoriaOrden").value =
        categoria?.orden ?? (
            state.menuCategorias.length + 1
        );

    el("menuCategoriaActiva").checked =
        categoria?.activo ?? true;

    el("tituloCategoriaMenu").textContent =
        categoria
            ? "Editar categoría del menú"
            : "Nueva categoría del menú";

    el("btnGuardarCategoriaMenu").textContent =
        categoria
            ? "Actualizar categoría"
            : "Guardar categoría";

    closeModal("modalConfiguracionMenu");

    openModal("modalCategoriaMenu");

}


// =====================================================
// GUARDAR CATEGORIA
// =====================================================

async function guardarCategoriaMenu(event) {

    event.preventDefault();

    if (!state.menuConfigId) return;

    const id = el("menuCategoriaId").value;

    let minimo = Number(
        el("menuCategoriaMin").value
    );

    const maximo = Number(
        el("menuCategoriaMax").value
    );

    const obligatorio = el(
        "menuCategoriaObligatoria"
    ).checked;

    // Si la categoría es opcional, su mínimo es cero.
    if (!obligatorio) {

        minimo = 0;

        el("menuCategoriaMin").value = "0";

    }

    if (
        !Number.isInteger(minimo) ||
        !Number.isInteger(maximo) ||
        minimo < 0 ||
        maximo < 1 ||
        minimo > maximo
    ) {

        showToast(
            "Las cantidades mínimas y máximas no son válidas.",
            "warning"
        );

        return;

    }

    if (obligatorio && minimo < 1) {

        showToast(
            "Una categoría obligatoria necesita al menos una selección.",
            "warning"
        );

        return;

    }

    const data = {

        codigo: el("menuCategoriaCodigo").value.trim(),

        nombre: el("menuCategoriaNombre").value.trim(),

        descripcion: el("menuCategoriaDescripcion").value.trim(),

        obligatorio,

        min_selecciones: minimo,

        max_selecciones: maximo,

        permitir_repetidos:
            el("menuCategoriaRepetidos").checked,

        activo:
            el("menuCategoriaActiva").checked,

        orden: Number(
            el("menuCategoriaOrden").value
        ) || 0

    };

    const button = el("btnGuardarCategoriaMenu");

    button.disabled = true;

    try {

        const endpoint = id

            ? `/catalogo/items/${state.menuConfigId}/categorias-menu/${id}`

            : `/catalogo/items/${state.menuConfigId}/categorias-menu`;

        const method = id
            ? "PUT"
            : "POST";

        const response = await apiFetch(
            endpoint,
            method,
            data
        );

        validateSuccess(response);

        closeModal("modalCategoriaMenu");

        showToast(
            id
                ? "Categoría del menú actualizada."
                : "Categoría agregada al menú."
        );

        openModal("modalConfiguracionMenu");

        await cargarConfiguracionMenu();

    } catch (error) {

        console.error(
            "ERROR GUARDANDO CATEGORIA MENU:",
            error
        );

        showToast(
            error.message,
            "error"
        );

    } finally {

        button.disabled = false;

    }

}


// =====================================================
// ACCIONES DE CATEGORIAS DEL MENU
// =====================================================

async function ejecutarAccionCategoriaMenu(event) {

    const button = event.target.closest(
        "[data-menu-action]"
    );

    if (!button) return;

    const id = Number(
        button.dataset.id
    );

    const action = button.dataset.menuAction;

    const categoria = state.menuCategorias.find(
        item => Number(item.id) === id
    );

    if (!categoria) return;


    if (action === "edit") {

        abrirFormularioCategoriaMenu(categoria);

        return;

    }


    if (action === "products") {

        await abrirProductosCategoriaMenu(categoria);

        return;

    }


    if (action === "toggle") {

        const nuevoEstado = !categoria.activo;

        const confirmar = confirm(

            nuevoEstado

                ? `¿Deseas activar ${categoria.nombre}?`

                : `¿Deseas desactivar ${categoria.nombre}?`

        );

        if (!confirmar) return;

        try {

            const response = await apiFetch(

                `/catalogo/items/${state.menuConfigId}/categorias-menu/${id}/estado`,

                "PATCH",

                {
                    activo: nuevoEstado
                }

            );

            validateSuccess(response);

            showToast(
                "Estado de la categoría actualizado."
            );

            await cargarConfiguracionMenu();

        } catch (error) {

            showToast(
                error.message,
                "error"
            );

        }

    }

}


// =====================================================
// ABRIR SELECTOR DE PRODUCTOS
// =====================================================

async function abrirProductosCategoriaMenu(categoria) {

    state.menuCategoriaActual = categoria;

    state.productosCategoriaMenu = [];

    el("tituloProductosCategoriaMenu").textContent =
        `Productos: ${categoria.nombre}`;

    el("buscarProductosCategoriaMenu").value = "";

    setLoading(
        el("productosCategoriaMenuLista"),
        "Consultando recetas activas..."
    );

    closeModal("modalConfiguracionMenu");

    openModal("modalProductosCategoriaMenu");

    try {

        const response = await apiFetch(

            `/catalogo/menu-categorias/${categoria.id}/productos-disponibles`

        );

        const data = validateSuccess(response);

        state.productosCategoriaMenu = Array.isArray(data)
            ? data
            : [];

        renderProductosCategoriaMenu();

    } catch (error) {

        console.error(
            "ERROR CARGANDO PRODUCTOS DE CATEGORIA:",
            error
        );

        el("productosCategoriaMenuLista").innerHTML = `
            <div class="catalogo-error">
                ${escapeHTML(error.message)}
            </div>
        `;

        showToast(
            error.message,
            "error"
        );

    }

}


// =====================================================
// FILTRAR PRODUCTOS SIN PERDER SELECCIONES
// =====================================================

function filtrarProductosCategoriaMenu() {

    const search = el(
        "buscarProductosCategoriaMenu"
    ).value.trim().toLowerCase();

    document
        .querySelectorAll(".menu-producto-row")
        .forEach(row => {

            const name = row.dataset.search || "";

            row.classList.toggle(
                "hidden",
                !name.includes(search)
            );

        });

}


// =====================================================
// RENDERIZAR PRODUCTOS DISPONIBLES
// =====================================================

function renderProductosCategoriaMenu() {

    const container = el(
        "productosCategoriaMenuLista"
    );

    const empty = el(
        "productosCategoriaMenuEmpty"
    );

    container.innerHTML = "";

    empty.classList.toggle(
        "hidden",
        state.productosCategoriaMenu.length > 0
    );

    state.productosCategoriaMenu.forEach(producto => {

        const asignado = Boolean(
            producto.asignado
        );

        const relacionActiva = Boolean(
            producto.relacion_activa
        );

        const seleccionado = (
            asignado && relacionActiva
        );

        const imageUrl = String(
            producto.imagen_url || ""
        ).trim();

        const image = /^https?:\/\//i.test(imageUrl)
            ? `
                <img
                    src="${escapeHTML(imageUrl)}"
                    alt=""
                    loading="lazy"
                >
            `
            : `
                <div class="menu-producto-placeholder">
                    🍽️
                </div>
            `;

        const row = document.createElement("article");

        row.className = "menu-producto-row";

        row.dataset.productId = producto.id;

        row.dataset.search = (
            `${producto.nombre || ""} ${producto.codigo || ""}`
        ).toLowerCase();

        row.innerHTML = `

            <div class="menu-producto-check">

                <input
                    type="checkbox"
                    class="menu-producto-seleccionado"
                    ${seleccionado ? "checked" : ""}
                    aria-label="Incluir producto"
                >

            </div>


            <div class="menu-producto-imagen">
                ${image}
            </div>


            <div class="menu-producto-info">

                <strong>
                    ${escapeHTML(producto.nombre)}
                </strong>

                <span>
                    ${escapeHTML(producto.codigo || "")}
                </span>

                <small>
                    ${escapeHTML(producto.producto_categoria || "Sin categoría")}
                </small>

            </div>


            <div class="menu-producto-config">

                <label>
                    Recargo adicional
                    <input
                        type="number"
                        class="menu-producto-recargo"
                        min="0"
                        step="0.01"
                        value="${Number(producto.precio_adicional || 0)}"
                    >
                </label>

                <label>
                    <input
                        type="checkbox"
                        class="menu-producto-predeterminado"
                        ${producto.predeterminado ? "checked" : ""}
                        ${seleccionado ? "" : "disabled"}
                    >
                    Predeterminado
                </label>

                <label>
                    Orden
                    <input
                        type="number"
                        class="menu-producto-orden"
                        min="0"
                        value="${Number(producto.orden || 0)}"
                    >
                </label>

            </div>

        `;

        const checkbox = row.querySelector(
            ".menu-producto-seleccionado"
        );

        const defaultCheckbox = row.querySelector(
            ".menu-producto-predeterminado"
        );

        checkbox.addEventListener(
            "change",
            () => {

                defaultCheckbox.disabled = !checkbox.checked;

                if (!checkbox.checked) {

                    defaultCheckbox.checked = false;

                }

            }
        );

        container.appendChild(row);

    });

}


// =====================================================
// GUARDAR PRODUCTOS ASOCIADOS
// =====================================================

async function guardarProductosCategoriaMenu() {

    const categoria = state.menuCategoriaActual;

    if (!categoria) return;

    const rows = document.querySelectorAll(
        ".menu-producto-row"
    );

    const productos = [];

    for (const row of rows) {

        const seleccionado = row.querySelector(
            ".menu-producto-seleccionado"
        ).checked;

        if (!seleccionado) continue;

        const recargo = Number(
            row.querySelector(".menu-producto-recargo").value
        );

        const orden = Number(
            row.querySelector(".menu-producto-orden").value
        );

        const predeterminado = row.querySelector(
            ".menu-producto-predeterminado"
        ).checked;

        if (
            !Number.isFinite(recargo) ||
            recargo < 0
        ) {

            showToast(
                "Hay un recargo inválido en los productos seleccionados.",
                "warning"
            );

            return;

        }

        if (
            !Number.isInteger(orden) ||
            orden < 0
        ) {

            showToast(
                "El orden de los productos debe ser un entero igual o mayor a cero.",
                "warning"
            );

            return;

        }

        productos.push({

            producto_id: Number(row.dataset.productId),

            precio_adicional: recargo,

            predeterminado,

            activo: true,

            orden

        });

    }

    if (
        categoria.obligatorio &&
        categoria.min_selecciones > productos.length
    ) {
        showToast(

            `Esta categoría necesita al menos ${categoria.min_selecciones} producto(s) seleccionado(s).`,

            "warning"

        );

        return;

    }

    const defaults = productos.filter(
        producto => producto.predeterminado
    ).length;

    if (defaults > categoria.max_selecciones) {

        showToast(

            "La cantidad de productos predeterminados supera el máximo permitido.",

            "warning"

        );

        return;

    }

    const button = el(
        "btnGuardarProductosCategoriaMenu"
    );

    button.disabled = true;

    try {

        const response = await apiFetch(

            `/catalogo/menu-categorias/${categoria.id}/productos`,

            "PUT",

            {
                productos
            }

        );

        validateSuccess(response);

        showToast(
            "Productos y recargos guardados correctamente."
        );

        closeModal("modalProductosCategoriaMenu");

        openModal("modalConfiguracionMenu");

        await cargarConfiguracionMenu();

    } catch (error) {

        console.error(
            "ERROR GUARDANDO PRODUCTOS CATEGORIA:",
            error
        );

        showToast(
            error.message,
            "error"
        );

    } finally {

        button.disabled = false;

    }

}

