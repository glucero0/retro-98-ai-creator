# Retro 98 AI Creator

A Windows 98–themed desktop studio for general-purpose AI creation: **text**, **images**, **video**, and **music** — with built-in editors, an archive of everything you make, and a fully skinnable retro desktop.

> **Work in progress.** This project is under active development. Features, APIs, config, and storage formats may change without notice. **Use at your own risk** — there is no warranty of any kind. You are responsible for API costs, local model downloads, and any data you generate or store. Do not rely on it for production, critical, or irreversible work.

**Default backend: Google Gemini** — text, image, Veo video, and Lyria music via separate model pickers. **OpenRouter** and optional **local Hugging Face** support three modality slots (text / image / video). Music generation is Gemini-only.

## Features

- Win98 desktop UI (98.css) with draggable/minimizable windows, a taskbar, and a Start menu
- **Creation Studio** — one freeform prompt box; the app infers text/image/video/music from your prompt and generation intent. Turn on **Enable Tools** in Studio (or set the Control Panel default) to switch to **Search** (optional) + **Tool Use** for file, PowerShell, Gmail, Drive, Docs, Calendar, Tasks, and web-browse automation.
- **Gemini Use Tools** (optional) — attach built-in tools (`read_json`, `write_json`, `read_text`, `write_text`, `execute_powershell`, `search_gmail`, `search_drive`, `create_drive_file`, `read_google_doc`, `create_google_doc`, `edit_google_doc`, `list_calendar_events`, `create_calendar_event`, `edit_calendar_event`, `list_tasks`, `create_task`, `edit_task`, `browse_web`) and describe steps in natural language; Gemini calls them via function calling (text generations only, Windows for PowerShell)
- **Google Search enrichment** (optional, Gemini text) — when Search runs, the app can OCR images and pull YouTube captions from cited results before the tool or document pass
- **Gemini** text, image, video, and music generation with separate model pickers per modality. Music uses **Lyria** (Clip for 30-second previews, **Lyria 3.5 / Lyria Pro** for full songs). Tracks are SynthID-watermarked by Google. Use an image as a Studio basis to compose from a picture; an existing MP3 cannot be sent as audio input.
- **OpenRouter** — text, image, and video slots (Studio routes by prompt intent)
- Optional **local Hugging Face** — text (causal LM), image (Diffusers), and video (Diffusers T2V) with separate pickers; Studio media basis uses local img2img (and I2V when the video model supports it)
- **Archives** — every creation is saved automatically: text/lyrics/metadata in `archives.json`, binaries in the media folder; search, import/export JSON, or import existing text/image/video/audio files
- **Viewer** — displays the active creation (document, image, video, or audio) with optional export buttons (already-saved work does not need to be exported) and a jump into editing
- **Image Edit** and **Video Edit** — standalone editors (and reachable via Viewer → Edit) for crop/rotate, color/filter adjustments, and (for video) a segment timeline for splitting/reordering/trimming clips
- **Control Panel** — backend/model selection, Google Workspace OAuth, media folder, display themes, sound, CRT overlay, and UI scale
- Cancel a generation in progress
- "Use as Basis" / "Load…" — start a new creation from the Viewer's active item or an imported file, without touching the original. For songs this reloads the prompt and lyrics (Lyria cannot take an MP3 as input).

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

Then open **Control Panel** → paste your Gemini API key → pick a **Text**, **Image**, **Video**, and/or **Audio (Lyria)** model → **Save**. Enable Lyria (and Lyria Pro / 3.5 if you want full-length songs) for that API key in [Google AI Studio](https://aistudio.google.com/) or the linked Cloud project if the Audio picker is empty after **Refresh…**.

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
| **Creation Studio** | Type a prompt and hit **Create**. With **Enable Tools** off, one prompt box handles text/image/video/music. With **Enable Tools** on (Studio checkbox; Control Panel → Use Tools is the default after launch/Save), Studio shows **Search** (optional), a **Tools** panel, and **Tool Use** instead — text only. Load text/image/video files or use the Viewer's active item as a basis. |
| **Archives** | The library of everything you've generated or imported (catalog in `archives.json`; PNG/MP4/MP3 files in the media folder). Search, delete, import/export JSON, or import a text/image/video/audio file directly. |
| **Viewer** | Shows the active creation — rendered document, image, video, or audio — with optional export buttons (TXT/JSON/PNG/PDF/MP4/MP3 depending on type) and an **Edit** shortcut into Image Edit or Video Edit. |
| **Image Edit** | Crop, rotate, and adjust (brightness/contrast/saturation/hue/sepia/blur/exposure/gamma/vignette/tint, grayscale, threshold, sharpen, background removal). Opened standalone or via Viewer → Edit. |
| **Video Edit** | Same filter/crop/rotate toolset plus a **segment timeline**: split at the playhead, delete/reorder segments, then re-render. Requires ffmpeg. Opened standalone or via Viewer → Edit. |
| **Control Panel** | AI backend + model pickers, Gemini search/tools toggles, **Storage** / media folder picker, display theme, sound, CRT scanlines, UI scale. **Save** writes `config.yaml` and resets Studio’s **Enable Tools** checkbox to the saved **Use Tools** default (search field visibility and model labels also update). |

### Image Edit / Video Edit: Apply vs. Save

- Opened **from the Viewer** on an existing Archive item: **Apply** writes the edit back onto that creation's media file.
- Opened **standalone** (Load Image/Video…): use **Save** to overwrite the loaded file, or **Save As…** to write a new file, via a native save dialog.

## Gemini setup

1. Create a key at https://aistudio.google.com/apikey
2. Open **Control Panel** → paste the key → pick Text / Image / Video / Audio models → **Save**
3. Model lists are fetched live from Google once a key is saved; each list only shows models compatible with that modality

### Control Panel → what affects Creation Studio

After **Save**, these settings apply on the next **Create** (no app restart):

| Setting | Effect on Studio |
| --- | --- |
| **Provider** | Gemini vs OpenRouter vs Hugging Face — only **Gemini** supports Google Search, Use Tools, and enrichment |
| **Text / Image / Video / Audio models** | Shown on the Studio model field; routing still follows prompt intent (e.g. “generate a video” uses Veo, “compose a song” uses the Lyria Audio slot) |
| **Google Search grounding (text)** | When on, an optional **Search** field appears in tools mode. When off, Search is hidden and no web research pass runs |
| **Two-pass verify** | Gemini text only, when Google Search is on and tools are off — extract with sources, then verify at temperature 0 |
| **Use Tools** | Saved default for Studio’s **Enable Tools** checkbox (applied on launch and after Save). Studio can still toggle tools for the current session without opening Control Panel. Text generations only |
| **OCR search images** | When a Search pass returns cited pages, download and OCR images (diagrams, scanned tables) into the research brief |
| **YouTube search captions** | When Search cites YouTube URLs, pull captions into the research brief |
| **Temperature** | Generation temperature for Gemini |
| **Extra system instructions** | Appended to every generation prompt |
| **Media folder** | Where new **PNG / MP4 / MP3** files are written — not text, lyrics, or metadata (those stay in `archives.json`). **Save** may offer to move existing media into the new folder; declining leaves old files where they are |

## Lyria music generation (Gemini)

Music is a fourth Gemini slot (alongside text, image, and Veo). Studio routes prompts such as “compose a song”, “generate a music clip”, or “background music, instrumental only” to the **Audio (Lyria)** model. OpenRouter and Hugging Face have no music slot.

Enable the music models for your Gemini API key in [Google AI Studio](https://aistudio.google.com/) or the Google Cloud project tied to that key, then Control Panel → **Refresh…** so they appear in the Audio picker.

| Picker label | Model id | Best for |
| --- | --- | --- |
| **Lyria 3 Clip** (default) | `lyria-3-clip-preview` | 30-second clips, loops, cheap prompt iteration |
| **Lyria 3.5 / Pro** | `lyria-3.5` | Full-length songs with verses, choruses, and bridges |
| **Lyria 3 Pro Preview** | `lyria-3-pro-preview` | Older full-song id — if Google blocks it, the app retries `lyria-3.5` |

Use Clip to try a prompt, then switch to **Lyria 3.5 / Pro** when you want a longer track. Duration for full songs is influenced in the prompt (for example “a 2-minute song”) or with `[Verse]` / `[Chorus]` tags. Custom lyrics **are** allowed — include them in the prompt with those structure tags. Output is 44.1 kHz stereo **MP3**. Viewer → **Save MP3…** always uses a `.mp3` save dialog.

The app asks Lyria for lowercase `audio` and `text` response modalities so the track and lyrics both come back. If that field is rejected, it retries without it (uppercase `AUDIO` is invalid on this endpoint).

Full-length Pro / 3.5 generations run Google’s **input and output** safety filters (recitation and vocal-likeness). A prompt that works on Clip can still return `content_blocked` on Pro. Clip lyrics often include `[0.0:4.7]` timestamps; re-sending those on Pro can trip the filter even when custom `[Verse]` lyrics are fine. If that happens, the toast explains it; drop timestamped lines, try an instrumental-only wording, drop artist names, or fall back to Clip.

**Inputs the API accepts**

- **Text** — genre, instruments, BPM, key, mood, custom lyrics, `[Verse]` / `[Chorus]` / `[Bridge]` tags
- **Image** — Studio **Load Image…** or Viewer **Use as Basis** on a picture, then a music prompt (image-to-music)

**Not supported** (Google’s Lyria API, not an app limitation)

- Sending an existing **MP3** as a reference / “make a new version of this track”
- Multi-turn edit of a generated clip (“make the drums louder” on the audio itself)
- Lyria RealTime (streaming) — those live models stay hidden from the picker

**Use as Basis** on a song therefore reloads the **prompt and lyrics** into Studio as text (timestamp lines are rewritten as `[Verse]` lyrics). It does not attach the MP3. Google also safety-filters prompts that ask for a specific artist’s voice or copyrighted lyrics. All generated audio includes a SynthID watermark.

Example prompts:

```
A 30-second lofi hip hop beat with dusty vinyl crackle, mellow Rhodes
piano, boom-bap drums at 85 BPM. Instrumental only.

An upbeat chiptune title theme in C major, retro 8-bit, 120 BPM,
instrumental only.

Create a 2-minute dreamy indie pop song.

[Verse]
Walking through the neon glow…
```

## Gemini Use Tools (optional)

In **Creation Studio**, check **Enable Tools** (Gemini backend). That is a per-session override — you do not need to open Control Panel. Control Panel → **Use Tools (local file read/write)** is only the default after launch or **Save**.

When tools are on, Studio hides the normal prompt and shows:

1. **Search** *(optional)* — what Google should look up for this run. Leave blank for tool-only workflows. Hidden entirely when Google Search is off in Control Panel.
2. **Tools** — attach one or more built-in tools with **Add Tool…**
3. **Tool Use** — describe what to do. You must mention at least one attached tool alias (e.g. `execute_powershell`, `write_text`, `browse_web`) so the app knows which capabilities you intend.

### Built-in tools

| Alias | What it does |
| --- | --- |
| `read_json` | Read a JSON file (absolute path) |
| `write_json` | Write JSON to a file (overwrites) |
| `read_text` | Read a text file |
| `write_text` | Write text to a file (overwrites) |
| `execute_powershell` | Run a `.ps1` script (Windows only); returns `stdout`, `stderr`, and `exit_code` |
| `search_gmail` | Search your Gmail inbox using Gmail query syntax |
| `search_drive` | Search Google Drive files (name, MIME type, Drive query syntax) |
| `create_drive_file` | Create a Drive file (default `text/plain`) |
| `read_google_doc` | Read a Google Doc by document ID |
| `create_google_doc` | Create a Google Doc (optional initial body) |
| `edit_google_doc` | Replace or append text in a Google Doc |
| `list_calendar_events` | List Google Calendar events in a time range |
| `create_calendar_event` | Create a Google Calendar event |
| `edit_calendar_event` | Update an existing Google Calendar event |
| `list_tasks` | List Google Tasks (default list `@default`) |
| `create_task` | Create a Google Task (title, optional notes and due date/time) |
| `edit_task` | Update or complete a Google Task |
| `browse_web` | Fetch an http(s) URL, return readable text and links, then follow links to traverse |

### Google Workspace setup (Gmail, Drive, Docs, Calendar, Tasks)

One desktop OAuth client and one stored token cover all of these tools. Google Keep is not supported on a personal Gmail account. Adding a product later does not require a new client secret — enable the API, add the scope, then Connect again.

1. In [Google Cloud Console](https://console.cloud.google.com/), create a project and enable the **Gmail**, **Google Drive**, **Google Docs**, **Google Calendar**, and **Google Tasks** APIs.
2. Create an OAuth client (**Desktop application**) and download the client JSON file.
3. Control Panel → **Gemini** → **Google Workspace**: **Pick OAuth JSON…**, **Save**, then **Connect Google Workspace…** (browser sign-in). Re-connect after adding APIs so the new scopes are granted.
4. In Creation Studio, attach the tools you need (`search_gmail`, `search_drive`, `read_google_doc`, `create_calendar_event`, …) and describe the work in **Tool Use**.

When any Google Workspace tool is attached, the app injects the machine’s current date, time, timezone, and the upcoming week into the prompt behind the scenes. You can say “this coming Wednesday at 9:45am” or “mail from yesterday” — you do not type RFC3339 or today’s date. Calendar events and Task due times use that local clock with a UTC offset (not `Z` unless you asked for UTC). Gmail and Drive search resolve relative windows the same way (`after:`, `newer_than:`, `modifiedTime`). Local file tools and `browse_web` do not get the clock.

Example Gmail queries: `is:unread in:inbox`, `category:purchases`, `subject:tracking newer_than:7d`, `from:amazon.com`.

Example Drive queries: `name contains 'budget'`, `mimeType = 'application/vnd.google-apps.document'`.

**Security note:** the token can read and write Gmail, Drive, Docs, Calendar, and Tasks data you grant at consent. It is stored as `.retro-98-ai-creator/google_workspace_token.json` (the whole `.retro-98-ai-creator/` folder is gitignored). An OAuth app in Testing must reconnect about every 7 days. Existing `gmail_token.json` files are migrated on the next successful connect or refresh.

All paths for file tools must be **absolute** (e.g. `C:\data\step1.json`). The model infers call order from your Tool Use text once tools are attached.

### Example: Browse a URL (no Google Search)

1. Studio: **Enable Tools** on (or Control Panel **Use Tools** on → **Save**)
2. Attach `browse_web`
3. Tool Use:

   ```
   browse_web https://docs.python.org/3/ and follow the Tutorial link, then summarize the first page
   ```

4. **Create** — Gemini fetches the page, can follow returned links with more `browse_web` calls, then summarizes.

### Example: PowerShell → text file (no web search)

1. Studio: **Enable Tools** on; Control Panel **Google Search** off (or on with blank Search)
2. Studio: attach `execute_powershell` and `write_text`
3. Tool Use:

   ```
   execute_powershell on C:\scripts\getdir.ps1, then write_text the stdout to C:\output\dirs.txt
   ```

4. **Create** — Gemini runs the script, captures output, and writes the file.

### Example: Search + write JSON

1. Studio: **Enable Tools** on; Control Panel **Google Search** on
2. Studio: attach `write_json`
3. Search: `Watch Dogs PS4 DualShock button bindings complete table`
4. Tool Use: `write_json the findings to C:\output\bindings.json` (mention `write_json`)
5. **Create** — a dedicated Search pass gathers grounded research (with optional OCR/YouTube enrichment), then the tool loop writes JSON using that brief.

### How the pipeline works

- **Tools only** (no Search text, or Google Search off): one Gemini pass with function calling on your attached tools.
- **Search + tools**: Search pass first (Google Search + URL context, plus optional image OCR and YouTube captions), then a separate tool pass that uses the research brief. Search and file tools are not combined in a single Gemini call (avoids the model skipping search or inventing file contents).
- **Image/video/music prompts** with tools on: tools are dropped for that run; Search and Tool Use text are merged into a normal media prompt instead.

**Security note:** tools read and write files on your machine, `execute_powershell` runs scripts you point at, Google tools use your connected Gmail/Drive/Docs/Calendar account, and `browse_web` fetches http(s) pages you (or the model) choose. Only attach tools you trust.

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
- **Storage / Media folder**: **Browse…** or **Use project default**, then **Save**. This folder holds PNG/MP4/MP3 only (text and lyrics stay in `archives.json`). Default is the project `media/` folder (you can also set an absolute path). Changing the folder does not move files until you Save — then you can choose to move existing media. Declining leaves old files where they are; Archives still opens items left in the project `media/` folder.

## Data & storage

Creations are saved automatically when you generate or import. You do **not** have to Export or Save MP3/PNG/MP4 to keep them — those Viewer buttons only make an extra copy for sharing or another folder.

| What | Where it lives |
| --- | --- |
| **PNG, JPEG, MP4, MP3, WAV** (generated or imported) | **Media folder** — default `media/` next to the app, or the folder you pick in Control Panel → Display & Sound → **Storage** |
| **Text documents** (full body) | `archives.json` (project root, gitignored) — not a `.txt` in the media folder |
| **Lyrics** (from Lyria) | `archives.json`, on the song’s Archive record |
| **Prompts, titles, model ids, timestamps, extracted text** | `archives.json` (each media item also stores a `mediaPath` pointer to its file) |
| **API keys and settings** | `config.yaml` (gitignored) |

Viewer **Export TXT** / **Export Lyrics** / **Export Metadata** dump what is already in `archives.json`. **Save PNG / MP4 / MP3** copies a file that is already in the media folder.

Changing the media folder does not move files by itself. After **Save**, the app can offer to move existing images/video/audio; declining leaves them in place. Leftover files in the project `media/` folder still open. Text and lyrics are unaffected — they stay in `archives.json`.

Everything above is local. Nothing is uploaded except your prompts (and any image basis) to the selected AI backend.

## config.yaml (excerpt)

All settings, including API keys, live in `config.yaml` (gitignored). Control Panel writes here. Copy `config.example.yaml` to get started, or just use Control Panel.

```yaml
backend:
  provider: gemini   # gemini | openrouter | huggingface

gemini:
  text_model: gemini-2.5-flash
  image_model: gemini-2.5-flash-image
  video_model: veo-2.0-generate-001
  audio_model: lyria-3-clip-preview   # or lyria-3.5 / lyria-3-pro-preview
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
  media: media   # or an absolute folder set from Control Panel
```

## License

MIT — see [LICENSE](LICENSE).

98.css is MIT-licensed by [Jordan Scales / jdan](https://github.com/jdan/98.css).
