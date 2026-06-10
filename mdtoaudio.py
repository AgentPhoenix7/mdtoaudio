import os
import re
import shutil
import subprocess
import sys

import numpy as np
import soundfile as sf
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

VAULT_PATH = "/run/media/agntdrgn/Expansion/Drive Vault/"
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

    # Strip table rows (lines starting and ending with |) and separator rows
    content = re.sub(r"^\|.*\|$", "", content, flags=re.MULTILINE)
    content = re.sub(r"^[-|: ]+$", "", content, flags=re.MULTILINE)

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
    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    audio_parts: list[np.ndarray] = []

    for i, chunk in enumerate(chunks, 1):
        print(f"Generating audio (chunk {i}/{len(chunks)})...")
        for _, _, audio in pipeline(chunk, voice="af_heart", speed=1.0):
            audio_parts.append(audio)

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


def pick_file() -> str | None:
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


def main() -> None:
    md_path = pick_file()
    if not md_path:
        print("No file selected. Exiting.")
        sys.exit(0)

    print(f"Selected: {md_path}")

    print("Cleaning text...")
    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()
    text = clean_text(content)

    if not text.strip():
        print("No readable text found after cleaning. Exiting.")
        sys.exit(1)

    chunks = chunk_text(text)
    stem = os.path.splitext(md_path)[0]
    audio_path = stem + ".wav"

    convert_to_audio(chunks, audio_path)

    print("Embedding audio in note...")
    embed_audio(md_path, audio_path)

    print(f"Done → {audio_path}")


if __name__ == "__main__":
    main()
