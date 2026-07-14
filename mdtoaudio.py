import os
import re
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
import torch
import torch.nn as _nn
import torch.nn.utils as _nn_utils
import torch.nn.utils.parametrizations as _parametrizations
from dotenv import load_dotenv

# Patch kokoro upstream bugs before import so fixes survive venv recreation:
# 1. Replace deprecated weight_norm with the current parametrizations API
_nn_utils.weight_norm = _parametrizations.weight_norm
# 2. LSTM with num_layers=1 ignores dropout but PyTorch still warns about it
_orig_lstm_init = _nn.LSTM.__init__
def _patched_lstm_init(self, *args, **kwargs):
    if kwargs.get("num_layers", args[2] if len(args) > 2 else 1) == 1:
        kwargs.pop("dropout", None)
    _orig_lstm_init(self, *args, **kwargs)
_nn.LSTM.__init__ = _patched_lstm_init

from kokoro import KPipeline

load_dotenv()

VAULT_PATH = r"D:\Drive Vault" if sys.platform == "win32" else "/run/media/agntdrgn/Expansion/Drive Vault/"
SAMPLE_RATE = 24000


def _humanize_emoji(match: re.Match) -> str:
    name = match.group(1)
    prefixes = ("Li", "Cu", "Lu", "Fa", "Md", "Io", "Bs", "Ri", "Ti", "Si", "Bi", "Hi", "Fi", "Ai")
    for prefix in prefixes:
        if name.startswith(prefix) and len(name) > 2 and name[2].isupper():
            name = name[2:]
            break
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", name)


def clean_text(content: str) -> str:
    # Strip YAML frontmatter
    content = re.sub(r"^---\n.*?\n---\n?", "", content, flags=re.DOTALL)

    # Strip dataviewjs / dataview / templater code blocks entirely
    content = re.sub(
        r"```(?:dataviewjs|dataview|templater)\n.*?```",
        "",
        content,
        flags=re.DOTALL | re.IGNORECASE,
    )

    # Strip Templater inline syntax
    content = re.sub(r"<%.*?%>", "", content, flags=re.DOTALL)

    # Keep regular code block content (strip backtick fences + language tag)
    content = re.sub(r"```(?:\w+)?\n?(.*?)```", r"\1", content, flags=re.DOTALL)

    # Strip inline code backtick markers, keep inner text
    content = re.sub(r"`(.+?)`", r"\1", content)

    # Strip embedded files ![[...]]
    content = re.sub(r"!\[\[.*?\]\]", "", content)

    # Wiki links: [[link|alias]] → alias, [[link]] → link
    content = re.sub(r"\[\[(?:[^\]|]*\|)?([^\]]+)\]\]", r"\1", content)

    # Strip HTML tags
    content = re.sub(r"<[^>]+>", "", content)

    # Obsidian emoji → humanized name
    content = re.sub(r":([A-Za-z][A-Za-z0-9]+):", _humanize_emoji, content)

    # Strip bold/italic (order: *** → ** → *)
    content = re.sub(r"\*\*\*(.+?)\*\*\*", r"\1", content)
    content = re.sub(r"\*\*(.+?)\*\*", r"\1", content)
    content = re.sub(r"\*(.+?)\*", r"\1", content)
    content = re.sub(r"(?<!\w)__(.+?)__(?!\w)", r"\1", content)
    content = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"\1", content)

    # Strip header markers, keep text
    content = re.sub(r"^#{1,6}\s+", "", content, flags=re.MULTILINE)

    # Strip curly braces (Dataview/Templater/LaTeX leftovers) — Kokoro's G2P
    # tags them the same as parentheses, and an orphaned closing brace turns
    # into an unpaired ")" phoneme that the TTS model mispronounces as a
    # stray sound
    content = re.sub(r"[{}]", "", content)

    # Convert tables to spoken lines: headers row, then each data row, cells comma-joined
    def _table_to_speech(text: str) -> str:
        lines = text.split("\n")
        result = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if re.match(r"^\|.*\|$", line):
                cells = [c.strip() for c in line.strip("|").split("|")]
                cells = [c for c in cells if c]
                # Skip separator rows (---|--- style)
                if not all(re.match(r"^[-: ]+$", c) for c in cells):
                    result.append(", ".join(cells) + ".")
            else:
                result.append(line)
            i += 1
        return "\n".join(result)

    content = _table_to_speech(content)

    # Strip standalone horizontal rules
    content = re.sub(r"^---+$", "", content, flags=re.MULTILINE)

    # Normalize whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)

    return content.strip()


def chunk_text(text: str, max_chars: int = 1000) -> list[str]:
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current: list[str] = []
    current_len = 0

    for para in paragraphs:
        if current and current_len + len(para) > max_chars:
            chunks.append("\n\n".join(current))
            current = [para]
            current_len = len(para)
        else:
            current.append(para)
            current_len += len(para)

    if current:
        chunks.append("\n\n".join(current))

    return chunks


def convert_to_audio(chunks: list[str], out_path: str) -> None:
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Using device: {device}")
    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M", device=device)
    audio_parts: list[np.ndarray] = []

    for i, chunk in enumerate(chunks, 1):
        print(f"Generating audio (chunk {i}/{len(chunks)})...")
        for _, _, audio in pipeline(chunk, voice="af_heart", speed=1.0):
            audio_parts.append(np.asarray(audio))

    audio = np.concatenate(audio_parts)
    sf.write(out_path, audio, SAMPLE_RATE)


def embed_audio(md_path: str, audio_path: str) -> None:
    audio_filename = os.path.basename(audio_path)
    embed_line = f"![[{audio_filename}]]"

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract frontmatter if present
    frontmatter = ""
    body = content
    frontmatter_match = re.match(r"^(---\n.*?\n---\n?)", content, flags=re.DOTALL)
    if frontmatter_match:
        frontmatter = frontmatter_match.group(1)
        body = content[len(frontmatter):]

    # Strip any existing audio embed from the top of the body
    body = body.lstrip("\n")
    body = re.sub(r"^!\[\[.*?\.(wav|mp3|ogg|m4a)\]\]\n\n?", "", body)
    body = body.lstrip("\n")

    if frontmatter:
        content = frontmatter + "\n" + embed_line + "\n\n" + body
    else:
        content = embed_line + "\n\n" + body

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)


def _read_key() -> str:
    """Read one keypress from stdin. Returns 'up', 'down', 'enter', 'cancel', or 'other'."""
    platform = sys.platform
    if platform == "win32":
        import msvcrt
        key = msvcrt.getch()
        if key == b'\xe0':
            key2 = msvcrt.getch()
            if key2 == b'H': return "up"
            if key2 == b'P': return "down"
            return "other"
        if key in (b'\r', b'\n'): return "enter"
        if key in (b'q', b'Q', b'\x03'): return "cancel"
        if key == b'k': return "up"
        if key == b'j': return "down"
        return "other"
    else:
        import termios
        import tty
        import select as _select
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)  # type: ignore[attr-defined]
        try:
            tty.setraw(fd)  # type: ignore[attr-defined]
            ch = sys.stdin.read(1)
            if ch == '\x1b' and _select.select([sys.stdin], [], [], 0.05)[0]:
                ch += sys.stdin.read(2)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)  # type: ignore[attr-defined]
        if ch in ('\r', '\n'): return "enter"
        if ch in ('q', 'Q', '\x03'): return "cancel"
        if ch == 'k': return "up"
        if ch == 'j': return "down"
        if ch == '\x1b[A': return "up"
        if ch == '\x1b[B': return "down"
        return "other"


def ask_mode() -> str | None:
    """Arrow-key terminal menu. Returns 'file', 'folder', or None (cancelled)."""
    options = [("file", "Single file"), ("folder", "Entire folder (recursive)")]
    selected = 0

    if sys.platform == "win32":
        try:
            import ctypes
            handle = ctypes.windll.kernel32.GetStdHandle(-11)
            mode = ctypes.c_ulong()
            if ctypes.windll.kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                ctypes.windll.kernel32.SetConsoleMode(handle, mode.value | 0x0004)
        except Exception:
            pass

    def _render(first: bool = False) -> None:
        lines = ["", "  Select mode:", ""]
        for i, (_, label) in enumerate(options):
            if i == selected:
                lines.append(f"  \033[1;36m▶ {label}\033[0m")
            else:
                lines.append(f"    {label}")
        lines.append("")
        lines.append("  ↑↓ / j k  navigate   Enter  confirm   q  quit")
        if not first:
            sys.stdout.write(f"\033[{len(lines)}A")
        for line in lines:
            sys.stdout.write(f"\r\033[2K{line}\n")
        sys.stdout.flush()

    _render(first=True)

    while True:
        key = _read_key()
        if key == "up":
            selected = (selected - 1) % len(options)
            _render()
        elif key == "down":
            selected = (selected + 1) % len(options)
            _render()
        elif key == "enter":
            return options[selected][0]
        elif key == "cancel":
            return None


def _pick_file_win32() -> str | None:
    import ctypes
    from ctypes import wintypes

    OFN_PATHMUSTEXIST = 0x00000800
    OFN_FILEMUSTEXIST = 0x00001000

    class OPENFILENAMEW(ctypes.Structure):
        _fields_ = [
            ("lStructSize", wintypes.DWORD),
            ("hwndOwner", wintypes.HWND),
            ("hInstance", wintypes.HINSTANCE),
            ("lpstrFilter", wintypes.LPCWSTR),
            ("lpstrCustomFilter", ctypes.c_void_p),
            ("nMaxCustFilter", wintypes.DWORD),
            ("nFilterIndex", wintypes.DWORD),
            ("lpstrFile", ctypes.c_void_p),
            ("nMaxFile", wintypes.DWORD),
            ("lpstrFileTitle", ctypes.c_void_p),
            ("nMaxFileTitle", wintypes.DWORD),
            ("lpstrInitialDir", wintypes.LPCWSTR),
            ("lpstrTitle", wintypes.LPCWSTR),
            ("Flags", wintypes.DWORD),
            ("nFileOffset", wintypes.WORD),
            ("nFileExtension", wintypes.WORD),
            ("lpstrDefExt", wintypes.LPCWSTR),
            ("lCustData", wintypes.LPARAM),
            ("lpfnHook", ctypes.c_void_p),
            ("lpTemplateName", ctypes.c_void_p),
            ("pvReserved", ctypes.c_void_p),
            ("dwReserved", wintypes.DWORD),
            ("FlagsEx", wintypes.DWORD),
        ]

    buf = ctypes.create_unicode_buffer(32768)
    ofn = OPENFILENAMEW()
    ofn.lStructSize = ctypes.sizeof(OPENFILENAMEW)
    ofn.lpstrFilter = "Markdown files\0*.md\0\0"
    ofn.lpstrFile = ctypes.addressof(buf)
    ofn.nMaxFile = len(buf)
    ofn.lpstrInitialDir = VAULT_PATH
    ofn.lpstrTitle = "Select a note to convert"
    ofn.Flags = OFN_PATHMUSTEXIST | OFN_FILEMUSTEXIST

    if ctypes.windll.comdlg32.GetOpenFileNameW(ctypes.byref(ofn)):
        return ctypes.wstring_at(ctypes.addressof(buf))
    return None


def pick_file() -> str | None:
    if sys.platform == "win32":
        return _pick_file_win32()

    if shutil.which("kdialog"):
        result = subprocess.run(
            ["kdialog", "--getopenfilename", VAULT_PATH, "*.md", "--title", "Select a note to convert"],
            capture_output=True,
            text=True,
        )
        path = result.stdout.strip()
        return path if path else None

    if shutil.which("zenity"):
        result = subprocess.run(
            ["zenity", "--file-selection", "--title=Select a note to convert",
             f"--filename={VAULT_PATH}", "--file-filter=Markdown files | *.md"],
            capture_output=True,
            text=True,
        )
        path = result.stdout.strip()
        return path if path else None

    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        initialdir=VAULT_PATH,
        title="Select a note to convert",
        filetypes=[("Markdown files", "*.md")],
    )
    root.destroy()
    return path or None


def _pick_folder_win32() -> str | None:
    import ctypes
    from ctypes import wintypes

    BIF_RETURNONLYFSDIRS = 0x0001
    BIF_NEWDIALOGSTYLE = 0x0040

    class BROWSEINFOW(ctypes.Structure):
        _fields_ = [
            ("hwndOwner", wintypes.HWND),
            ("pidlRoot", ctypes.c_void_p),
            ("pszDisplayName", ctypes.c_void_p),
            ("lpszTitle", wintypes.LPCWSTR),
            ("ulFlags", wintypes.UINT),
            ("lpfn", ctypes.c_void_p),
            ("lParam", wintypes.LPARAM),
            ("iImage", ctypes.c_int),
        ]

    shell32 = ctypes.windll.shell32
    shell32.SHBrowseForFolderW.restype = ctypes.c_void_p
    shell32.SHGetPathFromIDListW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p]
    shell32.SHGetPathFromIDListW.restype = ctypes.c_bool
    shell32.ILCreateFromPathW.restype = ctypes.c_void_p
    shell32.ILCreateFromPathW.argtypes = [wintypes.LPCWSTR]
    shell32.ILFree.restype = None
    shell32.ILFree.argtypes = [ctypes.c_void_p]
    ole32 = ctypes.windll.ole32
    ole32.CoInitialize.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.argtypes = [ctypes.c_void_p]
    ole32.CoTaskMemFree.restype = None
    ole32.CoInitialize(None)

    pidl_root = shell32.ILCreateFromPathW(VAULT_PATH)

    display_name = ctypes.create_unicode_buffer(260)
    bi = BROWSEINFOW()
    bi.pidlRoot = pidl_root
    bi.pszDisplayName = ctypes.addressof(display_name)
    bi.lpszTitle = "Select a folder to convert (recursive)"
    bi.ulFlags = BIF_RETURNONLYFSDIRS | BIF_NEWDIALOGSTYLE

    pidl = shell32.SHBrowseForFolderW(ctypes.byref(bi))

    if pidl_root:
        shell32.ILFree(pidl_root)

    if not pidl:
        return None

    path_buf = ctypes.create_unicode_buffer(32768)
    result = shell32.SHGetPathFromIDListW(pidl, path_buf)
    ole32.CoTaskMemFree(pidl)
    return path_buf.value if result else None


def pick_folder() -> str | None:
    platform = sys.platform
    if platform == "win32":
        return _pick_folder_win32()
    else:
        if shutil.which("kdialog"):
            result = subprocess.run(
                ["kdialog", "--getexistingdirectory", VAULT_PATH, "--title", "Select a folder to convert"],
                capture_output=True,
                text=True,
            )
            path = result.stdout.strip()
            return path if path else None

        if shutil.which("zenity"):
            result = subprocess.run(
                ["zenity", "--file-selection", "--directory",
                 f"--filename={VAULT_PATH}", "--title=Select a folder to convert"],
                capture_output=True,
                text=True,
            )
            path = result.stdout.strip()
            return path if path else None

        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askdirectory(initialdir=VAULT_PATH, title="Select a folder to convert")
        root.destroy()
        return path or None


def collect_md_files(folder: str) -> list[str]:
    md_files = []
    for root, _, files in os.walk(folder):
        for f in files:
            if f.lower().endswith(".md"):
                md_files.append(os.path.join(root, f))
    return sorted(md_files)


def process_file(md_path: str) -> None:
    print(f"Processing: {md_path}")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    text = clean_text(content)
    if not text.strip():
        print(f"  Skipping (no readable text): {md_path}")
        return
    chunks = chunk_text(text)
    audio_path = os.path.splitext(md_path)[0] + ".wav"
    convert_to_audio(chunks, audio_path)
    embed_audio(md_path, audio_path)
    print(f"  Done → {audio_path}")


def main() -> None:
    mode = ask_mode()
    if mode is None:
        print("Cancelled. Exiting.")
        sys.exit(0)

    if mode == "file":
        md_path = pick_file()
        if not md_path:
            print("No file selected. Exiting.")
            sys.exit(0)
        process_file(md_path)
    else:
        folder = pick_folder()
        if not folder:
            print("No folder selected. Exiting.")
            sys.exit(0)
        md_files = collect_md_files(folder)
        if not md_files:
            print("No markdown files found in selected folder.")
            sys.exit(1)
        print(f"Found {len(md_files)} markdown file(s). Starting conversion...")
        for md_path in md_files:
            process_file(md_path)
        print(f"\nAll done. Processed {len(md_files)} file(s).")


if __name__ == "__main__":
    main()
