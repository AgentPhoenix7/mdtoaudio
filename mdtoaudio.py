import os
import re
import sys
import tkinter as tk
from tkinter import filedialog

import numpy as np
import soundfile as sf
from kokoro import KPipeline

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
    pass


def embed_audio(md_path: str, audio_path: str) -> None:
    audio_filename = os.path.basename(audio_path)
    embed_line = f"![[{audio_filename}]]"

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    # Remove any existing audio embed at the top of the file
    content = re.sub(
        r"^!\[\[.*?\.(wav|mp3|ogg|m4a)\]\]\n?",
        "",
        content,
    )
    content = content.lstrip("\n")

    content = embed_line + "\n\n" + content

    with open(md_path, "w", encoding="utf-8") as f:
        f.write(content)


def pick_file() -> str | None:
    pass


def main() -> None:
    pass


if __name__ == "__main__":
    main()
