import locale

def get_lang_text(en, es):
    """
    Devuelve el texto en español si el sistema está configurado en español,
    en inglés en cualquier otro caso.
    """
    try:
        sys_lang = locale.getdefaultlocale()[0]
        is_spanish = sys_lang and "es" in sys_lang.lower()
    except Exception:
        is_spanish = False
    return es if is_spanish else en

