from unittest.mock import patch
from mdtoaudio import ask_mode


def test_enter_on_first_option_returns_file():
    with patch("mdtoaudio._read_key", side_effect=["enter"]):
        assert ask_mode() == "file"


def test_down_then_enter_returns_folder():
    with patch("mdtoaudio._read_key", side_effect=["down", "enter"]):
        assert ask_mode() == "folder"


def test_cancel_returns_none():
    with patch("mdtoaudio._read_key", side_effect=["cancel"]):
        assert ask_mode() is None


def test_up_wraps_from_first_to_last():
    with patch("mdtoaudio._read_key", side_effect=["up", "enter"]):
        assert ask_mode() == "folder"


def test_down_wraps_back_to_first():
    with patch("mdtoaudio._read_key", side_effect=["down", "down", "enter"]):
        assert ask_mode() == "file"


def test_down_up_returns_to_first():
    with patch("mdtoaudio._read_key", side_effect=["down", "up", "enter"]):
        assert ask_mode() == "file"


def test_other_keys_ignored():
    with patch("mdtoaudio._read_key", side_effect=["other", "other", "enter"]):
        assert ask_mode() == "file"


def test_cancel_after_navigation_returns_none():
    with patch("mdtoaudio._read_key", side_effect=["down", "cancel"]):
        assert ask_mode() is None


def test_multiple_downs_land_on_correct_option():
    # 3 options would wrap; with 2 options, down×3 lands back on folder (index 1)
    with patch("mdtoaudio._read_key", side_effect=["down", "down", "down", "enter"]):
        assert ask_mode() == "folder"
