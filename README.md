# Retro 98 AI Creator

A Windows 98–themed desktop studio for general-purpose AI creation: **text**, **images**, and **video** — with built-in editors, an archive of everything you make, and a fully skinnable retro desktop.

> **Work in progress.** This project is under active development. Features, APIs, config, and storage formats may change without notice. **Use at your own risk** — there is no warranty of any kind. You are responsible for API costs, local model downloads, and any data you generate or store. Do not rely on it for production, critical, or irreversible work.

**Default backend: Google Gemini** — text, image, and Veo video via separate model pickers. **OpenRouter** and optional **local Hugging Face** also support three modality slots (text / image / video).

## Features

- Win98 desktop UI (98.css) with draggable/minimizable windows, a taskbar, and a Start menu
- **Creation Studio** — one freeform prompt box; the app infers text/image/video from your prompt and generation intent. With **Gemini Use Tools** enabled, Studio switches to **Search** (optional) + **Tool Use** for local file and PowerShell automation.
- **Gemini Use Tools** (optional) — attach built-in tools (`read_json`, `write_json`, `read_text`, `write_text`, `execute_powershell`, `search_gmail`) and describe steps in natural language; Gemini calls them via function calling (text generations only, Windows for PowerShell)
- **Google Search enrichment** (optional, Gemini text) — when Search runs, the app can OCR images and pull YouTube captions from cited results before the tool or document pass
- **Gemini** text, image, and video generation with separate model pickers per modality
- **OpenRouter** — text, image, and video slots (Studio routes by prompt intent)
- Optional **local Hugging Face** — text (causal LM), image (Diffusers), and video (Diffusers T2V) with separate pickers; Studio media basis uses local img2img (and I2V when the video model supports it)
- **Archives** — every creation (and its prompt/model metadata) is saved automatically; search, import/export JSON, or import existing text/image/video files
- **Viewer** — displays the active creation (document, image, or video) with export buttons and a jump into editing
- **Image Edit** and **Video Edit** — standalone editors (and reachable via Viewer → Edit) for crop/rotate, color/filter adjustments, and (for video) a segment timeline for splitting/reordering/trimming clips
- **Control Panel** — backend/model selection, display themes, sound, CRT overlay, and UI scale
- Cancel a generation in progress
- "Use as Basis" / "Load…" — start a new creation from the Viewer's active item or an imported file, without touching the original

## Requirements

- Python 3.10+
- An API key for at least one backend, set via **Control Panel** (saved to `config.yaml`):
  - **Gemini** (default backend) — a [Gemini API key](https://aistudio.google.com/apikey)
  - **OpenRouter** — an [OpenRouter API key](https://openrouter.ai/keys)
  - **Hugging Face** (optional local backend) — no key required for public models; a [Hugging Face access token](https://huggingface.co/settings/tokens) is only needed for gated/private models or to avoid rate limits, plus `pip install -r requirements-local.txt` and, for GPU use, sufficient VRAM
- **ffmpeg + ffprobe** — only needed for **Video Edit** (apply filters, split/reorder segments, export). See [Installing ffmpeg](#installing-ffmpeg) below.

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

## Installing ffmpeg

Video Edit shells out to system `ffmpeg` and `ffprobe`. They are **not** bundled with this app — install them yourself and put them on your `PATH` (or, on Windows, in a common install folder the app already checks).

Official builds and docs: [https://ffmpeg.org/download.html](https://ffmpeg.org/download.html)

### Windows

Pick one:

```bash
winget install ffmpeg
```

```bash
choco install ffmpeg
```

```bash
scoop install ffmpeg
```

Or download a build from [ffmpeg.org](https://ffmpeg.org/download.html) / [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) and add the `bin` folder (containing `ffmpeg.exe` and `ffprobe.exe`) to your user or system **PATH**. Then open a **new** terminal and confirm:

```bash
ffmpeg -version
ffprobe -version
```

### macOS

With [Homebrew](https://brew.sh/):

```bash
brew install ffmpeg
ffmpeg -version
ffprobe -version
```

### Linux

Use your distro package manager (names vary slightly):

```bash
# Debian / Ubuntu
sudo apt update && sudo apt install ffmpeg

# Fedora
sudo dnf install ffmpeg

# Arch
sudo pacman -S ffmpeg
```

Then confirm:

```bash
ffmpeg -version
ffprobe -version
```

Use a reasonably current build (roughly ffmpeg 4+). Very old copies on `PATH` (for example ancient helper scripts) can break Video Edit — remove or reorder `PATH` so the modern `ffmpeg` wins.
## The apps

| Window | What it does |
| --- | --- |
| **Creation Studio** | Type a prompt and hit **Create**. With **Use Tools** off, one prompt box handles text/image/video. With **Use Tools** on (Control Panel → Gemini), Studio shows **Search** (optional), a **Tools** panel, and **Tool Use** instead — text only. Load text/image/video files or use the Viewer's active item as a basis. |
| **Archives** | The library of everything you've generated or imported. Search, delete, import/export JSON, or import a text/image/video file directly. |
| **Viewer** | Shows the active creation — rendered document, image, or video — with export buttons (TXT/JSON/PNG/PDF/MP4 depending on type) and an **Edit** shortcut into Image Edit or Video Edit. |
| **Image Edit** | Crop, rotate, and adjust (brightness/contrast/saturation/hue/sepia/blur/exposure/gamma/vignette/tint, grayscale, threshold, sharpen, background removal). Opened standalone or via Viewer → Edit. |
| **Video Edit** | Same filter/crop/rotate toolset plus a **segment timeline**: split at the playhead, delete/reorder segments, then re-render. Requires ffmpeg. Opened standalone or via Viewer → Edit. |
| **Control Panel** | AI backend + model pickers, Gemini search/tools toggles, display theme, sound, CRT scanlines, UI scale. **Save** writes `config.yaml` and immediately updates Creation Studio (tools mode, search field visibility, model labels). |

### Image Edit / Video Edit: Apply vs. Save

- Opened **from the Viewer** on an existing Archive item: **Apply** writes the edit back onto that creation's media file.
- Opened **standalone** (Load Image/Video…): use **Save** to overwrite the loaded file, or **Save As…** to write a new file, via a native save dialog.

## Gemini setup

1. Create a key at https://aistudio.google.com/apikey
2. Open **Control Panel** → paste the key → pick Text / Image / Video models → **Save**
3. Model lists are fetched live from Google once a key is saved; each list only shows models compatible with that modality

### Control Panel → what affects Creation Studio

After **Save**, these settings apply on the next **Create** (no app restart):

| Setting | Effect on Studio |
| --- | --- |
| **Provider** | Gemini vs OpenRouter vs Hugging Face — only **Gemini** supports Google Search, Use Tools, and enrichment |
| **Text / Image / Video models** | Shown on the Studio model field; routing still follows prompt intent (e.g. “generate a video” uses the video model) |
| **Google Search grounding (text)** | When on, an optional **Search** field appears in tools mode. When off, Search is hidden and no web research pass runs |
| **Two-pass verify** | Gemini text only, when Google Search is on and tools are off — extract with sources, then verify at temperature 0 |
| **Use Tools** | Switches Studio from a single **Prompt** to **Tools** + **Tool Use** (and optional **Search**). Text generations only |
| **OCR search images** | When a Search pass returns cited pages, download and OCR images (diagrams, scanned tables) into the research brief |
| **YouTube search captions** | When Search cites YouTube URLs, pull captions into the research brief |
| **Temperature** | Generation temperature for Gemini |
| **Extra system instructions** | Appended to every generation prompt |

## Gemini Use Tools (optional)

Enable **Control Panel → Use Tools (local file read/write)** and **Save**. Creation Studio then hides the normal prompt and shows:

1. **Search** *(optional)* — what Google should look up for this run. Leave blank for tool-only workflows. Hidden entirely when Google Search is off in Control Panel.
2. **Tools** — attach one or more built-in tools with **Add Tool…**
3. **Tool Use** — describe what to do. You must mention at least one attached tool alias (e.g. `execute_powershell`, `write_text`) so the app knows which capabilities you intend.

### Built-in tools

| Alias | What it does |
| --- | --- |
| `read_json` | Read a JSON file (absolute path) |
| `write_json` | Write JSON to a file (overwrites) |
| `read_text` | Read a text file |
| `write_text` | Write text to a file (overwrites) |
| `execute_powershell` | Run a `.ps1` script (Windows only); returns `stdout`, `stderr`, and `exit_code` |
| `search_gmail` | Search your Gmail inbox (read-only) using Gmail query syntax |

### Gmail setup (`search_gmail`)

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project, enable the **Gmail API**, and create an OAuth client (**Desktop application**).
2. Download the client JSON file.
3. Control Panel → **Gemini** → **Gmail**: **Pick OAuth JSON…**, **Save**, then **Connect Gmail…** (one-time browser sign-in).
4. In Creation Studio, attach `search_gmail` and describe what to check in **Tool Use** (e.g. unread mail, shipment tracking, a specific sender).

Example queries the model may build: `is:unread in:inbox`, `category:purchases`, `subject:tracking newer_than:7d`, `from:amazon.com`.

**Security note:** `search_gmail` is read-only (`gmail.readonly` scope). The OAuth token is stored under `.retro-98-ai-creator/` (gitignored).

All paths for file tools must be **absolute** (e.g. `C:\data\step1.json`). The model infers call order from your Tool Use text once tools are attached.

### Example: PowerShell → text file (no web search)

1. Control Panel: **Use Tools** on, **Google Search** off (or on with blank Search) → **Save**
2. Studio: attach `execute_powershell` and `write_text`
3. Tool Use:

   ```
   execute_powershell on C:\scripts\getdir.ps1, then write_text the stdout to C:\output\dirs.txt
   ```

4. **Create** — Gemini runs the script, captures output, and writes the file.

### Example: Search + write JSON

1. Control Panel: **Use Tools** on, **Google Search** on → **Save**
2. Studio: attach `write_json`
3. Search: `Watch Dogs PS4 DualShock button bindings complete table`
4. Tool Use: `write_json the findings to C:\output\bindings.json` (mention `write_json`)
5. **Create** — a dedicated Search pass gathers grounded research (with optional OCR/YouTube enrichment), then the tool loop writes JSON using that brief.

### How the pipeline works

- **Tools only** (no Search text, or Google Search off): one Gemini pass with function calling on your attached tools.
- **Search + tools**: Search pass first (Google Search + URL context, plus optional image OCR and YouTube captions), then a separate tool pass that uses the research brief. Search and file tools are not combined in a single Gemini call (avoids the model skipping search or inventing file contents).
- **Image/video prompts** with tools on: tools are dropped for that run; Search and Tool Use text are merged into a normal media prompt instead.

**Security note:** tools read and write files on your machine, `execute_powershell` runs scripts you point at, and `search_gmail` reads your inbox when connected. Only attach tools you trust.

## OpenRouter setup

1. Create a key at https://openrouter.ai/keys
2. Control Panel → **Provider: OpenRouter** → paste the key → pick Text / Image / Video models → **Save**
3. Google Search grounding is Gemini-only; OpenRouter uses the model's own knowledge (no grounding tool)
4. Studio routes by prompt intent to the matching OpenRouter slot (same pattern as Gemini)

## Local Hugging Face backend (optional)

```bash
pip install -r requirements-local.txt
```

Then in Control Panel set **Provider** to **Hugging Face local**, pick **Text**, **Image**, and **Video** models, and save. You can download all three into the Hugging Face cache from the Save dialog. First generation of each modality also downloads on demand.

- **Text** — causal instruct models (Phi-3.5, Qwen, Gemma, …)
- **Image** — Diffusers text-to-image (Stable Diffusion 1.5, SD Turbo, …)
- **Video** — Diffusers text-to-video (ModelScope T2V, Zeroscope, …)

Local image/video is slow on CPU and needs substantial VRAM on GPU. Small text models are not recommended for factual docs or keybindings compared to Gemini/OpenRouter with web search.

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
  use_tools: false
  ocr_search_images: true
  youtube_search_captions: true
  temperature: 0.0

openrouter:
  text_model: google/gemini-2.5-flash
  image_model: google/gemini-2.5-flash-image
  video_model: google/veo-2.0
  api_key: your_openrouter_key
  temperature: 0.0

huggingface:         # used when provider: huggingface
  text_model: microsoft/Phi-3.5-mini-instruct
  image_model: stable-diffusion-v1-5/stable-diffusion-v1-5
  video_model: ali-vilab/text-to-video-ms-1.7b
  device: auto
  max_new_tokens: 2048

prompt:
  extra_instructions: ""

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
