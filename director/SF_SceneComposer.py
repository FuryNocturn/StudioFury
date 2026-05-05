import torch
import torch.nn.functional as F

class SF_SceneComposer:
    @classmethod
    def INPUT_TYPES(cls):
        # Definimos los roles estándar para organizar el escenario
        roles = ["scene_background", "character_main", "character_secondary", "element_overlay"]

        return {
            "required": {
                "fury_bus": ("SF_LINK",),
                "bg_role": (roles, {"default": "scene_background"}),
                "fg_role": (roles, {"default": "character_main"}),

                # Desplazamientos permitimos negativos para que el personaje pueda entrar desde fuera de cámara
                "x_offset": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "y_offset": ("INT", {"default": 0, "min": -4096, "max": 4096}),
                "scale": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 5.0, "step": 0.05}),
                "opacity": ("FLOAT", {"default": 1.0, "min": 0.0, "max": 1.0, "step": 0.05}),
            },
            "optional": {
                # Mantenemos esto opcional por si el usuario usa un nodo "Rembg" (Remove Background)
                # antes de componer y quiere inyectar esa máscara exacta.
                "optional_fg_mask": ("MASK",),
            }
        }

    RETURN_TYPES = ("SF_LINK", "IMAGE", "MASK")
    RETURN_NAMES = ("bus", "composed_image", "fusion_mask")
    FUNCTION = "compose"
    CATEGORY = "🧩 Studio Fury/🎬 Director"

    def compose(self, fury_bus, bg_role, fg_role, x_offset, y_offset, scale, opacity, optional_fg_mask=None):
        # 1. Extraer del Bus
        new_bus = fury_bus.copy()
        loaded = new_bus.get("loaded_assets", {})

        if bg_role not in loaded or fg_role not in loaded:
            raise ValueError(f"❌ [SceneComposer] Faltan activos en el bus. Asegúrate de cargar '{bg_role}' y '{fg_role}' con el AssetLoader.")

        bg_image = loaded[bg_role]["image"]
        fg_image = loaded[fg_role]["image"]

        # Si no se conectó una máscara externa, vemos si el asset ya la traía
        char_mask = optional_fg_mask
        if char_mask is None and "mask" in loaded[fg_role]:
            char_mask = loaded[fg_role]["mask"]

        # 2. Clonamos fondo para no mutar el original
        canvas = bg_image.clone()
        B, H, W, C = canvas.shape

        # --- ESCALADO ---
        # Convertimos a [B, C, H, W] para interpolar
        char_tensor = fg_image.permute(0, 3, 1, 2)
        target_h = int(fg_image.shape[1] * scale)
        target_w = int(fg_image.shape[2] * scale)

        char_resized = F.interpolate(char_tensor, size=(target_h, target_w), mode="bilinear")
        char_resized = char_resized.permute(0, 2, 3, 1) # Volver a [B, H, W, C]

        # --- MÁSCARA (ALPHA) ---
        if char_mask is not None:
            # Aseguramos formato [B, 1, H, W] para escalar
            if len(char_mask.shape) == 2:
                mask_tensor = char_mask.unsqueeze(0).unsqueeze(0)
            else:
                mask_tensor = char_mask.unsqueeze(1)

            mask_resized = F.interpolate(mask_tensor, size=(target_h, target_w), mode="bilinear")

            # Formato final [B, H, W, 1] para multiplicar fácil con RGB
            mask_resized = mask_resized.squeeze(1)
            alpha = mask_resized.unsqueeze(-1)
        else:
            # Si no hay máscara, creamos una cuadrada completa (1.0)
            alpha = torch.ones((B, target_h, target_w, 1), device=canvas.device)

        # Aplicar opacidad global
        alpha = alpha * opacity

        # --- FUSIÓN MATEMÁTICA (ALPHA BLENDING) ---
        # Coordenadas seguras (Clipping) para que no crashee si sale del borde
        y1, y2 = max(0, y_offset), min(H, y_offset + target_h)
        x1, x2 = max(0, x_offset), min(W, x_offset + target_w)

        # Coordenadas relativas al personaje (crop interno)
        cy1 = max(0, -y_offset)
        cy2 = cy1 + (y2 - y1)
        cx1 = max(0, -x_offset)
        cx2 = cx1 + (x2 - x1)

        if y2 > y1 and x2 > x1:
            bg_slice = canvas[:, y1:y2, x1:x2, :]
            fg_slice = char_resized[:, cy1:cy2, cx1:cx2, :]
            alpha_slice = alpha[:, cy1:cy2, cx1:cx2, :]

            # Fórmula: Pixel = (Foreground * Alpha) + (Background * (1 - Alpha))
            blended = (fg_slice * alpha_slice) + (bg_slice * (1.0 - alpha_slice))

            canvas[:, y1:y2, x1:x2, :] = blended

        # Crear máscara de salida para el Animator (solo la silueta final en el canvas)
        output_mask = torch.zeros((B, H, W), device=canvas.device)
        if y2 > y1 and x2 > x1:
             output_mask[:, y1:y2, x1:x2] = alpha[:, cy1:cy2, cx1:cx2, 0]

        # 3. Guardar el resultado maestro en el Bus
        new_bus["master_composition"] = {
            "image": canvas,
            "mask": output_mask
        }
        print(f"🖼️ [SceneComposer] '{fg_role}' posicionado sobre '{bg_role}'. Composición maestra lista.")

        return (new_bus, canvas, output_mask)

# --- REGISTRO DEL NODO --- (Asegúrate de que no haya conflicto en tu __init__)
NODE_CLASS_MAPPINGS = {
    "SF_SceneComposer": SF_SceneComposer
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SF_SceneComposer": "🖼️ SF Scene Composer"
}