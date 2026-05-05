import torch
import nodes
import gc
from core.sf_io import FuryFileManager, fury_common_ksampler

try:
    import comfy.utils
    HAS_PROGRESS = True
except ImportError:
    HAS_PROGRESS = False

# PreviewImage instanciado una sola vez a nivel de módulo
_previewer = None

def _get_previewer():
    global _previewer
    if _previewer is None:
        from nodes import PreviewImage
        _previewer = PreviewImage()
    return _previewer


class SF_DirectorEngine:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "model": ("MODEL",),
                "charged_bus": ("SF_LINK",),
                "quality_preset": (["SD (512px)", "HD (720px)", "Full HD (1080px)", "2K (1440px)", "4K (2160px)"],),
                "steps": ("INT", {"default": 25}),
                "cfg": ("FLOAT", {"default": 8.0}),
                "sampler_name": (nodes.comfy.samplers.KSampler.SAMPLERS,),
                "scheduler": (nodes.comfy.samplers.KSampler.SCHEDULERS,),
                "denoise": ("FLOAT", {"default": 1.0}),
                "seed": ("INT", {"default": 0, "min": 0, "max": 0xffffffffffffffff}),
            }
        }

    RETURN_TYPES = ("IMAGE",)
    RETURN_NAMES = ("last_image",)
    OUTPUT_NODE = True
    FUNCTION = "run_director"
    CATEGORY = "🧩 Studio Fury/🎬 Director"

    def run_director(self, model, charged_bus, quality_preset, steps, cfg, sampler_name, scheduler, denoise, seed):
        project_name = charged_bus.get("project_name", "Untitled")
        entities     = charged_bus.get("entities", {})
        vae          = charged_bus.get("runtime", {}).get("vae")

        if not entities:
            return {"ui": {"images": []}, "result": (torch.zeros(1, 512, 512, 3),)}
        if not vae:
            raise ValueError("❌ El VAE no está en el Bus.")

        base_size = 512
        if "HD"     in quality_preset: base_size = 720
        elif "1080" in quality_preset: base_size = 1080
        elif "2K"   in quality_preset: base_size = 1440
        elif "4K"   in quality_preset: base_size = 2160

        total = len(entities)
        print(f"🎬 [Director] Iniciando Batch: {total} activos | Base: {base_size}px")

        # Barra de progreso visible en la UI de ComfyUI
        pbar = comfy.utils.ProgressBar(total) if HAS_PROGRESS else None

        previewer  = _get_previewer()
        ui_results = []
        last_tensor = None

        for i, (key, data) in enumerate(entities.items()):
            print(f"   [{i+1}/{total}] Generando: {data['name']}...")

            ratio_tag    = data.get("ratio_tag", "square")
            is_character = data["type"] == "character" or ratio_tag == "character_sheet"

            if is_character:
                width  = int(base_size * 0.66)
                height = base_size if base_size >= 1000 else int(base_size * 1.5)
            else:
                mult        = 1.0
                is_landscape = True
                if   "16:9"  in ratio_tag: mult = 1.77
                elif "21:9"  in ratio_tag: mult = 2.33
                elif "1.90"  in ratio_tag: mult = 1.90
                elif "9:16"  in ratio_tag: mult = 1.77; is_landscape = False

                if is_landscape:
                    height = base_size
                    width  = int(base_size * mult)
                else:
                    width  = base_size
                    height = int(base_size * mult)

            width  = (width  // 8) * 8
            height = (height // 8) * 8

            try:
                latent       = {"samples": torch.zeros([1, 4, height // 8, width // 8])}
                current_seed = seed + i
                samples      = fury_common_ksampler(
                    model, current_seed, steps, cfg, sampler_name, scheduler,
                    data["cond_pos"], data["cond_neg"], latent, denoise=denoise
                )[0]

                image  = vae.decode(samples["samples"])
                folder = "Characters" if data["type"] == "character" else "Scenes"

                FuryFileManager.save_fury_asset(
                    project_name, folder, data["name"],
                    {"version": "3.0", "type": data["type"], "name": data["name"],
                     "image": image, "latent": samples}
                )
                FuryFileManager.save_preview_png(project_name, folder, data["name"], image)

                saved_info = previewer.save_images(image)
                if "ui" in saved_info:
                    ui_results.extend(saved_info["ui"]["images"])

                last_tensor = image

                # Liberar tensores intermedios inmediatamente
                del image, samples, latent

            except Exception as e:
                print(f"      ❌ Error en {data['name']}: {e}")

            # Avanzar barra de progreso tras cada entidad
            if pbar:
                pbar.update(1)

        # gc y empty_cache una sola vez al terminar el batch completo,
        # no en cada iteración — evita serializar el procesamiento
        gc.collect()
        torch.cuda.empty_cache()

        if last_tensor is None:
            last_tensor = torch.zeros(1, 512, 512, 3)

        return {"ui": {"images": ui_results}, "result": (last_tensor,)}


NODE_CLASS_MAPPINGS = {
    "SF_DirectorEngine": SF_DirectorEngine
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SF_DirectorEngine": "3️⃣ SF Director Engine (Batch)"
}
