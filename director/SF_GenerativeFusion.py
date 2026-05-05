import torch
import nodes
from core.sf_io import fury_common_ksampler

class SF_GenerativeFusion:
    """
    Ejecuta un pase de Img2Img sobre la composición matemática del SceneComposer.
    Funde los bordes y adapta la iluminación del personaje al fondo basándose en un prompt de acción.
    """
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "fury_bus": ("SF_LINK",),
                "action_prompt": ("STRING", {"multiline": True, "default": "Cinematic lighting, the character is fully integrated in the environment, dramatic shadows"}),
                # Denoise bajo (0.4 - 0.6) altera la luz y bordes sin cambiar la identidad
                "denoise": ("FLOAT", {"default": 0.50, "min": 0.1, "max": 1.0, "step": 0.05}),
                "steps": ("INT", {"default": 25, "min": 1}),
                "cfg": ("FLOAT", {"default": 7.0, "min": 0.1, "max": 20.0}),
                "sampler_name": (nodes.comfy.samplers.KSampler.SAMPLERS, ),
                "scheduler": (nodes.comfy.samplers.KSampler.SCHEDULERS, ),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("SF_LINK", "IMAGE")
    RETURN_NAMES = ("bus", "fused_image")
    FUNCTION = "fuse"
    CATEGORY = "🧩 Studio Fury/🎬 Director"

    def fuse(self, model, fury_bus, action_prompt, denoise, steps, cfg, sampler_name, scheduler, seed):
        if "master_composition" not in fury_bus or "runtime" not in fury_bus:
            raise ValueError("❌ [GenerativeFusion] Faltan datos. Conecta el 'SceneComposer' al Bus primero.")

        vae = fury_bus["runtime"]["vae"]
        clip = fury_bus["runtime"]["clip"]
        composed_image = fury_bus["master_composition"]["image"]

        # 1. Pasar imagen compuesta a espacio latente
        print("✨ [GenerativeFusion] Preparando lienzo para integración por IA...")
        latent_image = {"samples": vae.encode(composed_image[:,:,:,:3])}

        # 2. Codificar la instrucción de integración (Prompt)
        tokens_pos = clip.tokenize(action_prompt)
        cond_pos, pooled_pos = clip.encode_from_tokens(tokens_pos, return_pooled=True)
        positive = [[cond_pos, {"pooled_output": pooled_pos}]]

        # Prompt negativo base genérico para evitar deformaciones en la fusión
        tokens_neg = clip.tokenize("bad anatomy, rough transition, floating, disconnected, watermark")
        cond_neg, pooled_neg = clip.encode_from_tokens(tokens_neg, return_pooled=True)
        negative = [[cond_neg, {"pooled_output": pooled_neg}]]

        # 3. KSampler (El proceso de Fusión)
        print(f"✨ [GenerativeFusion] Fusionando (Denoise: {denoise}, Pasos: {steps})...")
        samples = fury_common_ksampler(
            model, seed, steps, cfg, sampler_name, scheduler,
            positive, negative, latent_image, denoise=denoise
        )[0]

        # 4. Decodificar imagen final fundida
        fused_image = vae.decode(samples["samples"])

        # 5. Actualizar el Bus
        new_bus = fury_bus.copy()
        new_bus["master_composition"]["image"] = fused_image  # Reemplazamos la maestra
        new_bus["current_render"] = {
            "type": "scene",
            "entity_name": "Final_Fused_Scene",
            "image": fused_image,
            "latent": samples
        }

        print("✅ [GenerativeFusion] Personaje y entorno integrados con éxito.")
        return (new_bus, fused_image)

# --- REGISTRO DEL NODO ---
NODE_CLASS_MAPPINGS = {"SF_GenerativeFusion": SF_GenerativeFusion}
NODE_DISPLAY_NAME_MAPPINGS = {"SF_GenerativeFusion": "🧙‍♂️ SF Generative Fusion"}