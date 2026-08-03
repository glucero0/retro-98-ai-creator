# Retro 98 AI Creator

A Windows 98–themed desktop studio for general-purpose AI creation: **text**, **images**, and **video** — with built-in editors, an archive of everything you make, and a fully skinnable retro desktop.

**Default backend: Google Gemini** — text, image, and Veo video via separate model pickers. **OpenRouter** and optional **local Hugging Face** are also available; in this app they are wired for **text** generation today (see backend notes below).

## Features

- Win98 desktop UI (98.css) with draggable/minimizable windows, a taskbar, and a Start menu
- **Creation Studio** — one freeform prompt box; the app infers text/image/video from your prompt and generation intent
- **Gemini** text, image, and video generation with separate model pickers per modality
- **OpenRouter** — text chat models today (OpenRouter itself hosts many image/video models; this app does not route those yet)
- Optional **local Hugging Face** text models (Phi-3.5, Qwen, Gemma, etc.; causal-LM path only — not diffusion/video pipelines)
- **Archives** — every creation (and its prompt/model metadata) is saved automatically; search, import/export JSON, or import existing text/image/video files
- **Viewer** — displays the active creation (document, image, or video) with export buttons and a jump into editing
- **Image Edit** and **Video Edit** — standalone editors (and reachable via Viewer → Edit) for crop/rotate, color/filter adjustments, and (for video) a segment timeline for splitting/reordering/trimming clips
- **Control Panel** — backend/model selection, display themes, sound, CRT overlay, and UI scale
- Cancel a generation in progress
- "Use as Basis" / "Load…" — start a new creation from the Viewer's active item or an imported file, without touching the original

## Requirements

- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/apikey) (for the default backend)
- [ffmpeg + ffprobe](https://ffmpeg.org/) on `PATH` (or a common Windows install location) — only needed for **Video Edit**

## Quick start

```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

python -m retro_98_ai_creator
```

Then open **Control Panel** → paste your Gemini API key → pick a **Text**, **Image**, and/or **Video** model → **Save**.

## The apps

| Window | What it does |
| --- | --- |
| **Creation Studio** | Type a prompt and hit **Create**. You can also load an existing text/image/video file, or use the Viewer's active item as a starting basis for a new creation. |
| **Archives** | The library of everything you've generated or imported. Search, delete, import/export JSON, or import a text/image/video file directly. |
| **Viewer** | Shows the active creation — rendered document, image, or video — with export buttons (TXT/JSON/PNG/PDF/MP4 depending on type) and an **Edit** shortcut into Image Edit or Video Edit. |
| **Image Edit** | Crop, rotate, and adjust (brightness/contrast/saturation/hue/sepia/blur/exposure/gamma/vignette/tint, grayscale, threshold, sharpen, background removal). Opened standalone or via Viewer → Edit. |
| **Video Edit** | Same filter/crop/rotate toolset plus a **segment timeline**: split at the playhead, delete/reorder segments, then re-render. Requires ffmpeg. Opened standalone or via Viewer → Edit. |
| **Control Panel** | AI backend + model pickers, display theme, sound, CRT scanlines, UI scale. |

### Image Edit / Video Edit: Apply vs. Save

- Opened **from the Viewer** on an existing Archive item: **Apply** writes the edit back onto that creation's media file.
- Opened **standalone** (Load Image/Video…): use **Save** to overwrite the loaded file, or **Save As…** to write a new file, via a native save dialog.

## Gemini setup

1. Create a key at https://aistudio.google.com/apikey
2. Open **Control Panel** → paste the key → pick Text / Image / Video models → **Save**
3. Model lists are fetched live from Google once a key is saved; each list only shows models compatible with that modality

## OpenRouter setup

1. Create a key at https://openrouter.ai/keys
2. Control Panel → **Provider: OpenRouter** → paste the key → pick a model → **Save**
3. Google Search grounding is Gemini-only; OpenRouter uses the model's own knowledge (no grounding tool)
4. **In this app**, OpenRouter generation is text-only for now. Image/video prompts are blocked with a tip to switch to Gemini. (OpenRouter’s catalog does include image — and some video — models; wiring those into Studio would be a separate feature.)

## Local Hugging Face backend (optional)

```bash
pip install -r requirements-local.txt
```

Then in Control Panel set **Provider** to **Hugging Face local**, pick a repo (default `microsoft/Phi-3.5-mini-instruct`), and save. First run downloads weights into the HF cache. Small local models are not recommended for anything requiring factual accuracy or web knowledge.

**In this app**, the HF path is a local **causal language model** (text). The Hub also hosts diffusion / video models, but those need different pipelines (e.g. Diffusers) and are not loaded here — use Gemini for image/video generation.

## Display, sound, and UI scale

Control Panel → **Display & Sound**:

- **Appearance**: Light, Dark, or Customize (pick a solid desktop color, window color, title bar color, text color, and font — no patterned wallpaper)
- **Sound effects** on/off
- **CRT scanlines** overlay on/off
- **UI scale** from 75%–200%, for high-DPI displays or larger text

## Data & storage

- Generated/imported creations and their prompt/model metadata live in `archives.json` (project root, gitignored)
- Media files (images, video) are stored under `media/`
- Both are local to your machine — nothing is uploaded except your prompts to the selected AI backend

## config.yaml (excerpt)

All settings, including API keys, live in `config.yaml` (gitignored). Control Panel writes here. Copy `config.example.yaml` to get started, or just use Control Panel.

```yaml
backend:
  provider: gemini   # gemini | openrouter | huggingface

gemini:
  text_model: gemini-2.5-flash
  image_model: gemini-2.5-flash-image
  video_model: veo-2.0-generate-001
  api_key: your_key_here
  google_search: true
  two_pass_verify: true
  temperature: 0.0

openrouter:
  model: google/gemini-2.5-flash
  api_key: your_openrouter_key
  temperature: 0.0

model:               # used when provider: huggingface
  repo_id: microsoft/Phi-3.5-mini-instruct
  device: auto
  max_new_tokens: 2048

ui:
  app_theme: light    # light | dark | custom
  sound_enabled: true
  crt_enabled: false
  ui_scale: 1.0

paths:
  archives: archives.json
  media: media
```

## License

MIT — see [LICENSE](LICENSE).

98.css is MIT-licensed by [Jordan Scales / jdan](https://github.com/jdan/98.css).
