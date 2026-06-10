import os
from mdtoaudio import collect_md_files


def test_empty_folder(tmp_path):
    assert collect_md_files(str(tmp_path)) == []


def test_flat_folder_all_md(tmp_path):
    (tmp_path / "a.md").touch()
    (tmp_path / "b.md").touch()
    result = collect_md_files(str(tmp_path))
    assert len(result) == 2


def test_excludes_non_md_files(tmp_path):
    (tmp_path / "note.md").touch()
    (tmp_path / "image.png").touch()
    (tmp_path / "data.csv").touch()
    (tmp_path / "readme.txt").touch()
    result = collect_md_files(str(tmp_path))
    assert len(result) == 1
    assert result[0].endswith("note.md")


def test_recursive_one_level(tmp_path):
    sub = tmp_path / "sub"
    sub.mkdir()
    (tmp_path / "root.md").touch()
    (sub / "child.md").touch()
    result = collect_md_files(str(tmp_path))
    assert len(result) == 2


def test_recursive_deep_nesting(tmp_path):
    deep = tmp_path / "a" / "b" / "c"
    deep.mkdir(parents=True)
    (tmp_path / "top.md").touch()
    (tmp_path / "a" / "mid.md").touch()
    (deep / "leaf.md").touch()
    result = collect_md_files(str(tmp_path))
    assert len(result) == 3
    basenames = {os.path.basename(p) for p in result}
    assert basenames == {"top.md", "mid.md", "leaf.md"}


def test_output_is_sorted(tmp_path):
    (tmp_path / "z.md").touch()
    (tmp_path / "a.md").touch()
    (tmp_path / "m.md").touch()
    result = collect_md_files(str(tmp_path))
    assert result == sorted(result)


def test_case_insensitive_md_extension(tmp_path):
    (tmp_path / "upper.MD").touch()
    (tmp_path / "mixed.Md").touch()
    (tmp_path / "lower.md").touch()
    result = collect_md_files(str(tmp_path))
    assert len(result) == 3


def test_mixed_files_and_folders(tmp_path):
    sub = tmp_path / "notes"
    sub.mkdir()
    (tmp_path / "root.md").touch()
    (tmp_path / "root.txt").touch()
    (sub / "note.md").touch()
    (sub / "image.jpg").touch()
    result = collect_md_files(str(tmp_path))
    assert len(result) == 2
    basenames = {os.path.basename(p) for p in result}
    assert basenames == {"root.md", "note.md"}


def test_returns_full_absolute_paths(tmp_path):
    (tmp_path / "note.md").touch()
    result = collect_md_files(str(tmp_path))
    assert os.path.isabs(result[0])


def test_empty_subdirectory_ignored(tmp_path):
    empty_sub = tmp_path / "empty"
    empty_sub.mkdir()
    (tmp_path / "note.md").touch()
    result = collect_md_files(str(tmp_path))
    assert len(result) == 1
