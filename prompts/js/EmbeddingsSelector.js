import { app } from "/scripts/app.js";

app.registerExtension({
    name: "StudioFury.EmbeddingsSelector", // Nombre único
    async beforeRegisterNodeDef(nodeType, nodeData, app) {
        if (nodeData.name === "StudioFury_EmbeddingsSelector") {

            const onNodeCreated = nodeType.prototype.onNodeCreated;
            nodeType.prototype.onNodeCreated = function() {
                const r = onNodeCreated ? onNodeCreated.apply(this, arguments) : undefined;

                this.emb_list = [];
                this.selection = {};
                this.setSize([350, 400]);

                // Lógica de ocultar widgets y leer datos
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

            // Dibujado (igual que antes)
            nodeType.prototype.onDrawForeground = function(ctx) {
                if (this.flags.collapsed) return;
                ctx.save();
                ctx.font = "12px Arial";
                ctx.fillStyle = "#fff";

                let y = 40;
                ctx.fillText("Embedding File", 10, y);
                ctx.fillText("POS", 240, y);
                ctx.fillText("NEG", 290, y);

                y += 20;
                if(this.emb_list) {
                    for(let i=0; i<this.emb_list.length; i++) {
                        const name = this.emb_list[i];

                        ctx.fillStyle = "#ccc";
                        ctx.fillText(name.substring(0,25), 10, y);

                        // Pos
                        let isPos = (this.selection[name] === 'P');
                        ctx.fillStyle = isPos ? "#0f0" : "#333";
                        ctx.fillRect(240, y-10, 15, 15);
                        ctx.strokeStyle = "#fff"; ctx.strokeRect(240, y-10, 15, 15);

                        // Neg
                        let isNeg = (this.selection[name] === 'N');
                        ctx.fillStyle = isNeg ? "#f00" : "#333";
                        ctx.fillRect(290, y-10, 15, 15);
                        ctx.strokeStyle = "#fff"; ctx.strokeRect(290, y-10, 15, 15);

                        y += 22;
                    }
                }
                ctx.restore();
            };

            // Clicks (igual que antes)
            nodeType.prototype.onMouseDown = function(e, pos) {
                const x = pos[0];
                const y = pos[1];
                const startY = 60;
                const rowH = 22;

                if (y < startY) return;

                const index = Math.floor((y - startY) / rowH);
                if (this.emb_list && index >= 0 && index < this.emb_list.length) {
                    const name = this.emb_list[index];

                    if (x > 240 && x < 260) {
                        this.selection[name] = (this.selection[name] === 'P') ? null : 'P';
                    }
                    else if (x > 290 && x < 310) {
                        this.selection[name] = (this.selection[name] === 'N') ? null : 'N';
                    }

                    let out = [];
                    for(let k in this.selection) {
                        if(this.selection[k]) out.push(this.selection[k] + ":" + k);
                    }

                    const w = this.widgets.find(w => w.name === "selected_data");
                    if(w) w.value = out.join("|");

                    return true;
                }
            };
        }
    }
});