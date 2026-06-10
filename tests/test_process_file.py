import os
from unittest.mock import patch
from mdtoaudio import process_file


def test_convert_and_embed_called_for_normal_file(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("# Hello\nSome content here.")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio") as mock_embed:
        process_file(str(md_file))

    mock_convert.assert_called_once()
    mock_embed.assert_called_once()


def test_audio_path_is_wav_sibling(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("Some content.")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio"):
        process_file(str(md_file))

    audio_path = mock_convert.call_args[0][1]
    assert audio_path == str(tmp_path / "note.wav")


def test_audio_placed_in_same_directory_as_md(tmp_path):
    sub = tmp_path / "subdir"
    sub.mkdir()
    md_file = sub / "note.md"
    md_file.write_text("Content here.")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio"):
        process_file(str(md_file))

    audio_path = mock_convert.call_args[0][1]
    assert os.path.dirname(audio_path) == str(sub)


def test_embed_receives_correct_md_and_audio_paths(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("Some content.")

    with patch("mdtoaudio.convert_to_audio"), \
         patch("mdtoaudio.embed_audio") as mock_embed:
        process_file(str(md_file))

    md_arg, audio_arg = mock_embed.call_args[0]
    assert md_arg == str(md_file)
    assert audio_arg == str(tmp_path / "note.wav")


def test_skips_frontmatter_only_file(tmp_path):
    md_file = tmp_path / "empty.md"
    md_file.write_text("---\ntitle: test\nauthor: me\n---\n")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio") as mock_embed:
        process_file(str(md_file))

    mock_convert.assert_not_called()
    mock_embed.assert_not_called()


def test_skips_completely_blank_file(tmp_path):
    md_file = tmp_path / "blank.md"
    md_file.write_text("   \n\n   \n")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio") as mock_embed:
        process_file(str(md_file))

    mock_convert.assert_not_called()
    mock_embed.assert_not_called()


def test_skips_whitespace_only_after_clean(tmp_path):
    md_file = tmp_path / "noise.md"
    md_file.write_text("![[embed.png]]\n\n![[embed2.png]]")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio") as mock_embed:
        process_file(str(md_file))

    mock_convert.assert_not_called()
    mock_embed.assert_not_called()


def test_chunks_preserve_full_content(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("Paragraph one.\n\nParagraph two.")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio"):
        process_file(str(md_file))

    chunks = mock_convert.call_args[0][0]
    full_text = " ".join(chunks)
    assert "Paragraph one" in full_text
    assert "Paragraph two" in full_text


def test_chunks_passed_as_list(tmp_path):
    md_file = tmp_path / "note.md"
    md_file.write_text("Hello world.")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio"):
        process_file(str(md_file))

    chunks = mock_convert.call_args[0][0]
    assert isinstance(chunks, list)
    assert len(chunks) >= 1


def test_stem_preserved_in_audio_filename(tmp_path):
    md_file = tmp_path / "my-note-2024.md"
    md_file.write_text("Content.")

    with patch("mdtoaudio.convert_to_audio") as mock_convert, \
         patch("mdtoaudio.embed_audio"):
        process_file(str(md_file))

    audio_path = mock_convert.call_args[0][1]
    assert os.path.basename(audio_path) == "my-note-2024.wav"
