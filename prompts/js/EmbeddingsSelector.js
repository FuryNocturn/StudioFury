import { app } from "/scripts/app.js";

app.registerExtension({
    name: "StudioFury.EmbeddingsSelector",
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "StudioFury_EmbeddingsSelector") {

            // CONFIGURACIÓN VISUAL
            const ROW_HEIGHT = 25;
            const MAX_VISIBLE_ROWS = 5;
            const HEADER_HEIGHT = 80;
            const SCROLLBAR_WIDTH = 10;

            const onNodeCreated = nodeType.prototype.onNodeCreated;

            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                this.emb_list = [];
                this.selection = {};
                this.scroll_offset = 0;

                // Calculamos tamaño fijo
                const fixedHeight = HEADER_HEIGHT + (MAX_VISIBLE_ROWS * ROW_HEIGHT) + 10;
                this.setSize([350, fixedHeight]);

                if (this.widgets) {
                    for (const w of this.widgets) {
                        if (w.name === "embedding_list_raw") {
                            if (w.options && w.options.values) this.emb_list = w.options.values;
                            w.hidden = true;
                        }
                        if (w.name === "selected_data") w.hidden = true;
                    }
                }
                return r;
            };

            // 1. EVENTO SCROLL (CORREGIDO)
            nodeType.prototype.onMouseWheel = function(e) {
                // Verificar que el ratón está sobre el área de la lista para no bloquear scroll en cabecera
                // Aunque en nodos pequeños es mejor capturarlo todo.

                if (!this.emb_list || this.emb_list.length <= MAX_VISIBLE_ROWS) return;

                const delta = e.deltaY > 0 ? 1 : -1;
                this.scroll_offset += delta;

                // Clamping (Límites)
                const max_offset = this.emb_list.length - MAX_VISIBLE_ROWS;
                if (this.scroll_offset < 0) this.scroll_offset = 0;
                if (this.scroll_offset > max_offset) this.scroll_offset = max_offset;

                this.setDirtyCanvas(true, true);

                // ¡ESTA LÍNEA ES LA CLAVE!
                // Indica a ComfyUI que hemos consumido el evento y que no debe hacer zoom.
                return true;
            };

            // 2. BLOQUEO DE TAMAÑO
            nodeType.prototype.onResize = function(size) {
                const minHeight = HEADER_HEIGHT + (MAX_VISIBLE_ROWS * ROW_HEIGHT) + 10;
                // Forzamos el tamaño exacto para que no se vea feo
                size[0] = 350;
                size[1] = minHeight;
            };

            // 3. DIBUJADO
            nodeType.prototype.onDrawForeground = function(ctx) {
                if (this.flags.collapsed) return;

                ctx.save();
                ctx.font = "12px Arial";

                let y_header = 60;
                ctx.fillStyle = "#aaa";
                ctx.fillText("Embedding File", 10, y_header);
                ctx.fillText("POS", 240, y_header);
                ctx.fillText("NEG", 290, y_header);

                ctx.strokeStyle = "#444";
                ctx.beginPath();
                ctx.moveTo(10, y_header + 8);
                ctx.lineTo(this.size[0] - 20, y_header + 8);
                ctx.stroke();

                const start_y = HEADER_HEIGHT;

                if (this.emb_list && this.emb_list.length > 0) {
                    const visible_items = this.emb_list.slice(this.scroll_offset, this.scroll_offset + MAX_VISIBLE_ROWS);

                    for (let i = 0; i < visible_items.length; i++) {
                        const name = visible_items[i];
                        const row_y = start_y + (i * ROW_HEIGHT);

                        ctx.fillStyle = "#ccc";
                        let displayName = name;
                        if(displayName.length > 25) displayName = displayName.substring(0, 22) + "...";
                        ctx.fillText(displayName, 10, row_y);

                        // POS
                        const isPos = (this.selection[name] === 'P');
                        ctx.fillStyle = isPos ? "#0f0" : "#222";
                        ctx.fillRect(240, row_y - 10, 14, 14);
                        ctx.strokeStyle = "#888"; ctx.strokeRect(240, row_y - 10, 14, 14);

                        // NEG
                        const isNeg = (this.selection[name] === 'N');
                        ctx.fillStyle = isNeg ? "#f00" : "#222";
                        ctx.fillRect(290, row_y - 10, 14, 14);
                        ctx.strokeStyle = "#888"; ctx.strokeRect(290, row_y - 10, 14, 14);
                    }

                    // BARRA SCROLL
                    if (this.emb_list.length > MAX_VISIBLE_ROWS) {
                        const total_height = MAX_VISIBLE_ROWS * ROW_HEIGHT;
                        const scroll_x = this.size[0] - SCROLLBAR_WIDTH - 5;

                        ctx.fillStyle = "#111";
                        ctx.fillRect(scroll_x, start_y - 15, SCROLLBAR_WIDTH, total_height);

                        const ratio = MAX_VISIBLE_ROWS / this.emb_list.length;
                        const thumb_height = total_height * ratio;
                        const thumb_y = start_y - 15 + (this.scroll_offset / this.emb_list.length) * total_height;

                        ctx.fillStyle = "#666";
                        // Bordes redondeados simple
                        ctx.roundRect(scroll_x, thumb_y, SCROLLBAR_WIDTH, thumb_height, 2);
                        ctx.fill();
                    }
                } else {
                    ctx.fillStyle = "#666";
                    ctx.fillText("No embeddings found", 10, start_y);
                }
                ctx.restore();
            };

            // 4. CLICS
            nodeType.prototype.onMouseDown = function(e, pos) {
                const x = pos[0];
                const y = pos[1];

                const start_y = HEADER_HEIGHT - 15;
                const list_height = MAX_VISIBLE_ROWS * ROW_HEIGHT;

                // Si estamos en la zona de la lista
                if (y > start_y && y < start_y + list_height) {
                    const visual_row_index = Math.floor((y - start_y) / ROW_HEIGHT);
                    const real_index = this.scroll_offset + visual_row_index;

                    if (this.emb_list && real_index >= 0 && real_index < this.emb_list.length) {
                        const name = this.emb_list[real_index];

                        if (x > 240 && x < 260) {
                            this.selection[name] = (this.selection[name] === 'P') ? null : 'P';
                            this.updateOutput();
                            return true;
                        }
                        else if (x > 290 && x < 310) {
                            this.selection[name] = (this.selection[name] === 'N') ? null : 'N';
                            this.updateOutput();
                            return true;
                        }
                    }
                }
                // (Opcional: aquí se podría añadir lógica para clic en la barra de scroll,
                // pero la rueda suele ser suficiente para listas cortas).
            };

            nodeType.prototype.updateOutput = function() {
                let out = [];
                for(let k in this.selection) {
                    if(this.selection[k]) out.push(this.selection[k] + ":" + k);
                }
                const w = this.widgets.find(w => w.name === "selected_data");
                if(w) w.value = out.join("|");
            };
        }
    }
});