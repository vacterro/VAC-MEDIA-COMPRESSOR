<div align="center">

**### THIS CONTENT IS AI GENERATED ###**
<img width="1434" height="857" alt="2026-06-13_203529" src="https://github.com/user-attachments/assets/a35a2de8-de5c-4f92-b4e3-819684381389" />
# 🚀 Smart VAC Media Compressor

**A high-performance, intelligent batch media compression suite built in Python and PyQt6.**

[![Python](https://img.shields.io/badge/Python-3.9+-blue.svg)](https://www.python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-UI-green.svg)](https://riverbankcomputing.com/software/pyqt/)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Powered-red.svg)](https://ffmpeg.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

</div>

---

## ⚡ Overview

Smart VAC Media Compressor is a professional-grade desktop application designed to handle massive directories of raw media. Whether you're batch-converting gigabytes of uncompressed 3D renders into highly optimized WebP images, or encoding raw gameplay footage into the ultra-efficient AV1 format, this tool abstracts the complex CLI arguments into a beautiful, drag-and-drop interface.

## ✨ Key Features

- **🧠 Smart Heuristics Engine:** Drop a mixed folder of `.png`, `.jpg`, and `.bmp` files. The Smart Engine automatically evaluates each file extension and applies the mathematically ideal balance of lossy/lossless conversion (e.g., raw `.bmp` maps to lossless PNG, heavy `.jpg` maps to Quality 92 WebP).
- **🔥 Saturated Concurrency:** Built on a decoupled `ThreadPoolExecutor`, the batch manager automatically scales up to your `os.cpu_count()`. Got a 16-core CPU? It processes 16 images simultaneously.
- **⚡ Quick Converter:** A dedicated scratch-pad tab for rapid operations. Drag a `.wav` file in, and it instantly suggests "Extract Audio (MP3)". Zero configuration needed.
- **🎬 Next-Gen Video Encoding:** Native support for SVT-AV1. Shrink massive MKV/MP4 files using preset CRF values optimized for either visual fidelity or aggressive compression.
- **🗜️ Zero-Encode Pass-Throughs:** Features like "Remove Audio" or "Extract Audio" use `-c copy` under the hood, bypassing the encoding pipeline entirely for instantaneous, lossless extraction.
- **🎨 Modern UI & Theming:** A polished, fully customizable PyQt6 interface with dark mode, system tray integration, window state persistence, and native tooltips.

---

## 🛠️ Prerequisites & Installation

The application relies on several industry-standard command-line utilities. Ensure these are installed and added to your system `PATH`.

### Dependencies
1. **[Python 3.9+](https://www.python.org/)** 
2. **[FFmpeg / FFprobe](https://ffmpeg.org/download.html)** — Essential for all video, audio, and GIF operations.
3. **[ImageMagick (v7+)](https://imagemagick.org/)** — Powers the core image compression and conversion engine.
4. **[texconv](https://github.com/microsoft/DirectXTex/releases)** *(Optional)* — Required for DDS/TGA texture conversions.
5. **oxipng & jpegoptim** *(Optional)* — Required for true lossless optimization pathways.

> [!TIP]
> **Portable Installation**: Instead of adding these `.exe` files to your system `PATH`, you can simply drop them into the `bin/` folder inside the project directory. The compressor will automatically detect and use them from there!

### Quick Start
```bash
# 1. Clone the repository
git clone https://github.com/vacterro/VAC-MEDIA-COMPRESSOR.git
cd VAC-MEDIA-COMPRESSOR

# 2. Install Python requirements
pip install -r requirements.txt

# 3. (Optional) Drop your downloaded .exe tools into the /bin folder

# 4. Launch the application
python main.py
```

---

## 🎮 How to Use

### The Batch Compressor
1. Drag and drop entire folders (or multiple files) into the main drop zone.
2. Tick the **Smart Auto (Best Balance)** checkbox to let the application dynamically decide the best compression routes based on file extensions.
3. (Optional) Tick **Force Output Format** to rigidly convert everything to WebP, AVIF, or PNG.
4. Hit **START BATCH COMPRESSION**. Progress is tracked dynamically via the progress bar and real-time log.

### The Quick Converter
1. Switch to the "Quick Converter" tab.
2. Drag isolated files into the table.
3. The software will auto-detect the file type and pre-select the most logical action (e.g., extracting frames, compiling sequences, extracting audio).
4. Hit **Convert All** for instantaneous processing.

---

## 🏗️ Architecture

- **`gui/main_window.py`**: The primary PyQt6 view. Handles state, styling, layouts, and drag-and-drop signals.
- **`core/batch_manager.py`**: A non-blocking QThread manager that queues tasks, evaluates file targeting, and resolves path collisions.
- **`core/smart_heuristics.py`**: The knowledge-base engine that maps file extensions to optimal lossy/lossless profiles dynamically.
- **`core/image_processor.py` / `core/video_processor.py`**: The wrappers that safely bridge the Python runtime to the underlying CLI tools (`ffmpeg`, `magick`) with strict timeout, cancellation, and stdout-capture controls.

---

<div align="center">
  <i>Built with ❤️ for performance-obsessed creators.</i>
</div>
