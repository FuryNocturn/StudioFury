import copy
import torch


class SF_AddEntity:
    """
    Añade una entidad al bus y codifica sus prompts inmediatamente.
    Incluye selección de Aspect Ratio para Escenas.
    """
    def __init__(self):
        pass

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "fury_bus": ("SF_LINK",),
                "entity_type": (["character", "scene"],),
                "entity_id": ("STRING", {"default": "Hero", "placeholder": "ID (ej: Batman)"}),
                "scene_orientation": (["Landscape (16:9)", "Portrait (9:16)", "Square (1:1)", "Cinematic (21:9)", "IMAX (1.90:1)"],),
                "positive_prompt": ("STRING", {"default": "", "multiline": True}),
                "negative_prompt": ("STRING", {"default": "", "multiline": True}),
            }
        }

    RETURN_TYPES = ("SF_LINK",)
    RETURN_NAMES = ("bus",)
    FUNCTION = "add_and_encode"
    CATEGORY = "🧩 Studio Fury/📦 Dataset"

    def add_and_encode(self, fury_bus, entity_type, entity_id, scene_orientation, positive_prompt, negative_prompt):
        # deepcopy garantiza que todos los tensores de condicionamiento
        # de entidades anteriores sean copias independientes en memoria,
        # evitando que operaciones in-place downstream corrompan el bus original.
        new_bus = copy.deepcopy(fury_bus)

        clean_id = entity_id.strip()
        if not clean_id:
            return (new_bus,)

        # Lógica de ratio
        if entity_type == "character":
            ratio_tag = "character_sheet"
        else:
            ratio_tag = scene_orientation

        # Recuperar CLIP del bus
        clip = new_bus.get("runtime", {}).get("clip")
        if clip is None:
            raise ValueError("❌ Error: No hay CLIP en el Bus. Conecta el CLIP al 'Project Manager'.")

        # Construcción del prompt positivo
        final_pos = positive_prompt.strip() if positive_prompt.strip() else f"high quality {entity_type} of {clean_id}"
        if entity_type == "character":
            final_pos += ", full body view, standing pose, neutral background"

        print(f"⚡ [AddEntity] Cocinando: '{clean_id}' ({ratio_tag})")
        print(f"   Prompt positivo final: {final_pos}")

        try:
            tokens_pos = clip.tokenize(final_pos)
            tokens_neg = clip.tokenize(negative_prompt)

            cond_pos, pooled_pos = clip.encode_from_tokens(tokens_pos, return_pooled=True)
            cond_neg, pooled_neg = clip.encode_from_tokens(tokens_neg, return_pooled=True)

            new_bus["entities"][clean_id] = {
                "id":        clean_id,
                "type":      entity_type,
                "name":      clean_id,
                "ratio_tag": ratio_tag,
                "raw_pos":   final_pos,
                "cond_pos":  [[cond_pos, {"pooled_output": pooled_pos}]],
                "cond_neg":  [[cond_neg, {"pooled_output": pooled_neg}]],
            }

        except Exception as e:
            print(f"❌ Error codificando '{clean_id}': {e}")

        return (new_bus,)


NODE_CLASS_MAPPINGS = {
    "SF_AddEntity": SF_AddEntity
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "SF_AddEntity": "2️⃣ SF Add Entity (Builder)"
}
