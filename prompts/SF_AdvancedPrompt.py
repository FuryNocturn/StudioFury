from utils.sf_lang import get_lang_text


class StudioFury_AdvancedPrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP",),
                "quality": ("STRING", {
                    "multiline": True,
                    "default": "score_9, score_8_up, score_7_up, score_6_up, score_5_up, score_4_up",
                    "placeholder": get_lang_text(
                        "Quality (Score tags, Masterpiece...)",
                        "Calidad (Puntuación, Masterpiece...)"
                    ),
                }),
                "style": ("STRING", {
                    "multiline": True,
                    "default": "source_anime, best quality",
                    "placeholder": get_lang_text("Style (Anime, Realistic...)", "Estilo (Anime, Realista...)"),
                }),
                "camera": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": get_lang_text("Camera (Angles, Zoom...)", "Cámara (Angular, Zoom...)"),
                }),
                "subject": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": get_lang_text("Subject (Description)", "Sujeto (Descripción)"),
                }),
                "scene": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": get_lang_text("Scene (Action)", "Escena (Acción)"),
                }),
                "environment": ("STRING", {
                    "multiline": True,
                    "default": "",
                    "placeholder": get_lang_text("Environment (Lighting, Details)", "Entorno (Luces, Detalles)"),
                }),
                "negative_prompt": ("STRING", {
                    "multiline": True,
                    "default": "text, watermark, low quality",
                    "placeholder": get_lang_text("Negative Prompt", "Prompt Negativo"),
                }),
            },
            "optional": {
                "embeddings_pos": ("STRING", {"forceInput": True, "default": ""}),
                "embeddings_neg": ("STRING", {"forceInput": True, "default": ""}),
            },
        }

    RETURN_TYPES  = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES  = (get_lang_text("Positive", "Positivo"), get_lang_text("Negative", "Negativo"))
    FUNCTION      = "execute"
    CATEGORY      = "🧩 Studio Fury/📝 Prompts"

    def execute(self, clip, quality, style, camera, subject, scene, environment,
                negative_prompt, embeddings_pos="", embeddings_neg=""):

        # Orden: Calidad → Embeddings → Estilo → Cámara → Sujeto → Escena → Entorno
        parts_pos = [quality, embeddings_pos, style, camera, subject, scene, environment]
        final_pos = ", ".join(p.strip() for p in parts_pos if p and p.strip())

        parts_neg = [embeddings_neg, negative_prompt]
        final_neg = ", ".join(p.strip() for p in parts_neg if p and p.strip())

        tokens_pos = clip.tokenize(final_pos)
        cond_pos, pooled_pos = clip.encode_from_tokens(tokens_pos, return_pooled=True)

        tokens_neg = clip.tokenize(final_neg)
        cond_neg, pooled_neg = clip.encode_from_tokens(tokens_neg, return_pooled=True)

        return (
            [[cond_pos, {"pooled_output": pooled_pos}]],
            [[cond_neg, {"pooled_output": pooled_neg}]],
        )


NODE_CLASS_MAPPINGS = {
    "StudioFury_AdvancedPrompt": StudioFury_AdvancedPrompt
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "StudioFury_AdvancedPrompt": get_lang_text("Advanced Prompt 📝", "Prompt Avanzado 📝")
}
