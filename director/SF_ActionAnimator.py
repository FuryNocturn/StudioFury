import torch


class SF_ActionAnimator:
    """
    Convierte una composición estática en un flujo de video (Latent Batch).
    Devuelve 1 frame + noise_mask en lugar de repetir N veces en VRAM.
    El sampler de video (AnimateDiff) hace el expand internamente.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "vae":            ("VAE",),
                "composed_image": ("IMAGE",),
                "fusion_mask":    ("MASK",),
                "frame_count":    ("INT",   {"default": 24, "min": 8, "max": 120, "step": 8}),
                "motion_freedom": ("FLOAT", {"default": 1.0, "min": 0.1, "max": 1.0, "step": 0.1}),
            }
        }

    RETURN_TYPES = ("LATENT",)
    RETURN_NAMES = ("video_latents",)
    FUNCTION = "prepare_action"
    CATEGORY = "🧩 Studio Fury/🎬 Director"

    def prepare_action(self, vae, composed_image, fusion_mask, frame_count, motion_freedom):
        print(f"🎬 [Animator] Preparando latent base para {frame_count} frames...")

        # Codificar 1 sola imagen — el sampler de video hace el expand
        encoded        = vae.encode(composed_image[:, :, :, :3])
        original_latent = encoded["samples"]   # [1, 4, H/8, W/8]

        lat_h = original_latent.shape[2]
        lat_w = original_latent.shape[3]

        # Procesar máscara → [H, W]
        mask = fusion_mask
        if len(mask.shape) == 2:
            mask = mask.unsqueeze(0)   # [1, H, W]

        # Escalar máscara al espacio latente
        mask_resized = torch.nn.functional.interpolate(
            mask.unsqueeze(0).float(),          # [1, 1, H, W]
            size=(lat_h, lat_w),
            mode="bilinear",
            align_corners=False
        ).squeeze(0).squeeze(0)                 # [H, W]

        # Aplicar motion_freedom y expandir para frame_count
        # La noise_mask se repite aquí porque es ligera (sin canales de imagen)
        mask_final = (mask_resized * motion_freedom).unsqueeze(0)   # [1, H, W]
        mask_batch = mask_final.repeat(frame_count, 1, 1)            # [N, H, W]

        # El latent base se devuelve como 1 frame con batch_size=frame_count en metadata.
        # AnimateDiff y samplers compatibles leen "frame_count" del dict y hacen el expand.
        output_latent = {
            "samples":     original_latent,   # [1, 4, H/8, W/8] — no repetido
            "noise_mask":  mask_batch,         # [N, H, W]        — solo la máscara se expande
            "frame_count": frame_count,        # metadata para el sampler
        }

        print(f"   VRAM utilizada: 1 frame ({lat_h}×{lat_w} latent) en lugar de {frame_count}")

        return (output_latent,)


NODE_CLASS_MAPPINGS = {
    "SF_ActionAnimator": SF_ActionAnimator
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SF_ActionAnimator": "🏃 SF Action Animator"
}
