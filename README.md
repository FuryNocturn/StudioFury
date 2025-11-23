# 🧩 ComfyUI-Studio-Fury

![Python Version](https://img.shields.io/badge/python-3.12%2B-blue)
![ComfyUI](https://img.shields.io/badge/ComfyUI-Custom_Node-green)
![License](https://img.shields.io/github/license/FuryNocturn/ComfyUI-Studio-Fury)
![Version](https://img.shields.io/badge/version-1.0.0--r2-orange)

---

**ComfyUI-Studio-Fury** es una suite de nodos personalizados para [ComfyUI](https://github.com/comfyanonymous/ComfyUI) diseñada para añadir versatilidad y potencia a tus flujos de trabajo. Enfocado en la organización, el soporte multi-idioma y una interfaz visual mejorada.

> *Nodos custom al estilo Fury: potencia, control y simplicidad.*

---

## ✨ Características Principales

* **🌐 Soporte Multi-idioma Nativo:** Los nodos detectan automáticamente el idioma de tu sistema. Si estás en español, las entradas y salidas se mostrarán en español; de lo contrario, en inglés.
* **📂 Arquitectura Modular:** Los nodos están organizados por categorías (`prompts`, `images`, etc.) para mantener tu entorno de trabajo limpio.
* **🚀 Carga Inteligente de Assets:** Sistema automático de gestión de recursos web (JS/CSS) que evita conflictos y asegura que siempre tengas la última versión de la interfaz visual.

---

## 📦 Nodos Incluidos

### 📝 Categoría: Prompts

Herramientas avanzadas para la construcción y gestión de textos para modelos de difusión.

| Nodo | Descripción |
| :--- | :--- |
| **Advanced Prompt** 📝| Constructor de prompts modular. Permite separar `Estilo`, `Cámara`, `Sujeto`, `Escena` y `Entorno` en campos dedicados que se concatenan inteligentemente. Incluye sanitización de texto para evitar comas dobles. |
| **Embeddings List** 💉 | **¡Visual!** Muestra una tabla interactiva con todos tus archivos de *embeddings* detectados. Permite activarlos como positivos o negativos con un solo clic sin tener que escribir sus nombres manualmente. |

---

## 🛠️ Instalación

### Opción A: ComfyUI Manager (Recomendado)
1.  Busca **"ComfyUI-Studio-Fury"** en la lista de nodos personalizados.
2.  Haz clic en **Install**.
3.  Reinicia ComfyUI.

### Opción B: Instalación Manual (Git)
Si prefieres la línea de comandos, clona este repositorio dentro de tu carpeta `custom_nodes`:

```bash

cd ComfyUI/custom_nodes/
git clone [https://github.com/FuryNocturn/ComfyUI-Studio-Fury.git](https://github.com/FuryNocturn/ComfyUI-Studio-Fury.git) 
```
Luego reinicia tu ComfyUI.

---

## 📂 Estructura del Proyecto
Este pack utiliza una estructura de archivos híbrida para facilitar el desarrollo y la estabilidad:

```

ComfyUI-Studio-Fury/
├── prompts/           # Nodos relacionados con texto
├── images/            # (Próximamente) Nodos de imagen
├── js/                # Recursos Javascript globales
└── __init__.py        # Cargador dinámico inteligente

```

---

## 🤝 Contribuir
¡Las contribuciones son bienvenidas! Si tienes una idea para un nuevo nodo o una mejora:

1. Haz un Fork del proyecto.

2. Crea una nueva rama (git checkout -b feature/NuevaCaracteristica).

3. Añade tu nodo en la carpeta de categoría correspondiente (ej: prompts/).

4. Haz Commit y Push.

5. Abre un Pull Request.

---

## 📄 Licencia
Este proyecto está bajo la licencia MIT.

---

Creado con ❤️ por FuryNocturnTV
