# Game Base Ref Creator

Windows 98–themed desktop app that generates period-accurate retro game documentation (manuals, cheat sheets, lore summaries, and more).

**Default backend: Google Gemini** (fast API). **OpenRouter** and optional **local Hugging Face** models are also available.

## Features

- Win98 desktop UI powered by [98.css](https://jdan.github.io/98.css/)
- **Gemini** generation with optional Google Search grounding
- **OpenRouter** generation (many cloud models via one API key)
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

python -m game_base_ref_creator
```

Then open **Control Panel** → paste your Gemini API key → **Save Settings** (writes `config.yaml`).

## Gemini setup

1. Create a key at https://aistudio.google.com/apikey  
2. Open **Control Panel** → paste the key → **Save Settings**  
3. Default model is `gemini-2.5-flash` (changeable in Control Panel / `config.yaml`)

## OpenRouter setup

1. Create a key at https://openrouter.ai/keys  
2. Control Panel → **Provider: OpenRouter** → paste the key → pick a model → **Save Settings**  
3. Google Search grounding is Gemini-only; OpenRouter uses the model’s own knowledge (no Gemini grounding tool)

## Local Hugging Face backend (optional)

```bash
pip install -r requirements-local.txt
```

Then in Control Panel set **Provider** to **Hugging Face local**, pick a repo (default `microsoft/Phi-3.5-mini-instruct`), and save. First run downloads weights into the HF cache.

## config.yaml (excerpt)

All settings (including the Gemini API key) live in `config.yaml`. Control Panel saves here. The file is gitignored. Archives are stored in `archives.json` (also gitignored).

```yaml
backend:
  provider: gemini   # or openrouter | huggingface

gemini:
  model: gemini-2.5-flash
  api_key: your_key_here
  google_search: true
  temperature: 0.4

openrouter:
  model: google/gemini-2.5-flash
  api_key: your_openrouter_key
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
