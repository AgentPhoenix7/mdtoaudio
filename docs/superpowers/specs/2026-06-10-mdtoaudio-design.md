# mdtoaudio — Design Spec

**Date:** 2026-06-10  
**Last updated:** 2026-06-10  
**Status:** Current

## Overview

A single Python script (`mdtoaudio.py`) that converts Obsidian markdown notes into natural-sounding audio files using Kokoro TTS, then embeds the audio back into each note as an Obsidian-native voiceover.

The tool is invoked manually. An arrow-key terminal menu lets the user choose between converting a single file or an entire folder recursively. Native OS dialogs then open for path selection. No bulk scheduling, no watch mode, no automation.

## Usage

```bash
uv run mdtoaudio.py
```

A terminal menu appears:

```text
  Select mode:

  ▶ Single file
    Entire folder (recursive)

  ↑↓ / j k  navigate   Enter  confirm   q  quit
```

After confirming the mode, an OS-native dialog opens for file or folder selection, rooted at `VAULT_PATH`.

## Vault

- **Windows path:** `D:\Drive Vault`
- **Linux path:** `/run/media/agntdrgn/Expansion/Drive Vault/`
- `VAULT_PATH` is set at import time based on `sys.platform`.
- Both the file picker and folder picker open rooted at `VAULT_PATH`.

## Internal Functions

```text
mdtoaudio.py
├── _read_key()                      → reads one raw keypress; returns 'up'/'down'/'enter'/'cancel'/'other'
├── ask_mode()                       → arrow-key terminal menu; returns 'file' or 'folder' or None
│
├── _pick_file_win32()               → Win32 GetOpenFileNameW dialog (markdown filter, VAULT_PATH root)
├── pick_file()                      → cross-platform: Win32 → kdialog → zenity → tkinter
│
├── _pick_folder_win32()             → Win32 SHBrowseForFolderW dialog (VAULT_PATH as pidlRoot)
├── pick_folder()                    → cross-platform: Win32 → kdialog → zenity → tkinter
│
├── collect_md_files(folder)         → os.walk recursion; returns sorted list of .md paths
│
├── clean_text(md_content)           → produces clean prose for TTS
├── chunk_text(text)                 → splits cleaned text into paragraph-based chunks ≤ 1000 chars
├── convert_to_audio(chunks, out)    → converts each chunk via Kokoro, concatenates, writes .wav
├── embed_audio(md_path, audio)      → inserts/replaces ![[note.wav]] at top of .md
│
├── process_file(md_path)            → clean → chunk → convert → embed for a single file
└── main()                           → ask_mode → pick → process_file (×1 or ×N)
```

## Mode Selection

On launch, `ask_mode()` renders a live terminal menu using ANSI escape codes. The cursor and highlight redraw in-place on each keypress — no screen clears.

- **↑ / k** — move up
- **↓ / j** — move down
- **Enter** — confirm selection
- **q / Ctrl-C** — cancel (exits)

On Windows, ANSI processing is enabled via `SetConsoleMode` before rendering.  
On Unix, raw mode is set via `termios`/`tty` for each keypress, then restored.

## File Picker

`pick_file()` opens a native OS dialog filtered to `*.md`, rooted at `VAULT_PATH`:

- **Windows** — `GetOpenFileNameW` via `ctypes` (no tkinter dependency)
- **Linux with kdialog** — `kdialog --getopenfilename`
- **Linux with zenity** — `zenity --file-selection`
- **Fallback** — `tkinter.filedialog.askopenfilename`

## Folder Picker

`pick_folder()` opens a native OS directory browser rooted at `VAULT_PATH`:

- **Windows** — `SHBrowseForFolderW` via `ctypes`, with `pidlRoot` set to `VAULT_PATH` via `ILCreateFromPathW` (restricts browser to within the vault)
- **Linux with kdialog** — `kdialog --getexistingdirectory`
- **Linux with zenity** — `zenity --file-selection --directory`
- **Fallback** — `tkinter.filedialog.askdirectory`

## Folder Mode

When the user selects **Entire folder**, `collect_md_files(folder)` walks the tree recursively using `os.walk`, collecting all files whose extension is `.md` (case-insensitive). The list is sorted before processing.

Each file is passed to `process_file()`, which silently skips files that produce no readable text after cleaning (e.g. frontmatter-only or blank notes). Processing continues to the next file on skip — it does not exit.

## Text Cleaning Rules

| Element | Example | Action |
| --- | --- | --- |
| Frontmatter | `---\nnext: [[]]` | Strip entirely |
| Embedded files | `![[image.png]]` | Strip entirely |
| Wiki links | `[[My Note]]` | Keep link text → "My Note" |
| Wiki links with alias | `[[Note\|alias]]` | Keep alias text |
| Code blocks | ` ```sql ... ``` ` | Keep code text, strip fences |
| Inline code | `` `SELECT *` `` | Keep text, strip backticks |
| Dataview/dataviewjs blocks | ` ```dataviewjs ... ``` ` | Strip entirely |
| Templater syntax | `<% tp.file.cursor() %>` | Strip entirely |
| HTML tags | `<img src="...">` | Strip entirely |
| Obsidian emoji | `:LiBell:` `:CuLanguage:` | Convert to humanized name → "Bell", "Language" |
| Bold / italic | `**text**`, `*text*`, `_text_` | Keep text, strip markers |
| Headers | `## What you'll learn` | Keep text, strip `#` symbols |
| Tables | `\| Col \| Col \|` | Spoken as comma-joined lines (headers + each data row) |
| Horizontal rules | `---` | Strip |

**Table TTS example:** A markdown table like:

```markdown
| Name | Age |
|------|-----|
| Alice | 30 |
```

…is converted to:

```text
Name, Age.
Alice, 30.
```

Separator rows (`|---|---|`) are silently dropped.

**Obsidian emoji handling:** Strip the prefix (`Li`, `Cu`, `Lu`, `Fa`, `Md`, `Io`, `Bs`, `Ri`, `Ti`, `Si`, `Bi`, `Hi`, `Fi`, `Ai`) and the surrounding colons, then insert a space before each capital letter (e.g., `:LiCheckCircle:` → "Check Circle").

## Audio Output

- **Format:** `.wav` (Obsidian supports WAV natively; avoids ffmpeg dependency)
- **Location:** Same directory as the source `.md` file (preserves folder structure in folder mode)
- **Filename:** Same stem as the note (`What is Programming.md` → `What is Programming.wav`)
- **Sample rate:** 24000 Hz
- **TTS engine:** Kokoro-82M (`hexgrad/Kokoro-82M`), voice `af_heart`, speed `1.0`

## Audio Embedding

After generating the audio, the script inserts an Obsidian embed at the very top of the `.md` file:

```markdown
![[What is Programming.wav]]

# What Is Programming...
```

- If a frontmatter block is present, the embed is placed immediately after it.
- If an embed for any audio file (`.wav`, `.mp3`, `.ogg`, `.m4a`) already exists at the top → replace it.
- The rest of the note content is untouched.

## Progress Feedback

```text
Found 12 markdown file(s). Starting conversion...
Processing: D:\Drive Vault\04-Programming\...\What is Programming.md
  Generating audio (chunk 1/3)...
  Generating audio (chunk 2/3)...
  Generating audio (chunk 3/3)...
  Done → D:\Drive Vault\04-Programming\...\What is Programming.wav
Processing: D:\Drive Vault\...
  Skipping (no readable text): D:\Drive Vault\...\index.md
...
All done. Processed 12 file(s).
```

## Dependencies

| Package | Purpose |
| --- | --- |
| `kokoro` | Local natural-sounding TTS |
| `soundfile` | Write generated audio to `.wav` |
| `numpy` | Audio array concatenation |
| `python-dotenv` | Load `.env` if present |
| `ctypes` (stdlib) | Win32 native file/folder dialogs, console ANSI mode |
| `msvcrt` (stdlib, Win32) | Raw keypress reading for terminal menu |
| `termios` / `tty` (stdlib, Unix) | Raw keypress reading for terminal menu |
| `tkinter` (stdlib, fallback) | File/folder dialogs on Unix without kdialog/zenity |

Project is managed with `uv`:

```bash
uv add kokoro soundfile numpy python-dotenv
uv run mdtoaudio.py
```

## Kokoro Patches

Two upstream bugs are patched at import time before `from kokoro import KPipeline`:

1. `torch.nn.utils.weight_norm` is deprecated — replaced with `torch.nn.utils.parametrizations.weight_norm`
2. `LSTM(num_layers=1, dropout=...)` triggers a spurious PyTorch warning — the `dropout` kwarg is stripped when `num_layers == 1`

## Error Handling

- User cancels mode menu → exit silently
- User cancels file/folder picker → exit silently
- No markdown files found in selected folder → print message and exit
- File produces no readable text after cleaning → skip with a message, continue to next file
- File is blank or frontmatter-only → skip silently

## Non-Goals

- No watch mode
- No cloud TTS APIs
- No Docker
- No scheduling or automation
- No GUI beyond the native OS pickers
