import os
import shutil
import importlib
import importlib.util
import traceback
import folder_paths
import filecmp
import sys
import inspect

from server import PromptServer
from aiohttp import web

# ==============================================================================
#  CONFIGURACIÓN
# ==============================================================================
EXTENSION_NAME = "StudioFury"
DEBUG_MODE = True

# Archivos Python a ignorar (nunca contienen nodos)
IGNORE_FILES = {"__init__.py", "sf_io.py", "setup.py", "install.py"}

# Directorios a ignorar completamente durante el escaneo
IGNORE_DIRS  = {".idea", ".git", "interface", "js", "__pycache__",
                "node_modules", ".venv", "venv", "dist", "build"}

# ==============================================================================
#  PATH
# ==============================================================================
node_root = os.path.dirname(os.path.abspath(__file__))
if node_root not in sys.path:
    sys.path.insert(0, node_root)

# ==============================================================================
#  ESTADO DE DIAGNÓSTICO
# ==============================================================================
# Acumula el resultado de cada archivo intentado
_load_report = []   # List[dict]  — {file, status, nodes, error, tb}

def _report(file, status, nodes=None, error=None, tb=None):
    """Registra el resultado de un intento de carga."""
    _load_report.append({
        "file":   file,
        "status": status,          # "ok" | "error" | "skip" | "empty"
        "nodes":  nodes or [],
        "error":  error,
        "tb":     tb,
    })

# ==============================================================================
#  1. API — SISTEMA + DIAGNÓSTICO
# ==============================================================================
try:
    routes = PromptServer.instance.routes

    @routes.post("/studiofury/system/shutdown")
    async def fury_shutdown(request):
        print(f"\n🛑 [{EXTENSION_NAME}] Apagando servidor...")
        sys.stdout.flush()
        os._exit(0)

    @routes.post("/studiofury/system/restart")
    async def fury_restart(request):
        print(f"\n🔄 [{EXTENSION_NAME}] Reiniciando servidor...")
        sys.stdout.flush()
        os.execv(sys.executable, [sys.executable] + sys.argv)

    @routes.get("/studiofury/diagnostics")
    async def fury_diagnostics(request):
        """
        Endpoint que devuelve el informe completo de carga en JSON.
        Accesible desde el navegador en: http://localhost:8188/studiofury/diagnostics
        """
        import json
        summary = {
            "extension":    EXTENSION_NAME,
            "total_files":  len(_load_report),
            "ok":           sum(1 for r in _load_report if r["status"] == "ok"),
            "errors":       sum(1 for r in _load_report if r["status"] == "error"),
            "empty":        sum(1 for r in _load_report if r["status"] == "empty"),
            "skipped":      sum(1 for r in _load_report if r["status"] == "skip"),
            "total_nodes":  sum(len(r["nodes"]) for r in _load_report),
            "nodes_loaded": [n for r in _load_report for n in r["nodes"]],
            "details":      [
                {
                    "file":   r["file"],
                    "status": r["status"],
                    "nodes":  r["nodes"],
                    "error":  r["error"],
                    # Traceback completo solo si hay error
                    "traceback": r["tb"] if r["status"] == "error" else None,
                }
                for r in _load_report
            ],
        }
        return web.Response(
            text=json.dumps(summary, indent=2, ensure_ascii=False),
            content_type="application/json"
        )

    @routes.get("/studiofury/diagnostics/errors")
    async def fury_diagnostics_errors(request):
        """Solo devuelve los archivos con error — útil para debugging rápido."""
        import json
        errors = [r for r in _load_report if r["status"] == "error"]
        return web.Response(
            text=json.dumps(errors, indent=2, ensure_ascii=False),
            content_type="application/json"
        )

except Exception as e:
    print(f"⚠️  [{EXTENSION_NAME}] Error registrando APIs: {e}")

# ==============================================================================
#  2. INSTALADOR DE ASSETS WEB
# ==============================================================================
WEB_DIRECTORY = "./interface/js"

def install_web_assets():
    try:
        current_dir  = os.path.dirname(__file__)
        js_folder    = os.path.join(current_dir, "js")
        comfy_path   = os.path.dirname(folder_paths.__file__)
        dest_folder  = os.path.join(comfy_path, "web", "extensions", EXTENSION_NAME)

        if not os.path.exists(js_folder):
            return

        os.makedirs(dest_folder, exist_ok=True)
        for file in os.listdir(js_folder):
            if file.endswith(".js") or file.endswith(".css"):
                src = os.path.join(js_folder, file)
                dst = os.path.join(dest_folder, file)
                if not os.path.exists(dst) or not filecmp.cmp(src, dst, shallow=False):
                    shutil.copy2(src, dst)
                    if DEBUG_MODE:
                        print(f"   ⚡ Asset actualizado: {file}")
    except Exception as e:
        print(f"⚠️  [{EXTENSION_NAME}] Error instalando assets: {e}")

# ==============================================================================
#  3. CARGADOR DINÁMICO — AUTO-REGISTRO CON DIAGNÓSTICO COMPLETO
# ==============================================================================
NODE_CLASS_MAPPINGS         = {}
NODE_DISPLAY_NAME_MAPPINGS  = {}

def load_nodes():
    print(f"\n{'='*60}")
    print(f"  🧩 {EXTENSION_NAME} — Iniciando carga de nodos")
    print(f"{'='*60}")

    for root, dirs, files in os.walk(node_root):
        # ── Excluir directorios ignorados (modificar dirs in-place detiene os.walk) ──
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]

        for file in files:
            if not file.endswith(".py") or file in IGNORE_FILES:
                continue

            module_path  = os.path.join(root, file)
            # Nombre único para el módulo (relativo al root, con puntos)
            rel_path     = os.path.relpath(module_path, node_root)
            module_name  = rel_path.replace(os.sep, ".").removesuffix(".py")
            display_path = rel_path  # Para mensajes

            try:
                spec   = importlib.util.spec_from_file_location(module_name, module_path)
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)

            except Exception as e:
                tb_str = traceback.format_exc()
                _report(display_path, "error", error=str(e), tb=tb_str)

                # ── ERROR VISIBLE ── siempre se imprime, independiente de DEBUG_MODE
                print(f"\n  ❌ ERROR cargando: {display_path}")
                print(f"     {type(e).__name__}: {e}")
                if DEBUG_MODE:
                    # Traceback completo indentado para fácil lectura
                    for line in tb_str.strip().splitlines():
                        print(f"     {line}")
                else:
                    # En producción, solo la línea relevante
                    lines = [l for l in tb_str.strip().splitlines() if "File" in l or str(e) in l]
                    for line in lines[-3:]:
                        print(f"     {line}")
                continue

            # ── Estrategia A: el archivo declara sus propios mapeos ──────────────
            nodes_found = []

            if hasattr(module, "NODE_CLASS_MAPPINGS"):
                for name, cls in module.NODE_CLASS_MAPPINGS.items():
                    NODE_CLASS_MAPPINGS[name] = cls
                    nodes_found.append(name)

                if hasattr(module, "NODE_DISPLAY_NAME_MAPPINGS"):
                    NODE_DISPLAY_NAME_MAPPINGS.update(module.NODE_DISPLAY_NAME_MAPPINGS)

                _report(display_path, "ok" if nodes_found else "empty", nodes=nodes_found)

                if DEBUG_MODE and nodes_found:
                    print(f"  ✅ {display_path} ({len(nodes_found)} nodos)")
                    for n in nodes_found:
                        print(f"     └─ {n}")

            # ── Estrategia B: introspección automática ────────────────────────────
            else:
                for name, obj in inspect.getmembers(module, inspect.isclass):
                    # Solo clases definidas en este módulo (no importadas)
                    if obj.__module__ != module_name:
                        continue
                    # Verificar firma de nodo ComfyUI
                    if not (hasattr(obj, "INPUT_TYPES") and hasattr(obj, "RETURN_TYPES")):
                        continue

                    NODE_CLASS_MAPPINGS[name] = obj
                    fancy = "🧩 SF " + name.replace("SF_", "").replace("_", " ")
                    NODE_DISPLAY_NAME_MAPPINGS[name] = fancy
                    nodes_found.append(name)

                    if DEBUG_MODE:
                        print(f"  🪄 Auto-registrado: {fancy}  ←  {display_path}")

                if nodes_found:
                    _report(display_path, "ok", nodes=nodes_found)
                else:
                    _report(display_path, "empty")

    # ── Resumen final ──────────────────────────────────────────────────────────
    ok_count    = sum(1 for r in _load_report if r["status"] == "ok")
    err_count   = sum(1 for r in _load_report if r["status"] == "error")
    total_nodes = len(NODE_CLASS_MAPPINGS)

    print(f"\n{'='*60}")
    print(f"  {EXTENSION_NAME} — Resumen de carga")
    print(f"  Archivos OK : {ok_count}")
    print(f"  Nodos activos: {total_nodes}")

    if err_count > 0:
        print(f"\n  ⚠️  ARCHIVOS CON ERROR: {err_count}")
        for r in _load_report:
            if r["status"] == "error":
                print(f"     ✗ {r['file']}")
                print(f"       {r['error']}")
        print(f"\n  💡 Ver diagnóstico completo en:")
        print(f"     http://localhost:8188/studiofury/diagnostics")
        print(f"     http://localhost:8188/studiofury/diagnostics/errors")
    else:
        print(f"  ✅ Todos los archivos cargados sin errores")

    print(f"{'='*60}\n")

# ==============================================================================
#  EJECUCIÓN
# ==============================================================================
install_web_assets()
load_nodes()

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]
