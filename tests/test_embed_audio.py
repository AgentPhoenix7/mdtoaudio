import pytest
from mdtoaudio import embed_audio


def test_embeds_audio_at_top_of_note(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("# Hello\nWorld content here")
    audio_file = tmp_path / "note.wav"
    audio_file.touch()

    embed_audio(str(md_file), str(audio_file))

    content = md_file.read_text()
    assert content.startswith("![[note.wav]]")


def test_preserves_original_note_body(tmp_path):
    md_file = tmp_path / "note.md"
    original = "# Hello\nWorld content here"
    md_file.write_text(original)
    audio_file = tmp_path / "note.wav"
    audio_file.touch()

    embed_audio(str(md_file), str(audio_file))

    content = md_file.read_text()
    assert "# Hello" in content
    assert "World content here" in content


def test_replaces_existing_wav_embed(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("![[old.wav]]\n\n# Hello\nWorld")
    audio_file = tmp_path / "note.wav"
    audio_file.touch()

    embed_audio(str(md_file), str(audio_file))

    content = md_file.read_text()
    assert "![[old.wav]]" not in content
    assert content.startswith("![[note.wav]]")


def test_replaces_existing_mp3_embed(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("![[note.mp3]]\n\n# Hello\nWorld")
    audio_file = tmp_path / "note.wav"
    audio_file.touch()

    embed_audio(str(md_file), str(audio_file))

    content = md_file.read_text()
    assert "![[note.mp3]]" not in content
    assert content.startswith("![[note.wav]]")


def test_embed_separated_from_body_by_blank_line(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("# Hello\nWorld")
    audio_file = tmp_path / "note.wav"
    audio_file.touch()

    embed_audio(str(md_file), str(audio_file))

    content = md_file.read_text()
    assert content.startswith("![[note.wav]]\n\n")
