import os
import shutil
import importlib
import importlib.util
import traceback
import folder_paths
import filecmp

# ==============================================================================
# CONFIGURACIÓN DEL SISTEMA
# ==============================================================================

EXTENSION_NAME = "StudioFury"
NODE_CATEGORIES = ["prompts"] # Añade aquí tus categorías futuras (images, utils...)
ASSET_FOLDERS = ["js", "css", "assets", "lib", "fonts"]
DEBUG_MODE = True

# ==============================================================================
# PARTE 1: GESTOR DE ASSETS (Frontend / Javascript)
# Mantiene la estructura de carpetas original para evitar conflictos de nombres.
# ==============================================================================
def install_web_assets():
    root_dir = os.path.dirname(os.path.realpath(__file__))

    # Destino base: ComfyUI/web/extensions/StudioFury
    comfy_path = os.path.dirname(folder_paths.__file__)
    dest_root = os.path.join(comfy_path, "web", "extensions", EXTENSION_NAME)

    # Limpieza preventiva (opcional, pero recomendada para evitar basura vieja)
    # Si prefieres no borrar todo cada vez, puedes comentar estas líneas,
    # pero ayuda a eliminar archivos que hayas borrado en tu proyecto.
    if os.path.exists(dest_root):
        # Solo borramos si estamos seguros de que es nuestra carpeta
        pass

    print(f"📦 [StudioFury] Escaneando assets jerárquicos...")

    copied_count = 0

    # Recorremos el proyecto
    for root, dirs, files in os.walk(root_dir):
        # Filtros de seguridad
        if "__pycache__" in root or ".git" in root or "web/extensions" in root:
            continue

        # Revisamos las subcarpetas de la ruta actual
        for dir_name in dirs:
            # Si encontramos una carpeta de assets (js, css, etc.)
            if dir_name in ASSET_FOLDERS:
                source_folder = os.path.join(root, dir_name)

                # --- LA MAGIA: Calculamos la ruta relativa ---
                # Esto convierte "C:/.../StudioFury/prompts/js" en "prompts/js"
                relative_path = os.path.relpath(source_folder, root_dir)

                # Creamos el destino manteniendo esa ruta: ".../extensions/StudioFury/prompts/js"
                target_folder = os.path.join(dest_root, relative_path)

                if not os.path.exists(target_folder):
                    os.makedirs(target_folder)

                # Copiamos los archivos
                for file in os.listdir(source_folder):
                    src_file = os.path.join(source_folder, file)
                    dst_file = os.path.join(target_folder, file)

                    # Solo archivos, ignoramos sub-subcarpetas por ahora para simplificar
                    if os.path.isfile(src_file):
                        if not os.path.exists(dst_file) or not filecmp.cmp(src_file, dst_file):
                            shutil.copy(src_file, dst_file)
                            copied_count += 1
                            if DEBUG_MODE:
                                print(f"   -> Copiado: {relative_path}/{file}")

    if copied_count > 0:
        print(f"✅ [StudioFury] Actualizados {copied_count} archivos.")

# ==============================================================================
# PARTE 2: CARGADOR DE NODOS (Backend / Python)
# ==============================================================================
NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

def load_nodes():
    global NODE_CLASS_MAPPINGS, NODE_DISPLAY_NAME_MAPPINGS
    root_dir = os.path.dirname(os.path.realpath(__file__))

    print(f"\n🚀 [StudioFury] Cargando nodos...")

    for category in NODE_CATEGORIES:
        category_path = os.path.join(root_dir, category)

        if not os.path.exists(category_path):
            continue

        files = os.listdir(category_path)
        for file in files:
            if not file.endswith(".py") or file.startswith("__"):
                continue

            module_name = os.path.splitext(file)[0]
            file_path = os.path.join(category_path, file)

            try:
                spec = importlib.util.spec_from_file_location(module_name, file_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

                if hasattr(module, "NODE_CLASS_MAPPINGS"):
                    NODE_CLASS_MAPPINGS.update(module.NODE_CLASS_MAPPINGS)
                if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                    NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)

                if DEBUG_MODE: print(f"   ✅ Nodo cargado: {module_name}")

            except Exception as e:
                if DEBUG_MODE:
                    print(f"\n❌ [StudioFury] ERROR en {module_name}:")
                    traceback.print_exc()
                    print("---------------------------------------------------\n")

# ==============================================================================
# EJECUCIÓN
# ==============================================================================
install_web_assets()
load_nodes()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]

# Nota: Al copiar los archivos manualmente, WEB_DIRECTORY es menos crítico,
# pero podemos dejarlo apuntando a la raíz por compatibilidad.
WEB_DIRECTORY = "./"