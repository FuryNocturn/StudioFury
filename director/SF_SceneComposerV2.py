import torch
import torch.nn.functional as F

class SF_SceneComposer:
    @classmethod
    def INPUT_TYPES(cls):
        # Añadimos "previous_composition" para permitir el encadenamiento de múltiples personajes
        bg_roles = ["scene_background", "previous_composition", "character_main", "character_secondary", "element_overlay"]
        fg_roles = ["character_main", "character_secondary", "element_overlay"]

        return {
            "required": {
                "fury_bus": ("SF_LINK",),
                "bg_role": (bg_roles, {"default": "scene_background"}),
                "fg_role": (fg_roles, {"default": "character_main"}),
                "x_offset": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "y_offset": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0, "step": 0.05}),
                "opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
            },
            "optional": {
                "optional_fg_mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("SF_LINK", "IMAGE", "MASK")
    RETURN_NAMES = ("bus", "composed_image", "accumulated_mask")
    FUNCTION = "compose"
    CATEGORY = "🧩 Studio Fury/🎬 Director"

    def compose(self, fury_bus, bg_role, fg_role, x_offset, y_offset, scale, opacity, optional_fg_mask=None):
        new_bus = fury_bus.copy()
        loaded = new_bus.get("loaded_assets", {})

        # 1. Lógica Inteligente de Fondo (Soporte para Encadenamiento)
        if bg_role == "previous_composition":
            if "master_composition" not in new_bus:
                raise ValueError("❌ [SceneComposer] No hay composición previa. Usa 'scene_background' en el primer nodo.")
            bg_image = new_bus["master_composition"]["image"]
            prev_mask = new_bus["master_composition"]["mask"]
        else:
            if bg_role not in loaded:
                raise ValueError(f"❌ [SceneComposer] Falta el fondo '{bg_role}'.")
            bg_image = loaded[bg_role]["image"]
            # Si es el primer fondo, la máscara previa está vacía (todo negro)
            prev_mask = torch.zeros((bg_image.shape[0], bg_image.shape[1], bg_image.shape[2]), device=bg_image.device)

        # 2. Lógica del Personaje / Frente
        if fg_role not in loaded:
            raise ValueError(f"❌ [SceneComposer] Falta el personaje '{fg_role}'.")

        fg_image = loaded[fg_role]["image"]
        char_mask = optional_fg_mask if optional_fg_mask is not None else loaded[fg_role].get("mask")

        # Clonamos lienzo
        canvas = bg_image.clone()
        B, H, W, C = canvas.shape

        # --- ESCALADO ---
        char_tensor = fg_image.permute(0, 3, 1, 2)
        target_h, target_w = int(fg_image.shape[1] * scale), int(fg_image.shape[2] * scale)

        char_resized = F.interpolate(char_tensor, size=(target_h, target_w), mode="bilinear")
        char_resized = char_resized.permute(0, 2, 3, 1)

        # --- MÁSCARA (ALPHA) ---
        if char_mask is not None:
            mask_tensor = char_mask.unsqueeze(0).unsqueeze(0) if len(char_mask.shape) == 2 else char_mask.unsqueeze(1)
            mask_resized = F.interpolate(mask_tensor, size=(target_h, target_w), mode="bilinear").squeeze(1)
            alpha = mask_resized.unsqueeze(-1)
        else:
            alpha = torch.ones((B, target_h, target_w, 1), device=canvas.device)

        alpha = alpha * opacity

        # --- FUSIÓN Y CLIPPING ---
        y1, y2 = max(0, y_offset), min(H, y_offset + target_h)
        x1, x2 = max(0, x_offset), min(W, x_offset + target_w)
        cy1, cy2 = max(0, -y_offset), max(0, -y_offset) + (y2 - y1)
        cx1, cx2 = max(0, -x_offset), max(0, -x_offset) + (x2 - x1)

        current_fg_mask = torch.zeros((B, H, W), device=canvas.device)

        if y2 > y1 and x2 > x1:
            bg_slice = canvas[:, y1:y2, x1:x2, :]
            fg_slice = char_resized[:, cy1:cy2, cx1:cx2, :]
            alpha_slice = alpha[:, cy1:cy2, cx1:cx2, :]

            # Fusión de color
            canvas[:, y1:y2, x1:x2, :] = (fg_slice * alpha_slice) + (bg_slice * (1.0 - alpha_slice))

            # Registrar la silueta de este personaje específico
            current_fg_mask[:, y1:y2, x1:x2] = alpha[:, cy1:cy2, cx1:cx2, 0]

        # --- ACUMULACIÓN DE MÁSCARAS ---
        # Sumamos la máscara de este personaje con la máscara del personaje anterior
        # Usamos torch.max para asegurarnos de que el valor no pase de 1.0 (blanco puro)
        accumulated_mask = torch.max(prev_mask, current_fg_mask)

        # 3. Guardar en el Bus
        new_bus["master_composition"] = {
            "image": canvas,
            "mask": accumulated_mask
        }

        print(f"🖼️ [SceneComposer] Añadido '{fg_role}'. Capas combinadas exitosamente.")
        return (new_bus, canvas, accumulated_mask)

# --- REGISTRO ---
NODE_CLASS_MAPPINGS = {"SF_SceneComposer": SF_SceneComposer}
NODE_DISPLAY_NAME_MAPPINGS = {"SF_SceneComposer": "🖼️ SF Scene Composer"}}