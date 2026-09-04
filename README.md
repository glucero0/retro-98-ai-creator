# Retro 98 AI Creator

A Windows 98–themed desktop studio for general-purpose AI creation: **text**, **images**, and **video** — with built-in editors, an archive of everything you make, and a fully skinnable retro desktop.

> **Work in progress.** This project is under active development. Features, APIs, config, and storage formats may change without notice. **Use at your own risk** — there is no warranty of any kind. You are responsible for API costs and any data you generate or store. Do not rely on it for production, critical, or irreversible work.

**Backend: Google Gemini** — text, image, and Veo video via separate model pickers. Studio routes by prompt intent.

## Features

- Win98 desktop UI (98.css) with draggable/minimizable windows, a taskbar, and a Start menu
- **Creation Studio** — one freeform prompt box; the app infers text/image/video from your prompt and generation intent. Turn on **Enable Tools** in Studio (or set the Control Panel default) to switch to **Search** (optional) + **Tool Use** for file, PowerShell, Gmail, Drive, Docs, Calendar, Tasks, and web-browse automation.
- **Gemini Use Tools** (optional) — attach built-in tools (`read_json`, `write_json`, `read_text`, `write_text`, `execute_powershell`, `search_gmail`, `search_drive`, `create_drive_file`, `read_google_doc`, `create_google_doc`, `edit_google_doc`, `list_calendar_events`, `create_calendar_event`, `edit_calendar_event`, `list_tasks`, `create_task`, `edit_task`, `browse_web`) and describe steps in natural language; Gemini calls them via function calling (text generations only, Windows for PowerShell)
- **Google Search enrichment** (optional, Gemini text) — when Search runs, the app can OCR images and pull YouTube captions from cited results before the tool or document pass
- **Gemini** text, image, and video generation with separate model pickers per modality
- **Archives** — every creation (and its prompt/model metadata) is saved automatically; search, import/export JSON, or import existing text/image/video files
- **Viewer** — displays the active creation (document, image, or video) with export buttons and a jump into editing
- **Image Edit** and **Video Edit** — standalone editors (and reachable via Viewer → Edit) for crop/rotate, color/filter adjustments, and (for video) a segment timeline for splitting/reordering/trimming clips
- **Control Panel** — Gemini model pickers, Google Workspace OAuth, display themes, sound, CRT overlay, and UI scale
- Cancel a generation in progress
- "Use as Basis" / "Load…" — start a new creation from the Viewer's active item or an imported file, without touching the original

## Requirements

- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/apikey), set via **Control Panel** (saved to `config.yaml`)
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
| **Creation Studio** | Type a prompt and hit **Create**. With **Enable Tools** off, one prompt box handles text/image/video. With **Enable Tools** on (Studio checkbox; Control Panel → Use Tools is the default after launch/Save), Studio shows **Search** (optional), a **Tools** panel, and **Tool Use** instead — text only. Load text/image/video files or use the Viewer's active item as a basis. |
| **Archives** | The library of everything you've generated or imported. Search, delete, import/export JSON, or import a text/image/video file directly. |
| **Viewer** | Shows the active creation — rendered document, image, or video — with export buttons (TXT/JSON/PNG/PDF/MP4 depending on type) and an **Edit** shortcut into Image Edit or Video Edit. |
| **Image Edit** | Crop, rotate, and adjust (brightness/contrast/saturation/hue/sepia/blur/exposure/gamma/vignette/tint, grayscale, threshold, sharpen, background removal). Opened standalone or via Viewer → Edit. |
| **Video Edit** | Same filter/crop/rotate toolset plus a **segment timeline**: split at the playhead, delete/reorder segments, then re-render. Requires ffmpeg. Opened standalone or via Viewer → Edit. |
| **Control Panel** | Gemini model pickers, Gemini search/tools toggles, display theme, sound, CRT scanlines, UI scale. **Save** writes `config.yaml` and resets Studio’s **Enable Tools** checkbox to the saved **Use Tools** default (search field visibility and model labels also update). |

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
| **Text / Image / Video models** | Shown on the Studio model field; routing still follows prompt intent (e.g. “generate a video” uses the video model) |
| **Google Search grounding (text)** | When on, an optional **Search** field appears in tools mode. When off, Search is hidden and no web research pass runs |
| **Two-pass verify** | Gemini text only, when Google Search is on and tools are off — extract with sources, then verify at temperature 0 |
| **Use Tools** | Saved default for Studio’s **Enable Tools** checkbox (applied on launch and after Save). Studio can still toggle tools for the current session without opening Control Panel. Text generations only |
| **OCR search images** | When a Search pass returns cited pages, download and OCR images (diagrams, scanned tables) into the research brief |
| **YouTube search captions** | When Search cites YouTube URLs, pull captions into the research brief |
| **Temperature** | Generation temperature for Gemini |
| **Extra system instructions** | Appended to every generation prompt |

## Gemini Use Tools (optional)

In **Creation Studio**, check **Enable Tools**. That is a per-session override — you do not need to open Control Panel. Control Panel → **Use Tools (local file read/write)** is only the default after launch or **Save**.

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
- **Image/video prompts** with tools on: tools are dropped for that run; Search and Tool Use text are merged into a normal media prompt instead.

**Security note:** tools read and write files on your machine, `execute_powershell` runs scripts you point at, Google tools use your connected Gmail/Drive/Docs/Calendar account, and `browse_web` fetches http(s) pages you (or the model) choose. Only attach tools you trust.

## Display, sound, and UI scale

Control Panel → **Display & Sound**:

- **Appearance**: Light, Dark, or Customize (pick a solid desktop color, window color, title bar color, text color, and font — no patterned wallpaper)
- **Sound effects** on/off
- **CRT scanlines** overlay on/off
- **UI scale** from 75%–200%, for high-DPI displays or larger text

## Data & storage

- Generated/imported creations and their prompt/model metadata live in `archives.json` (project root, gitignored)
- Media files (images, video) are stored under `media/`
- Both are local to your machine — nothing is uploaded except your prompts to Gemini

## config.yaml (excerpt)

All settings, including API keys, live in `config.yaml` (gitignored). Control Panel writes here. Copy `config.example.yaml` to get started, or just use Control Panel.

```yaml
backend:
  provider: gemini

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
