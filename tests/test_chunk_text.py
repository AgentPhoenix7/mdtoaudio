import pytest
from mdtoaudio import chunk_text


def test_single_short_paragraph():
    assert chunk_text("Hello world.") == ["Hello world."]


def test_empty_text_returns_empty_list():
    assert chunk_text("") == []


def test_whitespace_only_returns_empty_list():
    assert chunk_text("   \n\n   ") == []


def test_combines_short_paragraphs_into_one_chunk():
    text = "Short one.\n\nShort two.\n\nShort three."
    chunks = chunk_text(text, max_chars=1000)
    assert len(chunks) == 1
    assert "Short one." in chunks[0]
    assert "Short three." in chunks[0]


def test_splits_long_text_at_paragraph_boundary():
    para = "A" * 600
    text = f"{para}\n\n{para}"
    chunks = chunk_text(text, max_chars=1000)
    assert len(chunks) == 2


def test_ignores_blank_paragraphs():
    text = "First.\n\n\n\nSecond."
    chunks = chunk_text(text, max_chars=1000)
    assert len(chunks) == 1
    assert "First." in chunks[0]
    assert "Second." in chunks[0]


def test_very_long_single_paragraph_stays_as_one_chunk():
    # A single paragraph longer than max_chars cannot be split further
    para = "Word " * 300  # ~1500 chars
    chunks = chunk_text(para, max_chars=1000)
    assert len(chunks) == 1


def test_chunk_boundaries_preserve_content():
    para_a = "First paragraph content."
    para_b = "B" * 800
    para_c = "Last paragraph content."
    text = f"{para_a}\n\n{para_b}\n\n{para_c}"
    chunks = chunk_text(text, max_chars=1000)
    full = " ".join(chunks)
    assert para_a in full
    assert para_c in full
