import torch
from core.sf_io import FuryFileManager


class SF_AssetLoader:
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "project_name": ("STRING", {"default": "My_Movie_01"}),
                "asset_type":   (["Characters", "Scenes"],),
                "asset_name":   ("STRING", {"default": "Hero_01"}),
            }
        }

    RETURN_TYPES  = ("IMAGE", "LATENT")
    RETURN_NAMES  = ("image", "latent")
    FUNCTION      = "load_asset"
    CATEGORY      = "🧩 Studio Fury/🎬 Director"

    def load_asset(self, project_name, asset_type, asset_name):
        empty_img = torch.zeros(1, 512, 512, 3)
        empty_lat = {"samples": torch.zeros([1, 4, 64, 64])}

        data = FuryFileManager.load_fury_asset(project_name, asset_type, asset_name)
        if data is None:
            return (empty_img, empty_lat)

        # La clave de imagen es siempre "image" desde la versión 3.0.
        # Soporte explícito hacia atrás para archivos guardados con versiones anteriores
        # que usaban "preview_image" como clave alternativa.
        image = data.get("image") or data.get("preview_image")
        if image is None:
            print(f"⚠️  [AssetLoader] '{asset_name}' no contiene imagen válida.")
            return (empty_img, empty_lat)

        latent = data.get("latent")
        if latent is None:
            print(f"⚠️  [AssetLoader] '{asset_name}' no contiene latent. Devolviendo latent vacío.")
            latent = empty_lat

        return (image, latent)


NODE_CLASS_MAPPINGS = {
    "SF_AssetLoader": SF_AssetLoader
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SF_AssetLoader": "📂 SF Asset Loader"
}
