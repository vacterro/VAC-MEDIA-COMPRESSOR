<div align="center">

# VAC Media Compressor

**Batch image/video compression and quick media conversion from a PyQt6 desktop interface.**

![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![PyQt6](https://img.shields.io/badge/UI-PyQt6-41CD52?style=flat-square)
![FFmpeg](https://img.shields.io/badge/media-FFmpeg-007808?style=flat-square&logo=ffmpeg&logoColor=white)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat-square)](LICENSE)

<img width="1080" alt="VAC Media Compressor main interface" src="https://github.com/user-attachments/assets/70912a79-2c2f-46ac-a970-80886d809ea9" />

</div>

## Overview

VAC Media Compressor wraps common image, video, and audio conversion jobs in a drag-and-drop GUI. It has two main workflows:

| Workflow | Best for |
|---|---|
| **Batch Compressor** | folders or mixed groups of files that should be processed together |
| **Quick Converter** | one-off jobs where the app can suggest an action from the file type |

The Python UI delegates heavy media work to established command-line tools instead of reimplementing codecs.

## Quick start

```powershell
git clone https://github.com/vacterro/VAC-MEDIA-COMPRESSOR.git
cd VAC-MEDIA-COMPRESSOR
pip install -r requirements.txt
python main.py
```

The Python requirement is intentionally small: PyQt6. Media backends can be installed globally or placed in the repository's `bin/` directory.

## Media backends

- **FFmpeg / FFprobe** — video, audio, GIF, extraction, remuxing;
- **ImageMagick 7+** — image conversion/compression paths;
- **texconv** — optional DDS/TGA texture workflows;
- **oxipng / jpegoptim** — optional lossless optimization paths.

The app checks local tools and the `bin/` folder rather than requiring every optional utility for every workflow.

## Features

- drag-and-drop batch queues;
- file-type-aware Smart Auto routing;
- WebP / AVIF / PNG and other image conversion paths;
- AV1 / HEVC / H.264 video workflows where the installed backend supports them;
- audio extraction and stream-copy operations without unnecessary re-encoding;
- background work through a non-blocking batch manager;
- output collision handling;
- progress and execution logging;
- configurable desktop theme and persistent window state.

## How to use

### Batch Compressor

1. Drop files or folders into the main queue.
2. Enable **Smart Auto** for file-type-aware routing, or choose an explicit output path/format.
3. Start the batch.
4. Follow progress and per-file messages in the live log.

### Quick Converter

1. Open the Quick Converter tab.
2. Drop one or more files.
3. Review the action suggested for each file.
4. Run **Convert All**.

## Architecture

| Path | Responsibility |
|---|---|
| `main.py` | primary application entry point |
| `gui/main_window.py` | PyQt6 interface, state, drag/drop, and layout |
| `core/batch_manager.py` | queue execution, targeting, and collision handling |
| `core/smart_heuristics.py` | file-type routing and profile selection |
| `core/image_processor.py` | image backend bridge |
| `core/video_processor.py` | video/audio backend bridge |
| `theme_config.json` | editable theme configuration |
| `build.bat` | Windows build helper |

<details>
<summary><b>Second interface view</b></summary>

<br>
<img width="1080" alt="VAC Media Compressor secondary interface" src="https://github.com/user-attachments/assets/c1df2745-f546-4c8c-b943-8ba842a31098" />
</details>

## License

[MIT](LICENSE)


## Project network

Part of the broader **SAIPEN / vacterro** project ecosystem.

[**Author hub**](https://github.com/vacterro) · [**SAIPEN HQ**](https://github.com/saipenhq) · [**SAIPEN Core**](https://github.com/vacterro/saipen) · [**ZAICODE**](https://github.com/vacterro/zaicode) · [**FastPrompter**](https://github.com/vacterro/FastPrompter) · [**SAIPEN Community**](https://discord.gg/SEYaYkuVgN)

For reproducible bugs and durable feature requests, use [GitHub Issues](https://github.com/vacterro/VAC-MEDIA-COMPRESSOR/issues).

<!-- VACTERRO_SUPPORT:BEGIN -->
---
<sub>If VAC Media Compressor is useful to you, optional support: [Buy Me a Coffee](https://buymeacoffee.com/vacuum34) · [Boosty](https://boosty.to/vacuum34/donate) · [PayPal](https://paypal.me/AlexNelin) · [other ways](https://github.com/vacterro/vacterro/blob/main/SUPPORT.md)</sub>
<!-- VACTERRO_SUPPORT:END -->
