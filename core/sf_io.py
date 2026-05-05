import os
import torch
import folder_paths
import nodes
import sys
import numpy as np
from PIL import Image

FURY_EXT = ".fury"


class FuryFileManager:
    """
    Gestor centralizado de Archivos I/O.
    """

    @staticmethod
    def get_project_root(project_name):
        output_dir   = folder_paths.get_output_directory()
        project_path = os.path.join(output_dir, "StudioFury", project_name)

        if not os.path.exists(project_path):
            try:
                os.makedirs(project_path, exist_ok=True)
                for folder in ["Characters", "Scenes", "Renders", "Cache"]:
                    os.makedirs(os.path.join(project_path, folder), exist_ok=True)
                print(f"✨ [StudioFury] Estructura creada: {project_path}")
            except Exception as e:
                print(f"❌ [StudioFury] Error IO: {e}")

        return project_path

    @staticmethod
    def save_fury_asset(project_name, subfolder, asset_name, data_dict):
        """Guarda los datos técnicos (tensores/latents) en formato .fury."""
        root      = FuryFileManager.get_project_root(project_name)
        file_path = os.path.join(root, subfolder, f"{asset_name}{FURY_EXT}")
        torch.save(data_dict, file_path)
        print(f"💾 [Data] Guardado: {asset_name}{FURY_EXT}")
        return file_path

    @staticmethod
    def save_preview_png(project_name, subfolder, asset_name, tensor_image):
        """
        Guarda un PNG de previsualización.
        compress_level=1 — prioriza velocidad de escritura sobre tamaño de archivo,
        adecuado para previsualizaciones intermedias que no se van a distribuir.
        """
        try:
            root = FuryFileManager.get_project_root(project_name)

            # Tensor [1, H, W, C] → numpy uint8
            i         = 255. * tensor_image.cpu().numpy()
            img_numpy = np.clip(i, 0, 255).astype(np.uint8)

            if img_numpy.shape[0] == 1:
                img_numpy = img_numpy[0]

            img_pil   = Image.fromarray(img_numpy)
            file_path = os.path.join(root, subfolder, f"{asset_name}.png")
            img_pil.save(file_path, compress_level=1)
            print(f"🖼️  [View] Preview generada: {asset_name}.png")

        except Exception as e:
            print(f"⚠️  Error generando PNG: {e}")

    @staticmethod
    def load_fury_asset(project_name, subfolder, asset_name):
        """
        Carga un asset .fury con weights_only=True para prevenir la ejecución
        de código arbitrario embebido en archivos pickle maliciosos.
        Solo permite tensores y tipos primitivos (dict, list, str, int, float).
        """
        root       = FuryFileManager.get_project_root(project_name)
        candidates = [
            os.path.join(root, subfolder, f"{asset_name}{FURY_EXT}"),
            os.path.join(root, subfolder, asset_name),
        ]

        for path in candidates:
            if not os.path.exists(path):
                continue
            try:
                data = torch.load(path, weights_only=True)
                # Validación mínima del esquema esperado
                if not isinstance(data, dict):
                    print(f"⚠️  [{asset_name}] El archivo no contiene un diccionario válido.")
                    return None
                if "image" not in data and "preview_image" not in data:
                    print(f"⚠️  [{asset_name}] El archivo no contiene clave 'image'.")
                    return None
                return data
            except Exception as e:
                print(f"❌ Error cargando {asset_name}: {e}")
                return None

        print(f"⚠️  [{asset_name}] Archivo no encontrado en: {root}/{subfolder}/")
        return None


# Wrapper seguro para KSampler
def fury_common_ksampler(model, seed, steps, cfg, sampler_name, scheduler,
                         positive, negative, latent, denoise=1.0):
    try:
        return nodes.common_ksampler(
            model, seed, steps, cfg, sampler_name, scheduler,
            positive, negative, latent, denoise=denoise
        )
    except Exception as e:
        print(f"❌ [FurySampler] Error crítico en sampling: {e}")
        return (latent,)
