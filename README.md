<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=200&section=header&text=mdtoaudio&fontSize=72&fontColor=fff&fontAlignY=38&desc=Obsidian%20notes%20%E2%86%92%20natural%20audio%2C%20locally%20and%20for%20free&descAlignY=56&descSize=16&descColor=fff" alt="mdtoaudio header" />

<img src="https://readme-typing-svg.demolab.com?font=JetBrains+Mono&size=15&pause=1000&color=FF6B6B&center=true&vCenter=true&width=580&lines=Pick+a+note+%E2%86%92+get+a+.wav+voiceover+embedded;Single+file+or+entire+folder+%E2%80%94+recursively;100%25+local+%E2%80%94+no+cloud%2C+no+API+key;Live+terminal+menu+%2B+native+OS+pickers" alt="Typing SVG" />

<br />
<br />

![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Kokoro](https://img.shields.io/badge/TTS-Kokoro--82M-FF6B6B?style=for-the-badge)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9?style=for-the-badge)
![License](https://img.shields.io/badge/license-MIT-22C55E?style=for-the-badge)
![Tests](https://img.shields.io/badge/tests-66%20passing-22C55E?style=for-the-badge)

</div>

<br />

---

## ✨ What it does

Pick an Obsidian note (or an entire folder) → get `.wav` voiceovers embedded at the top of each note.

```bash
  uv run mdtoaudio.py

  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
  │  ⌨️  Terminal │────▶│  🗂️  Native  │────▶│  🧹  Clean  │────▶│  🎙️  Kokoro │
  │     Menu     │     │    Picker    │     │    Text      │     │     TTS      │
  └──────────────┘     └──────────────┘     └──────────────┘     └──────┬───────┘
  ↑↓ navigate          Win32 / kdialog /    strips Obsidian             │
  Enter confirm        zenity / tkinter     syntax → prose              ▼
  q quit               rooted at vault                          ┌──────────────┐
                                                                │  📎  Embed  │
                                                                │    .wav      │
                                                                └──────────────┘
                                                                ![[note.wav]]
                                                                in your note
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

## 🚀 Features

<table>
<tr>
<td width="50%">

**🎙️ Natural AI Voice**

Kokoro-82M — free, local, no API key, genuinely human-sounding

</td>
<td width="50%">

**📁 File or Folder Mode**

Convert one note or recurse through an entire vault subfolder at once

</td>
</tr>
<tr>
<td>

**🧠 Obsidian-Aware**

Understands frontmatter, wiki links, embeds, Dataview, Templater, and tables

</td>
<td>

**⌨️ Live Terminal Menu**

Arrow-key mode selector renders in-place in the terminal — no GUI pop-up needed

</td>
</tr>
<tr>
<td>

**🪟 Native OS Pickers**

Win32 `GetOpenFileNameW` / `SHBrowseForFolderW` → kdialog → zenity → tkinter

</td>
<td>

**📄 Properties Preserved**

Audio embed placed *after* frontmatter — Obsidian Properties panel stays intact

</td>
</tr>
<tr>
<td>

**🔇 Clean Output**

Upstream Kokoro/PyTorch warnings patched at source, not suppressed

</td>
<td>

**🔒 Fully Local**

No cloud, no tracking, runs entirely on your machine

</td>
</tr>
</table>

---

## 🧹 How text is cleaned before narration

| Element | Example | Result |
| --- | --- | --- |
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
| Tables | `\| Name \| Age \|` | → "Name, Age. Alice, 30." |
| `snake_case` identifiers | `my_variable` | Preserved as-is |

---

## ⚙️ Setup

### Prerequisites

```bash
# Linux only — Kokoro requires espeak-ng for phonemization
sudo pacman -S espeak-ng        # Arch / Garuda
# sudo apt install espeak-ng    # Debian / Ubuntu
```

### Install

```bash
git clone https://github.com/AgentPhoenix7/mdtoaudio
cd mdtoaudio
uv sync
cp .env.example .env
# Edit .env and add your HuggingFace token
# Get one free at: https://huggingface.co/settings/tokens
```

> **First run only:** Kokoro's 327 MB model weights are downloaded automatically and cached in `~/.cache/huggingface`. All subsequent runs start instantly.

---

## 💻 Usage

```bash
uv run mdtoaudio.py
```

**Step 1 — choose a mode** in the live terminal menu:

```text
  Select mode:

  ▶ Single file
    Entire folder (recursive)

  ↑↓ / j k  navigate   Enter  confirm   q  quit
```

**Step 2 — pick a file or folder** from the native OS dialog (opens at your vault root).

**Step 3 — watch the progress:**

*Single file:*

```text
Processing: D:\Drive Vault\04-Programming\What is Programming.md
  Generating audio (chunk 1/3)...
  Generating audio (chunk 2/3)...
  Generating audio (chunk 3/3)...
  Done → D:\Drive Vault\04-Programming\What is Programming.wav
```

*Folder (recursive):*

```text
Found 12 markdown file(s). Starting conversion...
Processing: D:\Drive Vault\04-Programming\Algorithms\BFS.md
  Done → D:\Drive Vault\04-Programming\Algorithms\BFS.wav
Processing: D:\Drive Vault\04-Programming\Algorithms\DFS.md
  Skipping (no readable text): ...DFS.md
...
All done. Processed 12 file(s).
```

**Step 4 —** open any processed note in Obsidian. An audio player appears right after the Properties block.

---

## 🔧 Configuration

Before running the script, update `VAULT_PATH` in `mdtoaudio.py` to point to your own Obsidian vault:

```python
VAULT_PATH = r"D:\Drive Vault" if sys.platform == "win32" else "/run/media/agntdrgn/Expansion/Drive Vault/"
SAMPLE_RATE = 24000  # Kokoro's native rate
```

> **Required:** Both the file picker and folder picker open rooted at `VAULT_PATH`, so the script won't navigate to your vault unless this is set correctly.

To change voice, edit the `voice` parameter in `convert_to_audio()`:

```python
# Available voices: af_heart (default), af_sky, am_adam, bf_emma, bm_george
for _, _, audio in pipeline(chunk, voice="af_heart", speed=1.0):
```

---

## 📁 Project structure

```text
mdtoaudio/
├── mdtoaudio.py                  # the whole tool — single script
├── tests/
│   ├── test_clean_text.py        # 19 tests — markdown cleaning
│   ├── test_chunk_text.py        # 8 tests  — paragraph chunking
│   ├── test_embed_audio.py       # 7 tests  — audio embedding
│   ├── test_convert_audio.py     # 3 tests  — TTS (mocked)
│   ├── test_ask_mode.py          # 9 tests  — terminal menu navigation
│   ├── test_collect_md_files.py  # 10 tests — recursive file discovery
│   └── test_process_file.py      # 10 tests — single-file pipeline
├── docs/
│   └── superpowers/
│       ├── specs/                # design spec
│       └── plans/                # implementation plan
├── .env                          # HF_TOKEN (gitignored)
├── .env.example
├── pyproject.toml
└── uv.lock
```

---

## 🔬 How it works

<details>
<summary><b>⌨️ _read_key() / ask_mode()</b> — live arrow-key terminal menu</summary>
<br />

`_read_key()` reads one raw keypress and returns a normalised string (`"up"`, `"down"`, `"enter"`, `"cancel"`, `"other"`). On Windows it uses `msvcrt.getch()`; on Unix it sets stdin to raw mode via `termios`/`tty`. Also handles `j`/`k` (vim-style) and `Ctrl-C`.

`ask_mode()` renders a live menu using ANSI escape codes. The selected option is highlighted in bold cyan with a `▶` cursor and redraws in-place on each keypress. On Windows, ANSI processing is enabled via `SetConsoleMode` before first render.

</details>

<details>
<summary><b>📁 collect_md_files() / process_file()</b> — folder mode</summary>
<br />

`collect_md_files()` walks the directory tree with `os.walk`, collects all `.md` files (case-insensitive), and returns them sorted.

`process_file()` runs the full pipeline for one file: read → `clean_text` → `chunk_text` → `convert_to_audio` → `embed_audio`. Files that produce no readable text after cleaning are silently skipped — processing continues rather than exiting.

</details>

<details>
<summary><b>🧹 clean_text(content)</b> — strips Obsidian syntax → clean prose</summary>
<br />

Applies regex transformations in order: frontmatter → Dataview/Templater blocks → inline Templater → code fences (content kept) → inline backticks (content kept) → embedded files → wiki links → HTML → Obsidian emoji → bold/italic → headers → tables → horizontal rules → whitespace normalization.

**Tables** are converted to spoken lines rather than stripped: each row's cells are comma-joined and terminated with a period. Separator rows (`|---|---|`) are dropped silently.

Underscore italic stripping uses word-boundary guards (`(?<!\w)_(.+?)_(?!\w)`) so `snake_case_identifiers` are never mangled.

</details>

<details>
<summary><b>✂️ chunk_text(text, max_chars=1000)</b> — splits long notes for TTS</summary>
<br />

Splits on `\n\n` paragraph boundaries. Accumulates paragraphs into chunks up to `max_chars`. A single paragraph longer than `max_chars` stays as one chunk — it cannot be split further without breaking sentences. This prevents Kokoro from failing or degrading on very long inputs.

</details>

<details>
<summary><b>🎙️ convert_to_audio(chunks, out_path)</b> — runs Kokoro TTS</summary>
<br />

Instantiates `KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")` once, then calls it once per chunk with `voice="af_heart"`. Each call yields `(graphemes, phonemes, audio)` tuples — arrays are collected, concatenated into a single numpy array, and written as a 24 kHz WAV via `soundfile`.

</details>

<details>
<summary><b>📎 embed_audio(md_path, audio_path)</b> — inserts Obsidian audio embed</summary>
<br />

Extracts any YAML frontmatter first. Strips any existing audio embed from the top of the body (handles re-runs cleanly). Re-assembles as `frontmatter + \n + ![[note.wav]] + \n\n + body`. This ensures Obsidian's Properties panel is never broken — the embed always lands after the closing `---`.

</details>

<details>
<summary><b>🩹 Kokoro warning patches</b> — applied before import, survive venv recreation</summary>
<br />

Kokoro 0.9.4 ships with two upstream bugs that produce noisy warnings:

1. Uses deprecated `torch.nn.utils.weight_norm` → patched by replacing it with `torch.nn.utils.parametrizations.weight_norm` before kokoro is imported.

2. Passes `dropout=0.2` to `nn.LSTM(num_layers=1)` → patched by wrapping `nn.LSTM.__init__` to drop the `dropout` kwarg when `num_layers=1`, where it has no effect anyway.

Both patches live in `mdtoaudio.py` (tracked in git) so they apply automatically on every machine after `uv sync` — no manual venv patching needed.

</details>

---

## 🧪 Running tests

```bash
uv run pytest tests/ -v
```

```text
66 passed in 2.7s
```

---

## 🛠️ Tech stack

| | |
| --- | --- |
| [Kokoro-82M](https://huggingface.co/hexgrad/Kokoro-82M) | State-of-the-art open-source TTS, 82M params, runs locally |
| [uv](https://docs.astral.sh/uv/) | Fast Python package and project manager |
| [soundfile](https://python-soundfile.readthedocs.io/) | WAV writing from numpy arrays |
| [python-dotenv](https://github.com/theskumar/python-dotenv) | `.env` file loading |
| `ctypes` / `msvcrt` (stdlib, Win32) | Native dialogs, ANSI console mode, raw keypresses |
| `termios` / `tty` (stdlib, Unix) | Raw keypress reading for terminal menu |
| kdialog / zenity / tkinter | Native file/folder pickers on Linux: KDE → GTK → fallback |

---

<div align="center">

<img src="https://capsule-render.vercel.app/api?type=waving&color=gradient&customColorList=6,11,20&height=100&section=footer" alt="mdtoaudio footer" />

</div>
