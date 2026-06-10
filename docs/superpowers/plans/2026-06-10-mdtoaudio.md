# mdtoaudio Implementation Plan

**Goal:** A single Python script that presents a terminal mode-selection menu, opens a native OS file or folder picker rooted at the vault, converts selected Obsidian markdown note(s) to WAV audio via Kokoro TTS, and embeds the audio back into each note.

**Architecture:** `mdtoaudio.py` — one file, all logic. Independently testable functions orchestrated by `main()`. Tests live in `tests/`.

**Tech Stack:** Python 3.11+, uv, kokoro, soundfile, numpy, python-dotenv, pytest

---

## File Map

| File | Purpose |
| --- | --- |
| `mdtoaudio.py` | Main script — all logic lives here |
| `tests/test_clean_text.py` | Unit tests for `clean_text()` |
| `tests/test_chunk_text.py` | Unit tests for `chunk_text()` |
| `tests/test_embed_audio.py` | Unit tests for `embed_audio()` |
| `tests/test_convert_audio.py` | Unit tests for `convert_to_audio()` (mocked) |
| `tests/test_ask_mode.py` | Unit tests for `ask_mode()` (patching `_read_key`) |
| `tests/test_collect_md_files.py` | Unit tests for `collect_md_files()` |
| `tests/test_process_file.py` | Unit tests for `process_file()` (mocked) |
| `pyproject.toml` | Managed by `uv`, tracks deps and pytest config |
| `conftest.py` | Marks project root for pytest imports |

---

## Task 1: Project Setup ✅

- [x] Install system dependency `espeak-ng` (Linux)
- [x] Initialize uv project, add `kokoro soundfile numpy python-dotenv`, add `--dev pytest`
- [x] Configure `[tool.pytest.ini_options] pythonpath = ["."]` in `pyproject.toml`
- [x] Create `conftest.py` and `tests/__init__.py`
- [x] Create `mdtoaudio.py` skeleton

---

## Task 2: Implement `clean_text()` ✅

**Key cleaning rules:**
- Strip YAML frontmatter, embedded files, dataview/templater blocks, HTML tags
- Resolve wiki links to their display text
- Strip bold/italic/header markers (keep text)
- Convert Obsidian emoji (`:LiBell:` → "Bell") via `_humanize_emoji`
- Tables: spoken as comma-joined lines — headers row, then each data row; separator rows dropped
- Strip horizontal rules
- Normalize excess whitespace

**Tests:** `tests/test_clean_text.py` — 19 tests covering all cleaning rules including table TTS behaviour.

---

## Task 3: Implement `chunk_text()` ✅

Splits cleaned text at paragraph boundaries (`\n\n`). Combines short paragraphs greedily up to `max_chars=1000`. A single paragraph longer than `max_chars` stays as one chunk (cannot be split further).

**Tests:** `tests/test_chunk_text.py` — 8 tests.

---

## Task 4: Implement `embed_audio()` ✅

Inserts `![[note.wav]]` at the top of the `.md` file (after frontmatter if present). Replaces any existing audio embed (`.wav`, `.mp3`, `.ogg`, `.m4a`) rather than duplicating. Body content is untouched.

**Tests:** `tests/test_embed_audio.py` — 7 tests covering insert, replace, frontmatter preservation.

---

## Task 5: Implement `convert_to_audio()` ✅

Loads `KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")`. Iterates chunks, calling `pipeline(chunk, voice="af_heart", speed=1.0)`. Appends each audio segment as a numpy array. Concatenates and writes via `soundfile`.

Two Kokoro bugs patched at import time (before `from kokoro import KPipeline`):
1. `weight_norm` deprecation — replaced with `parametrizations.weight_norm`
2. `LSTM(num_layers=1, dropout=...)` spurious warning — `dropout` kwarg stripped when `num_layers == 1`

**Tests:** `tests/test_convert_audio.py` — 3 tests (mocked KPipeline).

---

## Task 6: Implement `_read_key()` and `ask_mode()` ✅

`_read_key()` reads one raw keypress and returns a normalised string (`"up"`, `"down"`, `"enter"`, `"cancel"`, `"other"`):
- **Windows** — `msvcrt.getch()`; special keys prefixed with `\xe0`
- **Unix** — `termios`/`tty` raw mode; arrow keys as `\x1b[A`/`\x1b[B`
- Also handles `j`/`k` (vim-style) and `Ctrl-C`

`ask_mode()` renders a live arrow-key terminal menu via ANSI escape codes. The selected option is highlighted in bold cyan with a `▶` cursor. The menu redraws in-place on each keypress. On Windows, ANSI processing is enabled via `SetConsoleMode` before first render.

**Tests:** `tests/test_ask_mode.py` — 9 tests patching `mdtoaudio._read_key` with `side_effect` lists to exercise navigation, wrapping, cancel, and unknown-key handling.

---

## Task 7: Implement native OS pickers ✅

### File picker

`_pick_file_win32()` — `GetOpenFileNameW` via ctypes (`OPENFILENAMEW` struct), filtered to `*.md`, rooted at `VAULT_PATH`.

`pick_file()` — dispatches to: Win32 → `kdialog --getopenfilename` → `zenity --file-selection` → `tkinter.filedialog.askopenfilename`.

### Folder picker

`_pick_folder_win32()` — `SHBrowseForFolderW` via ctypes (`BROWSEINFOW` struct). `pidlRoot` set to `VAULT_PATH` via `ILCreateFromPathW`, restricting the browser to within the vault. All PIDLs freed with `ILFree` / `CoTaskMemFree`. All argtypes/restypes declared explicitly to handle 64-bit pointers correctly.

`pick_folder()` — dispatches to: Win32 → `kdialog --getexistingdirectory` → `zenity --file-selection --directory` → `tkinter.filedialog.askdirectory`.

Both pickers open rooted at `VAULT_PATH` (platform-aware: `D:\Drive Vault` on Windows, `/run/media/agntdrgn/Expansion/Drive Vault/` on Linux).

---

## Task 8: Implement folder mode ✅

`collect_md_files(folder)` — `os.walk` recursive scan, case-insensitive `.md` filter, sorted output.

`process_file(md_path)` — single-file pipeline: read → `clean_text` → `chunk_text` → `convert_to_audio` → `embed_audio`. Silently skips files with no readable text after cleaning.

`main()` updated:
1. `ask_mode()` — mode menu
2. `pick_file()` or `pick_folder()` — path selection
3. Single file → `process_file(path)` directly
4. Folder → `collect_md_files(folder)` then `process_file` for each, with count summary

**Tests:**
- `tests/test_collect_md_files.py` — 10 tests (empty folder, flat, non-md exclusion, deep recursion, sort, case-insensitive extension, absolute paths)
- `tests/test_process_file.py` — 10 tests (convert/embed called, audio path derivation, skip empty/blank/frontmatter-only, chunk content preservation)

---

## Test Summary

| File | Tests |
| --- | --- |
| `test_clean_text.py` | 19 |
| `test_chunk_text.py` | 8 |
| `test_embed_audio.py` | 7 |
| `test_convert_audio.py` | 3 |
| `test_ask_mode.py` | 9 |
| `test_collect_md_files.py` | 10 |
| `test_process_file.py` | 10 |
| **Total** | **66** |

All 66 tests pass on Python 3.14 / Windows 11.

---

## Known Constraints

- `termios`/`tty` imports are Unix-only; Pylance on Windows flags them as unknown attributes — suppressed with `# type: ignore[attr-defined]`.
- Pylance's `sys.platform` narrowing requires a local variable (`platform = sys.platform`) to prevent the non-win32 branch from being flagged as unreachable.
- `CoTaskMemFree` and `ILFree` must have explicit `argtypes = [ctypes.c_void_p]` to pass 64-bit PIDLs on 64-bit Windows without `OverflowError`.
