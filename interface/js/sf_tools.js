import { app } from "../../scripts/app.js";
import { api } from "../../scripts/api.js";

app.registerExtension({
    name: "StudioFury.Tools",

    async setup() {
        console.log("🧩 [StudioFury] Iniciando extensión de herramientas...");

        const callApi = async (endpoint, confirmMsg) => {
            if (!confirm(confirmMsg)) return;
            try {
                await api.fetchApi("/studiofury/system/" + endpoint, { method: "POST" });
            } catch (e) {
                alert("Error conectando con Studio Fury: " + e);
            }
        };

        const MAX_ATTEMPTS = 15;
        let attempts = 0;

        const addMenuItems = () => {
            attempts++;

            // Abortar si se supera el límite — evita el timer infinito en ComfyUI 2.0
            // donde la API del menú cambió y app.ui.menu nunca existe
            if (attempts > MAX_ATTEMPTS) {
                console.warn(
                    `⚠️ [StudioFury] No se pudo añadir el menú tras ${MAX_ATTEMPTS} intentos. ` +
                    "Es posible que esta versión de ComfyUI use una API de menú diferente. " +
                    "Los endpoints de sistema siguen disponibles en /studiofury/system/restart y /shutdown."
                );
                return;
            }

            // API legacy (ComfyUI pre-2.0)
            if (app.ui?.menu?.addMenuItem) {
                app.ui.menu.addMenuItem({
                    name:     "SF-Restart",
                    label:    "🔄 SF: Reiniciar Servidor",
                    callback: () => callApi(
                        "restart",
                        "⚠️ ¿Reiniciar ComfyUI?\nLa conexión se perderá unos segundos."
                    ),
                });
                app.ui.menu.addMenuItem({
                    name:     "SF-Shutdown",
                    label:    "🛑 SF: Apagar Servidor",
                    callback: () => callApi(
                        "shutdown",
                        "🛑 ¿Apagar ComfyUI completamente?\nTendrás que abrir la consola manualmente."
                    ),
                });
                console.log(`✅ [StudioFury] Botones de menú añadidos (intento ${attempts}).`);
                return;
            }

            // API ComfyUI 2.0 — usa el sistema de comandos registrados
            if (app.registerCommand) {
                app.registerCommand("StudioFury.Restart", {
                    label:    "🔄 SF: Reiniciar Servidor",
                    function: () => callApi(
                        "restart",
                        "⚠️ ¿Reiniciar ComfyUI?\nLa conexión se perderá unos segundos."
                    ),
                });
                app.registerCommand("StudioFury.Shutdown", {
                    label:    "🛑 SF: Apagar Servidor",
                    function: () => callApi(
                        "shutdown",
                        "🛑 ¿Apagar ComfyUI completamente?\nTendrás que abrir la consola manualmente."
                    ),
                });
                console.log(`✅ [StudioFury] Comandos registrados en ComfyUI 2.0 (intento ${attempts}).`);
                return;
            }

            // Ninguna API disponible aún — reintentar en 1s
            console.log(`⏳ [StudioFury] Menú no disponible, reintentando... (${attempts}/${MAX_ATTEMPTS})`);
            setTimeout(addMenuItems, 1000);
        };

        addMenuItems();
    },
});
