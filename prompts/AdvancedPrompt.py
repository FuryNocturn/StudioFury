import locale

# --- CORRECCIÓN: Definimos la función directamente, no una clase ---
def get_lang_text(en, es):
    try:
        sys_lang = locale.getdefaultlocale()[0]
        is_spanish = sys_lang and "es" in sys_lang.lower()
    except:
        is_spanish = False
    return es if is_spanish else en

class StudioFury_AdvancedPrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "clip": ("CLIP",),
                "style": ("STRING", {"multiline": True, "default": "Masterpiece, best quality, photorealistic", "placeholder": get_lang_text("Style (Anime, Realistic...)", "Estilo (Anime, Realista...)")}),
                "camera": ("STRING", {"multiline": True, "default": "8k, sharp focus", "placeholder": get_lang_text("Camera (Angles, Zoom...)", "Cámara (Angular, Zoom...)")}),
                "subject": ("STRING", {"multiline": True, "default": "A beautiful woman", "placeholder": get_lang_text("Subject (Description)", "Sujeto (Descripción)")}),
                "scene": ("STRING", {"multiline": True, "default": "Standing in a garden", "placeholder": get_lang_text("Scene (Action)", "Escena (Acción)")}),
                "environment": ("STRING", {"multiline": True, "default": "Sunset, dynamic lighting", "placeholder": get_lang_text("Environment (Lighting, Details)", "Entorno (Luces, Detalles)")}),
                "negative_prompt": ("STRING", {"multiline": True, "default": "text, watermark, low quality", "placeholder": get_lang_text("Negative Prompt", "Prompt Negativo")}),
            },
            "optional": {
                "embeddings_pos": ("STRING", {"forceInput": True, "default": ""}),
                "embeddings_neg": ("STRING", {"forceInput": True, "default": ""}),
            }
        }

    RETURN_TYPES = ("CONDITIONING", "CONDITIONING")
    RETURN_NAMES = (get_lang_text("Positive", "Positivo"), get_lang_text("Negative", "Negativo"))
    FUNCTION = "execute"
    CATEGORY = "🧩 Studio Fury/📝 Prompts"

    def execute(self, clip, style, camera, subject, scene, environment, negative_prompt, embeddings_pos="", embeddings_neg=""):
        # 1. Construir Prompt Positivo
        parts_pos = [embeddings_pos, style, camera, subject, scene, environment]
        final_pos_text = ", ".join([p.strip() for p in parts_pos if p and p.strip() != ""])

        # 2. Construir Prompt Negativo
        parts_neg = [embeddings_neg, negative_prompt]
        final_neg_text = ", ".join([p.strip() for p in parts_neg if p and p.strip() != ""])

        # 3. Codificar con CLIP
        tokens_pos = clip.tokenize(final_pos_text)
        cond_pos, pooled_pos = clip.encode_from_tokens(tokens_pos, return_dict=True)

        tokens_neg = clip.tokenize(final_neg_text)
        cond_neg, pooled_neg = clip.encode_from_tokens(tokens_neg, return_dict=True)

        return ([[cond_pos, {"pooled_output": pooled_pos}]], [[cond_neg, {"pooled_output": pooled_neg}]])

NODE_CLASS_MAPPINGS = {
    "StudioFury_AdvancedPrompt": StudioFury_AdvancedPrompt
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "StudioFury_AdvancedPrompt": get_lang_text("Advanced Prompt 📝", "Prompt Avanzado 📝")
}