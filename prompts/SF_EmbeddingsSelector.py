import folder_paths
from utils.sf_lang import get_lang_text


class StudioFury_EmbeddingsSelector:
    @classmethod
    def INPUT_TYPES(s):
        file_list = sorted(folder_paths.get_filename_list("embeddings"))
        return {
            "required": {
                "selected_data": ("STRING", {"default": "", "multiline": False, "hidden": True}),
            },
            "optional": {
                "embedding_list_raw": (file_list,),
            },
        }

    RETURN_TYPES  = ("STRING", "STRING")
    RETURN_NAMES  = (
        get_lang_text("Positive Text", "Texto Positivo"),
        get_lang_text("Negative Text", "Texto Negativo"),
    )
    FUNCTION  = "process"
    CATEGORY  = "🧩 Studio Fury/📝 Prompts"

    def process(self, selected_data, embedding_list_raw=None):
        pos_stack = []
        neg_stack = []

        if selected_data:
            for item in selected_data.split("|"):
                if not item:
                    continue

                if item.startswith("P:"):
                    name = item[2:]
                elif item.startswith("N:"):
                    name = item[2:]
                else:
                    continue

                # Eliminar extensión del archivo para compatibilidad con todos los modelos.
                # ComfyUI espera "embedding:nombre" sin extensión.
                clean_name = name
                for ext in (".pt", ".bin", ".safetensors", ".ckpt"):
                    if clean_name.lower().endswith(ext):
                        clean_name = clean_name[: -len(ext)]
                        break

                token = f"embedding:{clean_name}"

                if item.startswith("P:"):
                    pos_stack.append(token)
                else:
                    neg_stack.append(token)

        return (", ".join(pos_stack), ", ".join(neg_stack))


NODE_CLASS_MAPPINGS = {
    "StudioFury_EmbeddingsSelector": StudioFury_EmbeddingsSelector
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "StudioFury_EmbeddingsSelector": get_lang_text("Embeddings List 💉", "Lista Embeddings 💉")
}
