# 🧩 StudioFury
### Pro AI Art Direction & Advanced Workflow Suite for ComfyUI


<p align="center">
  <a href="README.md"><b>Español 🇪🇸</b></a> | 
  <a href="README_EN.md"><b>English 🇺🇸</b></a> | 
  <a href="https://github.com/FuryNocturn/StudioFury/wiki"><b>Documentation / Wiki 📖</b></a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/python-3.12%2B-blue" alt="Python Version">
  <img src="https://img.shields.io/badge/ComfyUI-Custom_Node_Suite-green" alt="ComfyUI">
  <img src="https://img.shields.io/github/license/FuryNocturn/StudioFury" alt="License">
  <img src="https://img.shields.io/badge/version-2.0.0-orange" alt="Version">
</p>

---

**Studio Fury** is a senior-level suite of custom nodes designed to transform ComfyUI into a comprehensive art direction workstation. It focuses on organizational efficiency, native multi-language support, and a high-fidelity visual interface.

> *Fury-style custom nodes: Power, Control, and Simplicity.*

---

## ✨ Key Features

* **🌐 Native Multi-language Support:** Nodes automatically detect your system language. Labels and descriptions adjust to Spanish or English accordingly.
* **🚌 SF_LINK (Charged Bus) Architecture:** Eliminate "spaghetti wiring." Our data bus system carries models, CLIP, VAE, and entity metadata through a single consolidated stream.
* **📂 Modular Architecture:** Nodes are organized into specialized categories (`prompts`, `dataset`, `director`, etc.) to keep your workspace professional and clean.
* **🚀 Intelligent Asset Management:** Automatic synchronization of web resources (JS/CSS) ensures the visual interface is always up to date and conflict-free.

---

## 📦 Included Nodes

### 📝 Category: Prompts
Advanced tools for building and managing text for broadcast models.

| Node | Description |
| :--- | :--- |
| **Advanced Prompt** 📝 | Modular prompt builder. Divides the flow into `Quality`, `Style`, `Camera`, `Subject`, and `Environment`. Includes automatic sanitization to prevent syntax errors in the final prompt. |
| **Embeddings Selector** 💉 | **Visual Interface!** Displays an interactive table with all your *embeddings*. Allows you to classify them as Positive (P) or Negative (N) with one click, eliminating the need to manually write paths. |

### 📦 Category: Dataset & Project
Asset management, data persistence, and project organization.

| Nodo | Descripción |
| :--- | :--- |
**Project Manager** 📂 | The root node. Initializes the data bus (`SF_LINK`), defines the project name, and centralizes the VAE and CLIP to maintain consistency throughout the workflow. |
**Add Entity** 👤 | Registers characters or scenes on the bus. Allows you to configure the `Aspect Ratio` and immediately encodes prompts for processing by the director's engine. |
**Smart Saver** 💾 | Export management. Saves your results in the technical `.fury` format (preserving tensors and latents) and generates a `.png` preview organized by categories. |
**Asset Loader** 📥 | Retrieves saved assets. Loads both the image and the original latent space of `.fury` files for refinements, inpainting, or variations. |

### 🎬 Category: Director
Execution engine and high-fidelity artistic compositing tools.

| Nodo | Descripción |
| :--- | :--- |
| **Director Engine** 🧠 | The massive rendering brain. Processes all entities on the bus sequentially, managing VRAM and automatically freeing memory to prevent system errors. |
| **Fury Sampler** 🎨 | Bus-injected optimized sampler. Allows for the generation of specific entity IDs individually, integrating rendering metadata into the workflow. |
| **Scene Composer** 🖼️ | Precision compositing tool. Places characters on backgrounds with full control over `Scale`, `X/Y Coordinates`, and `Opacity` using GPU tensor blending. |
| **Action Animator** 📽️ | Video flow generator. Converts static compositions into latent batches, applying Motion Freedom masks to restrict movement to specific areas. |

---

## 🛠️ Installation

### Option A: ComfyUI Manager (Recommended)
1. Search for **"ComfyUI-Studio-Fury"** in the list of custom nodes.

2. Click **Install**.

3. Restart ComfyUI.

### Option B: Manual Installation (Git)
If you prefer the command line, clone this repository into your `custom_nodes` folder:

```bash

cd ComfyUI/custom_nodes/
git clone [https://github.com/FuryNocturn/ComfyUI-Studio-Fury.git](https://github.com/FuryNocturn/ComfyUI-Studio-Fury.git)
```
Then restart your ComfyUI.

---

## 📂 Project Structure

The suite follows a modular design pattern for maximum scalability:

```
ComfyUI-Studio-Fury/
├── prompts/           # Logic for prompt construction and visual Embedding Selection.
├── core/              # System Core: File I/O management, .fury serialization, and Bus logic.
├── dataset/           # Project management, asset persistence (Smart Saver), and resource loading.
├── director/          # Rendering Engines, custom samplers, and sequential flow control.
├── images/            # (Coming Soon) Visual composition, tensor blending, and post-processing.
├── Interface/         # Global Javascript resources and system menu extensions.
└── __init__.py        # Intelligent dynamic loader and node registration engine.
```

---
## ⚙️ System Tools
Studio Fury extends the ComfyUI control menu to improve server management:

🔄 Restart Server: Restarts the ComfyUI instance to refresh nodes or free up system memory without closing the command terminal.

🛑 Shutdown Server: Performs a safe and controlled shutdown of the active server instance.

---

## 🤝 Contribute
Contributions are welcome! If you have an idea for a new node or an improvement:

1. Fork the project.

2. Create a new branch (git checkout -b feature/NewFeature).

3. Add your node to the appropriate category folder (e.g., prompts/).

4. Commit and push.

5. Open a pull request.

---

## 📄 License
This project is licensed under the MIT License.

--

Created with ❤️ by FuryNocturnTV