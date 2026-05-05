import { app } from "/scripts/app.js";

// ============================================================
//  StudioFury — EmbeddingsSelector  (Legacy + ComfyUI 2.0)
//  Detecta la versión del frontend y usa el sistema correcto.
// ============================================================

const IS_COMFY_V2 = !!window.__COMFYUI_FRONTEND_VERSION__
    || !!document.querySelector?.("#comfy-vue-app, #comfy-app")
    || typeof globalThis.useToastStore !== "undefined";

// ── Parámetros visuales compartidos ─────────────────────────
const ROW_HEIGHT      = 24;
const MAX_VISIBLE     = 10;
const HEADER_HEIGHT   = 70;
const SCROLLBAR_W     = 16;
const NODE_WIDTH      = 370;

// ============================================================
//  HELPERS comunes
// ============================================================
function buildOutputText(selection) {
    return Object.entries(selection)
        .filter(([, v]) => v)
        .map(([k, v]) => v + ":" + k)
        .join("|");
}

// ============================================================
//  RUTA A  —  Legacy canvas renderer (pre-2.0)
// ============================================================
function registerLegacy(nodeType) {
    const _onCreated = nodeType.prototype.onNodeCreated;

    nodeType.prototype.onNodeCreated = function () {
        const r = _onCreated?.apply(this, arguments);

        this._sf_list      = [];
        this._sf_sel       = {};
        this._sf_scroll    = 0;

        const fixedH = HEADER_HEIGHT + MAX_VISIBLE * ROW_HEIGHT + 20;
        this.setSize([NODE_WIDTH, fixedH]);

        // Ocultar widgets nativos y capturar la lista de embeddings
        if (this.widgets) {
            for (const w of this.widgets) {
                if (w.name === "selected_data")      { w.hidden = true; }
                if (w.name === "embedding_list_raw") {
                    // La lista viene como w.options.values o w.type (combo)
                    const vals = w.options?.values ?? (Array.isArray(w.value) ? w.value : null);
                    if (vals) this._sf_list = [...vals];
                    w.hidden = true;
                }
            }
        }

        // ── Scroll con rueda ─────────────────────────────────
        // LiteGraph llama onMouseWheel SOLO si el nodo lo implementa
        // y el canvas ya no consume el evento primero.
        // Para garantizarlo añadimos también un listener DOM directo.
        this._sf_wheelHandler = (e) => {
            if (!this._sf_hovered) return;
            const maxOff = Math.max(0, this._sf_list.length - MAX_VISIBLE);
            this._sf_scroll = Math.max(0, Math.min(maxOff,
                this._sf_scroll + (e.deltaY > 0 ? 1 : -1)));
            this.setDirtyCanvas(true, true);
            e.preventDefault();
            e.stopPropagation();
        };
        // Buscamos el canvas del editor para adjuntar el handler
        const canvas = document.getElementById("graph-canvas")
            ?? document.querySelector("canvas.litegraph");
        if (canvas) {
            canvas.addEventListener("wheel", this._sf_wheelHandler, { passive: false });
        }

        // ── Hover tracking ───────────────────────────────────
        this.onMouseEnter = () => { this._sf_hovered = true; };
        this.onMouseLeave = () => { this._sf_hovered = false; };

        return r;
    };

    // Limpieza al eliminar el nodo
    const _onRemoved = nodeType.prototype.onRemoved;
    nodeType.prototype.onRemoved = function () {
        if (this._sf_wheelHandler) {
            const canvas = document.getElementById("graph-canvas")
                ?? document.querySelector("canvas.litegraph");
            canvas?.removeEventListener("wheel", this._sf_wheelHandler);
        }
        _onRemoved?.apply(this, arguments);
    };

    // ── Bloqueo de tamaño ────────────────────────────────────
    nodeType.prototype.onResize = function (size) {
        size[0] = NODE_WIDTH;
        size[1] = HEADER_HEIGHT + MAX_VISIBLE * ROW_HEIGHT + 20;
    };

    // ── Dibujado ─────────────────────────────────────────────
    nodeType.prototype.onDrawForeground = function (ctx) {
        if (this.flags?.collapsed) return;

        ctx.save();
        ctx.font = "12px Arial, sans-serif";

        // Cabecera
        const headerY = 50;
        ctx.fillStyle = "#aaa";
        ctx.fillText("Embedding", 10, headerY);
        ctx.fillText("POS", 265, headerY);
        ctx.fillText("NEG", 310, headerY);

        ctx.strokeStyle = "#444";
        ctx.beginPath();
        ctx.moveTo(10, headerY + 8);
        ctx.lineTo(this.size[0] - 20, headerY + 8);
        ctx.stroke();

        const startY = HEADER_HEIGHT;
        const list   = this._sf_list ?? [];
        const sel    = this._sf_sel  ?? {};
        const scroll = this._sf_scroll ?? 0;

        if (list.length === 0) {
            ctx.fillStyle = "#666";
            ctx.fillText("No embeddings found", 10, startY + 16);
            ctx.restore();
            return;
        }

        const visible = list.slice(scroll, scroll + MAX_VISIBLE);

        for (let i = 0; i < visible.length; i++) {
            const name = visible[i];
            const rowY = startY + i * ROW_HEIGHT + ROW_HEIGHT / 2;

            // Fila alternada
            if (i % 2 === 0) {
                ctx.fillStyle = "rgba(255,255,255,0.03)";
                ctx.fillRect(6, startY + i * ROW_HEIGHT, this.size[0] - 12, ROW_HEIGHT);
            }

            // Nombre (truncado)
            ctx.fillStyle = "#ccc";
            let label = name.replace(/\.(pt|bin|safetensors)$/i, "");
            if (label.length > 30) label = label.slice(0, 27) + "…";
            ctx.fillText(label, 10, rowY + 1);

            // Checkbox POS
            const isPos = sel[name] === "P";
            ctx.fillStyle = isPos ? "#22c55e" : "#1e1e1e";
            ctx.beginPath();
            ctx.roundRect(260, rowY - 8, 16, 16, 3);
            ctx.fill();
            ctx.strokeStyle = isPos ? "#16a34a" : "#555";
            ctx.lineWidth = 1;
            ctx.stroke();
            if (isPos) {
                ctx.strokeStyle = "#fff";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(263, rowY); ctx.lineTo(266, rowY + 4); ctx.lineTo(273, rowY - 4);
                ctx.stroke();
            }

            // Checkbox NEG
            const isNeg = sel[name] === "N";
            ctx.fillStyle = isNeg ? "#ef4444" : "#1e1e1e";
            ctx.beginPath();
            ctx.roundRect(310, rowY - 8, 16, 16, 3);
            ctx.fill();
            ctx.strokeStyle = isNeg ? "#dc2626" : "#555";
            ctx.lineWidth = 1;
            ctx.stroke();
            if (isNeg) {
                ctx.strokeStyle = "#fff";
                ctx.lineWidth = 1.5;
                ctx.beginPath();
                ctx.moveTo(313, rowY); ctx.lineTo(316, rowY + 4); ctx.lineTo(323, rowY - 4);
                ctx.stroke();
            }
        }

        // ── Scrollbar ─────────────────────────────────────────
        if (list.length > MAX_VISIBLE) {
            const trackH  = MAX_VISIBLE * ROW_HEIGHT;
            const sbX     = this.size[0] - SCROLLBAR_W - 4;
            const maxOff  = list.length - MAX_VISIBLE;

            // Track
            ctx.fillStyle = "#111";
            ctx.beginPath();
            ctx.roundRect(sbX, startY, SCROLLBAR_W, trackH, 4);
            ctx.fill();

            // Thumb
            const ratio   = MAX_VISIBLE / list.length;
            const thumbH  = Math.max(20, trackH * ratio);
            const thumbY  = startY + (scroll / maxOff) * (trackH - thumbH);
            ctx.fillStyle = "#555";
            ctx.beginPath();
            ctx.roundRect(sbX + 2, thumbY + 2, SCROLLBAR_W - 4, thumbH - 4, 4);
            ctx.fill();

            // Flechas
            const arrowX = sbX + SCROLLBAR_W / 2;
            ctx.fillStyle = "#888";

            // ▲ arriba
            ctx.beginPath();
            ctx.moveTo(arrowX, startY + 4);
            ctx.lineTo(arrowX - 5, startY + 12);
            ctx.lineTo(arrowX + 5, startY + 12);
            ctx.closePath(); ctx.fill();

            // ▼ abajo
            const botY = startY + trackH;
            ctx.beginPath();
            ctx.moveTo(arrowX, botY - 4);
            ctx.lineTo(arrowX - 5, botY - 12);
            ctx.lineTo(arrowX + 5, botY - 12);
            ctx.closePath(); ctx.fill();
        }

        // Contador inferior
        ctx.fillStyle = "#555";
        ctx.font = "10px Arial, sans-serif";
        const total = list.length;
        const showing = Math.min(MAX_VISIBLE, total - scroll);
        ctx.fillText(`${scroll + 1}–${scroll + showing} of ${total}`, 10,
            startY + MAX_VISIBLE * ROW_HEIGHT + 14);

        ctx.restore();
    };

    // ── Clics ────────────────────────────────────────────────
    nodeType.prototype.onMouseDown = function (e, pos) {
        const [mx, my] = pos;
        const list   = this._sf_list ?? [];
        const sel    = this._sf_sel  ?? {};
        const scroll = this._sf_scroll ?? 0;
        const startY = HEADER_HEIGHT - ROW_HEIGHT * 0.5;
        const listH  = MAX_VISIBLE * ROW_HEIGHT;
        const sbX    = this.size[0] - SCROLLBAR_W - 4;
        const maxOff = Math.max(0, list.length - MAX_VISIBLE);

        // ── Flechas de scroll ──
        if (mx > sbX) {
            const trackBot = HEADER_HEIGHT + MAX_VISIBLE * ROW_HEIGHT;
            if (my > HEADER_HEIGHT && my < HEADER_HEIGHT + 14) {
                this._sf_scroll = Math.max(0, scroll - 1);
                this.setDirtyCanvas(true, true); return true;
            }
            if (my > trackBot - 14 && my < trackBot + 4) {
                this._sf_scroll = Math.min(maxOff, scroll + 1);
                this.setDirtyCanvas(true, true); return true;
            }
            // Clic en la track → saltar a posición proporcional
            const trackH = MAX_VISIBLE * ROW_HEIGHT;
            const rel = (my - HEADER_HEIGHT) / trackH;
            this._sf_scroll = Math.round(rel * maxOff);
            this._sf_scroll = Math.max(0, Math.min(maxOff, this._sf_scroll));
            this.setDirtyCanvas(true, true); return true;
        }

        // ── Checkboxes ──
        if (my > startY && my < startY + listH) {
            const rowIdx = Math.floor((my - startY) / ROW_HEIGHT);
            const realIdx = scroll + rowIdx;
            if (realIdx >= 0 && realIdx < list.length) {
                const name = list[realIdx];
                if (mx >= 260 && mx <= 280) {
                    this._sf_sel[name] = sel[name] === "P" ? null : "P";
                    this._updateOutput();
                    this.setDirtyCanvas(true, true); return true;
                }
                if (mx >= 310 && mx <= 330) {
                    this._sf_sel[name] = sel[name] === "N" ? null : "N";
                    this._updateOutput();
                    this.setDirtyCanvas(true, true); return true;
                }
            }
        }
    };

    nodeType.prototype._updateOutput = function () {
        const w = this.widgets?.find(w => w.name === "selected_data");
        if (w) w.value = buildOutputText(this._sf_sel);
    };

    // onMouseWheel de LiteGraph (fallback, por si el DOM listener no funciona)
    nodeType.prototype.onMouseWheel = function (e) {
        const maxOff = Math.max(0, (this._sf_list?.length ?? 0) - MAX_VISIBLE);
        this._sf_scroll = Math.max(0, Math.min(maxOff,
            (this._sf_scroll ?? 0) + (e.deltaY > 0 ? 1 : -1)));
        this.setDirtyCanvas(true, true);
        return true; // consume el evento
    };
}

// ============================================================
//  RUTA B  —  ComfyUI 2.0  (DOM widget + addDOMWidget)
// ============================================================
function registerV2(nodeType) {
    const _onCreated = nodeType.prototype.onNodeCreated;

    nodeType.prototype.onNodeCreated = function () {
        const r = _onCreated?.apply(this, arguments);

        // Extraemos la lista de embeddings del widget nativo antes de ocultarlo
        let embList = [];
        if (this.widgets) {
            for (const w of this.widgets) {
                if (w.name === "embedding_list_raw") {
                    const vals = w.options?.values ?? [];
                    embList = [...vals];
                    w.hidden = true;
                }
                if (w.name === "selected_data") { w.hidden = true; }
            }
        }

        // ── Construir el widget DOM ──────────────────────────
        const container = document.createElement("div");
        container.style.cssText = `
            width: 100%;
            max-height: ${MAX_VISIBLE * 28 + 40}px;
            overflow-y: auto;
            font-size: 12px;
            font-family: Arial, sans-serif;
            box-sizing: border-box;
            padding: 4px 0;
        `;

        // Cabecera
        const header = document.createElement("div");
        header.style.cssText = `
            display: grid;
            grid-template-columns: 1fr 44px 44px;
            padding: 4px 8px;
            border-bottom: 1px solid rgba(255,255,255,0.1);
            font-weight: 600;
            color: #999;
            position: sticky;
            top: 0;
            background: rgba(30,30,30,0.95);
            z-index: 1;
        `;
        header.innerHTML = `
            <span>Embedding</span>
            <span style="text-align:center;color:#22c55e">POS</span>
            <span style="text-align:center;color:#ef4444">NEG</span>
        `;
        container.appendChild(header);

        // Lista de filas
        const selection = {};
        const node = this;

        function updateOutput() {
            const w = node.widgets?.find(w => w.name === "selected_data");
            if (w) w.value = buildOutputText(selection);
        }

        function makeRow(name, idx) {
            const row = document.createElement("div");
            row.style.cssText = `
                display: grid;
                grid-template-columns: 1fr 44px 44px;
                align-items: center;
                padding: 3px 8px;
                border-radius: 4px;
                background: ${idx % 2 === 0 ? "rgba(255,255,255,0.02)" : "transparent"};
                transition: background 0.1s;
            `;
            row.addEventListener("mouseenter", () => {
                row.style.background = "rgba(255,255,255,0.06)";
            });
            row.addEventListener("mouseleave", () => {
                row.style.background = idx % 2 === 0
                    ? "rgba(255,255,255,0.02)" : "transparent";
            });

            // Nombre
            const label = document.createElement("span");
            let display = name.replace(/\.(pt|bin|safetensors)$/i, "");
            if (display.length > 30) display = display.slice(0, 27) + "…";
            label.title = name;
            label.textContent = display;
            label.style.cssText = "color:#ccc; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;";

            // Botón POS
            const btnPos = document.createElement("button");
            btnPos.textContent = "P";
            styleBtn(btnPos, false, "pos");
            btnPos.addEventListener("click", (e) => {
                e.stopPropagation();
                selection[name] = selection[name] === "P" ? null : "P";
                styleBtn(btnPos, selection[name] === "P", "pos");
                styleBtn(btnNeg, false, "neg");
                updateOutput();
            });

            // Botón NEG
            const btnNeg = document.createElement("button");
            btnNeg.textContent = "N";
            styleBtn(btnNeg, false, "neg");
            btnNeg.addEventListener("click", (e) => {
                e.stopPropagation();
                selection[name] = selection[name] === "N" ? null : "N";
                styleBtn(btnNeg, selection[name] === "N", "neg");
                styleBtn(btnPos, false, "pos");
                updateOutput();
            });

            row.appendChild(label);
            row.appendChild(btnPos);
            row.appendChild(btnNeg);
            return { row, btnPos, btnNeg };
        }

        if (embList.length === 0) {
            const empty = document.createElement("div");
            empty.style.cssText = "color:#555; padding:8px; font-size:11px;";
            empty.textContent = "No embeddings found";
            container.appendChild(empty);
        } else {
            embList.forEach((name, i) => {
                const { row } = makeRow(name, i);
                container.appendChild(row);
            });
        }

        // Prevenir que el scroll del widget llegue al canvas
        container.addEventListener("wheel", (e) => { e.stopPropagation(); }, { passive: true });

        // Registrar como DOM widget
        this.addDOMWidget("sf_embeddings_ui", "div", container, {
            getValue: () => buildOutputText(selection),
            setValue: (v) => {
                // Si se restaura un estado guardado, sincronizar
                if (!v) return;
                v.split("|").forEach(item => {
                    if (item.startsWith("P:")) selection[item.slice(2)] = "P";
                    else if (item.startsWith("N:")) selection[item.slice(2)] = "N";
                });
            }
        });

        return r;
    };
}

// ── Estilo de botones para modo V2 ───────────────────────────
function styleBtn(btn, active, type) {
    const activeColor = type === "pos" ? "#22c55e" : "#ef4444";
    const activeBorder = type === "pos" ? "#16a34a" : "#dc2626";
    btn.style.cssText = `
        width: 28px; height: 22px;
        border-radius: 4px;
        border: 1px solid ${active ? activeBorder : "#444"};
        background: ${active ? activeColor : "#1e1e1e"};
        color: ${active ? "#fff" : "#666"};
        font-size: 11px; font-weight: 600;
        cursor: pointer;
        margin: 0 auto;
        display: block;
        transition: background 0.15s, border-color 0.15s;
    `;
}

// ============================================================
//  REGISTRO DE LA EXTENSIÓN
// ============================================================
app.registerExtension({
    name: "StudioFury.EmbeddingsSelector",

    async beforeRegisterNodeDef(nodeType, nodeData) {
        if (nodeData.name !== "StudioFury_EmbeddingsSelector") return;

        console.log(`🧩 [StudioFury] EmbeddingsSelector → modo: ${IS_COMFY_V2 ? "ComfyUI 2.0" : "Legacy"}`);

        if (IS_COMFY_V2) {
            registerV2(nodeType);
        } else {
            registerLegacy(nodeType);
        }
    }
});
