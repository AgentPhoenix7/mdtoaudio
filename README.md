<div align="center">

```
 ███╗   ███╗██████╗ ████████╗ ██████╗  █████╗ ██╗   ██╗██████╗ ██╗ ██████╗
 ████╗ ████║██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗██║   ██║██╔══██╗██║██╔═══██╗
 ██╔████╔██║██║  ██║   ██║   ██║   ██║███████║██║   ██║██║  ██║██║██║   ██║
 ██║╚██╔╝██║██║  ██║   ██║   ██║   ██║██╔══██║██║   ██║██║  ██║██║██║   ██║
 ██║ ╚═╝ ██║██████╔╝   ██║   ╚██████╔╝██║  ██║╚██████╔╝██████╔╝██║╚██████╔╝
 ╚═╝     ╚═╝╚═════╝    ╚═╝    ╚═════╝ ╚═╝  ╚═╝ ╚═════╝ ╚═════╝ ╚═╝ ╚═════╝
```

**Turn your Obsidian notes into natural-sounding audio voiceovers — locally, for free.**

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=flat-square&logo=python&logoColor=white)
![Kokoro](https://img.shields.io/badge/TTS-Kokoro--82M-FF6B6B?style=flat-square)
![uv](https://img.shields.io/badge/package%20manager-uv-DE5FE9?style=flat-square)
![License](https://img.shields.io/badge/license-MIT-22C55E?style=flat-square)
![Tests](https://img.shields.io/badge/tests-37%20passing-22C55E?style=flat-square)

</div>

---

## What it does

Pick an Obsidian note → get a `.wav` voiceover embedded at the top of that note.

```
┌─────────────────────────────────────────────────────────────┐
│  uv run mdtoaudio.py                                        │
│                                                             │
│   ┌─────────┐   ┌─────────┐   ┌──────────┐   ┌─────────┐  │
│   │  Pick   │──▶│  Clean  │──▶│  Kokoro  │──▶│  Embed  │  │
│   │  Note   │   │  Text   │   │   TTS    │   │  .wav   │  │
│   └─────────┘   └─────────┘   └──────────┘   └─────────┘  │
│   kdialog /     strips md      natural AI     ![[note.wav]] │
│   zenity /      syntax →       voice, free,   inserted in  │
│   tkinter       clean prose    runs locally   your note    │
└─────────────────────────────────────────────────────────────┘
```

The result in your note:

```markdown
---
prev: "[[Previous Note]]"
next: "[[Next Note]]"
---

![[My Note.wav]]       ← audio player appears here in Obsidian

# My Note

Your content here...
```

---

## Features

| | |
|---|---|
| 🎙️ **Natural AI voice** | Kokoro-82M — free, local, no API key, genuinely human-sounding |
| 🧠 **Obsidian-aware** | Understands frontmatter, wiki links, embeds, Dataview, Templater |
| 📄 **Properties preserved** | Audio embed placed *after* frontmatter — Obsidian properties stay intact |
| 🪟 **Modern file picker** | Native KDE dialog (kdialog) → zenity → tkinter fallback |
| 🔇 **Clean output** | Upstream Kokoro/PyTorch warnings patched at source, not suppressed |
| 🔒 **Fully local** | No cloud, no tracking, runs entirely on your machine |

---

## How text is cleaned before narration

| Element | Example | Result |
|---|---|---|
| Frontmatter | `---\nnext: [[B]]\n---` | Stripped (not read) |
| Embedded images | `![[diagram.png]]` | Stripped |
| Wiki links | `[[My Note]]` | → "My Note" |
| Wiki links with alias | `[[My Note\|click here]]` | → "click here" |
| Code blocks | ` ```sql\nSELECT *\n``` ` | Code text read aloud |
| Inline code | `` `SELECT *` `` | → "SELECT *" |
| Dataview / Templater blocks | ` ```dataviewjs\n...\n``` ` | Stripped |
| Templater inline | `<% tp.file.cursor() %>` | Stripped |
| HTML tags | `<img src="...">` | Stripped |
| Obsidian emoji | `:LiCheckCircle:` | → "Check Circle" |
| Bold / italic | `**text**`, `*text*` | → "text" |
| Headers | `## What you'll learn` | → "What you'll learn" |
| Tables | `\| col \| col \|` | Stripped |
| `snake_case` identifiers | `my_variable` | Preserved as-is |

---

## Setup

### Prerequisites

```bash
# Install espeak-ng (required by Kokoro for phonemization on Linux)
sudo pacman -S espeak-ng        # Arch / Garuda
# sudo apt install espeak-ng    # Debian / Ubuntu
```

### Install

```bash
git clone https://github.com/yourusername/mdtoaudio
cd mdtoaudio

uv sync

cp .env.example .env
# Edit .env — add your HuggingFace token
# Get one free at: https://huggingface.co/settings/tokens
```

> **First run only:** Kokoro's 327 MB model weights download automatically and are cached locally (`~/.cache/huggingface`). All subsequent runs start instantly.

---

## Usage

```bash
uv run mdtoaudio.py
```

1. A native file picker opens rooted at your vault
2. Select any `.md` note
3. Watch the progress in your terminal:

```
Selected: /your/vault/04-Programming/What is Programming.md
Cleaning text...
Generating audio (chunk 1/3)...
Generating audio (chunk 2/3)...
Generating audio (chunk 3/3)...
Embedding audio in note...
Done → /your/vault/04-Programming/What is Programming.wav
```

4. Open the note in Obsidian — an audio player appears right after the properties block

---

## Configuration

Open `mdtoaudio.py` and edit the constants at the top:

```python
VAULT_PATH = "/your/path/to/vault/"   # where the file picker opens
SAMPLE_RATE = 24000                    # Kokoro's native rate, no need to change
```

To change the voice, edit the `voice` parameter in `convert_to_audio()`:

```python
# Some available voices:
# af_heart (default), af_sky, am_adam, bf_emma, bm_george
for _, _, audio in pipeline(chunk, voice="af_heart", speed=1.0):
```

---

## Project structure

```
mdtoaudio/
├── mdtoaudio.py              # the whole tool — single script
├── tests/
│   ├── test_clean_text.py    # 19 tests for markdown cleaning
│   ├── test_chunk_text.py    # 8 tests for paragraph chunking
│   ├── test_embed_audio.py   # 7 tests for audio embedding
│   └── test_convert_audio.py # 3 tests for TTS (mocked)
├── docs/
│   └── superpowers/
│       ├── specs/            # design spec
│       └── plans/            # implementation plan
├── .env                      # your HF_TOKEN (gitignored)
├── .env.example              # template
├── pyproject.toml
└── uv.lock
```

---

## How it works

<details>
<summary><b>clean_text(content)</b> — strips Obsidian syntax → clean prose</summary>

Applies a sequence of regex transformations in a specific order:
frontmatter → Dataview/Templater blocks → inline Templater → code fences (content kept) →
inline backticks (content kept) → embedded files → wiki links → HTML → Obsidian emoji →
bold/italic → headers → tables → horizontal rules → whitespace normalization.

Underscore italic stripping uses word-boundary guards (`(?<!\w)_(.+?)_(?!\w)`) so
`snake_case_identifiers` are never mangled.

</details>

<details>
<summary><b>chunk_text(text, max_chars=1000)</b> — splits long notes for TTS</summary>

Splits on `\n\n` paragraph boundaries. Accumulates paragraphs into chunks up to
`max_chars`. A single paragraph longer than `max_chars` stays as one chunk — it
cannot be split further without breaking sentences. This prevents Kokoro from
failing or degrading on very long inputs.

</details>

<details>
<summary><b>convert_to_audio(chunks, out_path)</b> — runs Kokoro TTS</summary>

Instantiates `KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")` once, then
calls it once per chunk with `voice="af_heart"`. Each call yields `(graphemes, phonemes, audio)`
tuples — audio arrays are collected and concatenated into a single numpy array,
then written as a 24 kHz WAV file via `soundfile`.

</details>

<details>
<summary><b>embed_audio(md_path, audio_path)</b> — inserts Obsidian audio embed</summary>

Extracts any YAML frontmatter first. Strips any existing audio embed from the top
of the body (handles re-runs cleanly). Re-assembles as
`frontmatter + \n + ![[note.wav]] + \n\n + body`.
This ensures Obsidian's Properties panel is never broken — the embed always lands
after the closing `---`.

</details>

<details>
<summary><b>Kokoro warning patches</b> — applied before import, survive venv recreation</summary>

Kokoro 0.9.4 ships with two upstream bugs that produce noisy warnings:

1. Uses deprecated `torch.nn.utils.weight_norm` → patched by replacing it with
   `torch.nn.utils.parametrizations.weight_norm` before kokoro is imported.

2. Passes `dropout=0.2` to `nn.LSTM(num_layers=1)` → patched by wrapping
   `nn.LSTM.__init__` to drop the `dropout` kwarg when `num_layers=1`,
   where it has no effect anyway.

Both patches live in `mdtoaudio.py` (tracked in git) so they apply automatically
on every machine after `uv sync` — no manual venv patching needed.

</details>

---

## Running tests

```bash
uv run pytest tests/ -v
```

```
37 passed in 2.6s
```

---

## Tech stack

| | |
|---|---|
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | State-of-the-art open-source TTS, 82M params, runs locally |
| [uv](https://docs.astral.sh/uv/) | Fast Python package and project manager |
| [soundfile](https://python-soundfile.readthedocs.io/) | WAV writing from numpy arrays |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | `.env` file loading |
| kdialog / zenity / tkinter | Native file picker: KDE → GTK → fallback |
