# Game Base Ref Creator

Windows 98–themed desktop app that generates period-accurate retro game documentation (manuals, cheat sheets, lore summaries, and more).

Same Win98 / **98.css** look as the original web studio — now a Python GUI. **Default backend: Google Gemini** (fast API). Optional **local Hugging Face** models remain available for offline / open-weight use.

## Features

- Win98 desktop UI powered by [98.css](https://jdan.github.io/98.css/)
- **Gemini** generation with optional Google Search grounding
- Optional local HF models (Phi-3.5, Qwen, etc.)
- Swap backends and models from Control Panel or `config.yaml`
- Archives library with JSON import/export
- TXT / JSON / PNG / PDF document export

## Requirements

- Python 3.10+
- A [Gemini API key](https://aistudio.google.com/apikey) (for the default backend)

## Quick start

```bash
git clone https://github.com/glucero0/Game-Base-Ref-Creator.git
cd Game-Base-Ref-Creator

python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS / Linux
source .venv/bin/activate

pip install -r requirements.txt

# Set your key (or paste it in Control Panel — saved to .env)
# Windows PowerShell:
$env:GEMINI_API_KEY="your_key_here"
# Or create .env with: GEMINI_API_KEY=your_key_here

python -m retro_game_creator
```

## Gemini setup

1. Create a key at https://aistudio.google.com/apikey  
2. Either:
   - put `GEMINI_API_KEY=...` in a project `.env` (gitignored), or  
   - open **Control Panel** → paste the key → **Save Settings** (writes `.env`)
3. Default model is `gemini-2.5-flash` (changeable in Control Panel / `config.yaml`)

## Local Hugging Face backend (optional)

```bash
pip install -r requirements-local.txt
```

Then in Control Panel set **Provider** to **Hugging Face local**, pick a repo (default `microsoft/Phi-3.5-mini-instruct`), and save. First run downloads weights into the HF cache.

## config.yaml (excerpt)

Project settings live in `config.yaml` (Control Panel saves here). Secrets stay in `.env`. Archives are stored in `archives.json` (gitignored).

```yaml
backend:
  provider: gemini   # or huggingface

gemini:
  model: gemini-2.5-flash
  api_key: null      # prefer GEMINI_API_KEY in .env
  google_search: true
  temperature: 0.4

model:               # used when provider: huggingface
  repo_id: microsoft/Phi-3.5-mini-instruct
  device: auto
  max_new_tokens: 2048

paths:
  archives: archives.json
```

## License

MIT — see [LICENSE](LICENSE).

98.css is MIT-licensed by [Jordan Scales / jdan](https://github.com/jdan/98.css).
