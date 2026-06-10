import pytest
from mdtoaudio import clean_text


def test_strips_frontmatter():
    md = "---\nnext: '[[]]'\nauthor: me\n---\n# Hello\nWorld"
    result = clean_text(md)
    assert "next:" not in result
    assert "Hello" in result
    assert "World" in result


def test_strips_embedded_files():
    md = "![[image.png]]\nSome text"
    result = clean_text(md)
    assert "![[" not in result
    assert "Some text" in result


def test_keeps_wiki_link_text():
    md = "See [[My Note]] for more"
    assert clean_text(md) == "See My Note for more"


def test_keeps_wiki_link_alias():
    md = "See [[My Note|the alias]] for more"
    assert clean_text(md) == "See the alias for more"


def test_keeps_code_block_content():
    md = "Example:\n```sql\nSELECT * FROM users;\n```"
    result = clean_text(md)
    assert "SELECT * FROM users;" in result


def test_strips_dataviewjs_block():
    md = "```dataviewjs\ndv.paragraph('hi');\n```\nSome text"
    result = clean_text(md)
    assert "dv.paragraph" not in result
    assert "Some text" in result


def test_strips_templater_syntax():
    md = "<% tp.file.cursor(1) %>\nSome text"
    result = clean_text(md)
    assert "<%" not in result
    assert "Some text" in result


def test_strips_html_tags():
    md = '<img src="icon.png" class="inline-emoji">\nSome text'
    result = clean_text(md)
    assert "<img" not in result
    assert "Some text" in result


def test_humanizes_obsidian_emoji_li_prefix():
    md = ":LiBell: Recently updated"
    result = clean_text(md)
    assert "Bell" in result
    assert ":LiBell:" not in result


def test_humanizes_obsidian_emoji_cu_prefix():
    md = ":CuLanguage: Taught in English"
    result = clean_text(md)
    assert "Language" in result


def test_humanizes_obsidian_emoji_multiword():
    md = ":LiCheckCircle: Done"
    result = clean_text(md)
    assert "Check Circle" in result


def test_strips_bold_markers():
    md = "This is **bold** text"
    assert clean_text(md) == "This is bold text"


def test_strips_italic_markers():
    md = "This is *italic* text"
    assert clean_text(md) == "This is italic text"


def test_strips_header_markers():
    md = "## What you'll learn"
    assert clean_text(md) == "What you'll learn"


def test_strips_all_header_levels():
    md = "# H1\n## H2\n### H3"
    result = clean_text(md)
    assert "#" not in result
    assert "H1" in result
    assert "H2" in result
    assert "H3" in result


def test_tables_spoken_as_comma_lines():
    md = "| Col1 | Col2 |\n|------|------|\n| A    | B    |\n\nAfter table"
    result = clean_text(md)
    assert "|" not in result
    assert "Col1, Col2." in result
    assert "A, B." in result
    assert "After table" in result


def test_keeps_inline_code():
    md = "Use `SELECT *` to query"
    assert clean_text(md) == "Use SELECT * to query"


def test_preserves_snake_case_identifiers():
    md = "Use snake_case_var in your code"
    assert "snake_case_var" in clean_text(md)


def test_strips_standalone_horizontal_rule():
    md = "Above\n\n---\n\nBelow"
    result = clean_text(md)
    assert "Above" in result
    assert "Below" in result
