# Voice-to-Blog AI

> Speak your ideas. Let AI turn them into polished blogs.

## Overview

Voice-to-Blog AI is a web app that turns a spoken voice note into a structured blog post. You record or upload audio, the app transcribes it **locally** with Whisper, you correct the transcript, and Google's **Gemini API (free tier)** writes a blog in the tone, length, audience and platform style you choose. You can then edit, refine and export the result. No paid API credits are needed.

## Features

- Record in the browser or upload audio (WAV, MP3, M4A, OGG, FLAC, WebM)
- Local speech-to-text with faster-whisper (audio never leaves your machine)
- Editable transcript
- Settings for tone, length, audience and platform
- Blog generation with the Gemini API free tier
- Editable blog with word count
- Generate again, Improve writing, Make shorter, Make more detailed, Change tone
- Five title suggestions, with one-click apply
- Copy (via the code box's copy icon), download as `.md` or `.txt`
- Friendly error messages (rate limits, bad key, network) and loading indicators
- Start a new blog with one click

## How It Works

```
Audio (record / upload)
   ↓
Faster-Whisper (local)
   ↓
Transcript
   ↓
User Editing
   ↓
Prompt Builder (src/prompts.py)
   ↓
Gemini API (free tier)
   ↓
Generated Blog
   ↓
Editor
   ↓
Export (.md / .txt)
```

## Architecture

| Component | Responsibility |
|---|---|
| `app.py` | Streamlit UI, session state, button handling |
| `src/speech_to_text.py` | Loads and caches the Whisper model, transcribes audio locally |
| `src/prompts.py` | Builds all LLM prompts from the user's settings |
| `src/blog_generator.py` | Calls the Gemini API with the `google-genai` SDK and maps errors to friendly messages |
| `src/utils.py` | Validation, text cleaning, export helpers |
| `tests/` | Unit tests that mock Whisper and Gemini (no key or network needed) |

Data moves between components as plain strings: audio bytes → transcript → prompt → blog.

Only the **transcript text** is sent to Gemini. The audio stays on your computer.

## Tech Stack

- **Python 3.12+**
- **Streamlit**: UI with a built-in audio recorder and widgets.
- **faster-whisper**: fast, local, free speech-to-text.
- **google-genai**: the official Google Gen AI SDK for the Gemini Developer API.
- **python-dotenv**: keeps secrets in `.env`, out of the code.

## Project Structure

```
voice-to-blog-ai/
├── app.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── .streamlit/config.toml
├── src/
│   ├── __init__.py
│   ├── speech_to_text.py
│   ├── blog_generator.py
│   ├── prompts.py
│   └── utils.py
├── tests/
│   ├── __init__.py
│   └── test_basic.py
└── outputs/.gitkeep
```

## Requirements

- Python 3.12+
- About 1 GB free disk space (packages plus the Whisper model)
- Internet for the first model download and for Gemini calls
- A **free** Gemini API key (no billing needed)
- A microphone (only for the Record tab)

## Get a Free Gemini API Key

1. Open https://aistudio.google.com/apikey and sign in with a Google account.
2. Click **Create API key**.
3. Copy the key. Do not add billing details if you want to stay on the free tier.

## Installation

### Windows (PowerShell)

```powershell
cd voice-to-blog-ai
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

If activation is blocked, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

### macOS / Linux

```bash
cd voice-to-blog-ai
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

## Environment Variables

Open `.env` and fill in:

```
GEMINI_API_KEY=your_key_here
GEMINI_MODEL=gemini-3.1-flash-lite
```

- `GEMINI_API_KEY` is required.
- `GEMINI_MODEL` is optional (default `gemini-3.1-flash-lite`, a Flash-Lite model with a free tier).
- Optional Whisper settings are listed in `.env.example`.

Restart the app after editing `.env`.

### About the free tier

- Free-tier models and limits change over time. Check your current limits at https://aistudio.google.com/rate-limit and the model list at https://ai.google.dev/gemini-api/docs/pricing.
- Lighter "Flash-Lite" models are the safest choice for a free key because they generally have more generous request limits than full "Flash" models.
- If you see a "model not found" or quota message, set `GEMINI_MODEL` to another free model.
- **Privacy:** Google states that free-tier content may be used to improve its products. Do not put confidential or personal information in your transcripts.

## Running the Application

```
streamlit run app.py
```

Streamlit starts a local web server and opens http://localhost:8501 in your browser.

## How to Use

1. Open the app.
2. Record a voice note or upload an audio file.
3. Click **Convert Speech to Text** (the first run downloads the Whisper model).
4. Fix mistakes in the transcript, then click **Use This Transcript**.
5. Choose tone, length, audience and platform.
6. Click **Generate Blog**.
7. Edit the blog, or use Improve, Shorter, More detailed, Change tone or New titles.
8. Download `.md` / `.txt`, or copy using the icon on the code box.

Every AI button is one Gemini request, so on the free tier avoid clicking many in quick succession.

## Running the Tests

```
pytest
```

Tests use mocks, so no API key, network or Whisper model is needed.

## Troubleshooting

| Problem | Fix |
|---|---|
| `python` not recognized | Reinstall Python and tick "Add python.exe to PATH", or use `py` |
| `pip` not recognized | Use `python -m pip ...` |
| `No module named google` / `google.genai` | `pip install -r requirements.txt` with the virtual environment active |
| faster-whisper install fails | Upgrade pip, use Python 3.12 (64-bit), retry |
| Whisper model download stuck | Check internet/VPN; try `WHISPER_MODEL_SIZE=tiny` |
| "Gemini API key not found" | Create `.env` from `.env.example`, add `GEMINI_API_KEY`, restart |
| "Google rejected the Gemini API key" | Re-copy the key from AI Studio, no quotes or spaces; the free tier is not available in every region |
| "rate limit or daily quota reached" | Wait a minute; if it persists you used today's free quota, so try tomorrow or set another free `GEMINI_MODEL` |
| "model was not found" | Set `GEMINI_MODEL` to a model listed in AI Studio |
| "temporarily unavailable" | Gemini is busy; retry in a moment |
| Audio can't be decoded | Convert to WAV or MP3 and retry |
| Streamlit doesn't open | Open http://localhost:8501 manually |
| Port already in use | `streamlit run app.py --server.port 8502` |
| Slow transcription | Use `tiny`/`base`, shorter audio, or a GPU |

## Security

Your `.env` holds your Gemini API key. **Never commit it.** Anyone who sees the key can use your quota or, if you later enable billing, run up charges, and bots scan GitHub for leaked keys within minutes. This repo ignores `.env` in `.gitignore` and only commits `.env.example` (no real values). If a key ever leaks, delete it in Google AI Studio and create a new one.

## Limitations

- Free-tier limits are small and can change. Heavy use will hit rate or daily limits.
- Free-tier prompts may be used by Google to improve its products.
- CPU transcription is slower than real time on weaker laptops, especially with larger models.
- Smaller Whisper models make more mistakes with accents, noise and technical terms. Always review the transcript.
- Blog generation needs an internet connection.
- LLMs can hallucinate. The prompts discourage invented facts, but you must fact-check the output.
- Very long recordings are rejected (50 MB / 30 minutes) to keep the app responsive.

## Future Improvements

- Multilingual transcription, including Tamil and English
- Authentication and a database for blog history
- SEO keywords and metadata
- Blog image generation
- RAG-based fact checking and citations
- Publishing integrations
- YouTube-to-blog and podcast-to-blog
- Switchable LLM providers (e.g. a local model through Ollama)

## Interview Explanation

**One-minute pitch:** "Voice-to-Blog AI lets you speak about a topic and get a structured blog. Audio is transcribed locally with faster-whisper, so it's private and free. The user corrects the transcript, picks tone, length, audience and platform, and my prompt builder sends only the text to the Gemini API's free tier, which writes the blog without inventing facts. The user can edit, refine and export it. I separated UI, speech, prompts and LLM code into modules, and tested them with mocks, so the tests need no API key."

**Why did you choose faster-whisper?** It runs locally, so audio stays private and there is no per-minute cost. It's about 4x faster than original Whisper on CPU and doesn't need a separate ffmpeg install.

**Why did you use an LLM?** Whisper only gives raw, messy speech text. An LLM can organize ideas, fix grammar and adapt tone and format, which speech-to-text can't do.

**Why Gemini?** Its free tier needs no billing, so the project costs nothing to run, and the official `google-genai` SDK is simple. Because all LLM code is in one module, the provider can be swapped without touching the UI.

**What happens when the user speaks?** Audio bytes go to faster-whisper, which returns a transcript. The user edits it, `prompts.py` combines it with the settings, the Gemini API returns Markdown, and the user edits and exports it.

**How did you secure the API key?** It's only in `.env`, read via `os.getenv`, never printed, and `.env` is in `.gitignore`. A `.env.example` template documents the setup.

**How did you handle free-tier limits?** I catch the SDK's API errors and map them to plain messages (429 means rate limit or daily quota, 404 means wrong model, 5xx is retried once), and the model is configurable with `GEMINI_MODEL`.

**What challenges did you face?** Streamlit reruns the script on every click, so I used session state, cached the model, and hashed the audio to avoid retranscribing. I also had to design prompts that avoid invented content.

**What would you improve next?** Multilingual support, blog history in a database, and RAG-based fact checking.

## Screenshots

_Add screenshots here (`docs/screenshot-home.png`, `docs/screenshot-blog.png`)._

## Learning Outcomes

Speech-to-text, LLM APIs, prompt engineering, prompt-injection basics, secrets management, free-tier rate limits, Streamlit state, error handling, unit testing with mocks.

## Author

Your Name | [GitHub](https://github.com/your-username) | [LinkedIn](https://linkedin.com/in/your-profile)
