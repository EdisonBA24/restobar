/**
 * ============================================================
 * TABLA UI
 * ============================================================
 * Componente reutilizable para todos los listados del ERP.
 *
 * Responsabilidades:
 *  - Paginación
 *  - Ordenamiento
 *  - Page Size
 *  - Persistencia
 *  - Indicadores visuales
 *
 * No contiene lógica de negocio.
 * ============================================================
 */

export class TablaUI {

    constructor(config = {}) {

        // Configuración general
        this.nombre = config.nombre ?? "";

        this.callback = config.callback ?? null;

        // Selectores HTML
        this.selectores = {

            tabla: config.tabla ?? null,

            pageSize: config.pageSize ?? null,

            btnAnterior: config.btnAnterior ?? null,

            btnSiguiente: config.btnSiguiente ?? null,

            numeros: config.numeros ?? null,

            resumen: config.resumen ?? null,

            info: config.info ?? null

        };

    }

}