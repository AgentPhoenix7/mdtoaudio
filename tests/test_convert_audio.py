import numpy as np
import pytest
from unittest.mock import MagicMock, patch
from mdtoaudio import convert_to_audio


def _make_mock_pipeline(audio_chunk: np.ndarray):
    """Returns a mock KPipeline instance that yields one audio chunk per call."""
    mock_instance = MagicMock()
    mock_instance.return_value = iter([("graphemes", "phonemes", audio_chunk)])
    return mock_instance


def test_writes_wav_file(tmp_path):
    out = tmp_path / "output.wav"
    fake_audio = np.zeros(24000, dtype=np.float32)
    mock_pipeline = _make_mock_pipeline(fake_audio)

    with patch("mdtoaudio.KPipeline", return_value=mock_pipeline):
        convert_to_audio(["hello world"], str(out))

    assert out.exists()


def test_concatenates_chunks(tmp_path):
    out = tmp_path / "output.wav"
    fake_audio = np.ones(12000, dtype=np.float32)

    mock_instance = MagicMock()

    def side_effect(text, voice, speed):
        return iter([("g", "p", fake_audio)])

    mock_instance.side_effect = side_effect

    with patch("mdtoaudio.KPipeline", return_value=mock_instance):
        with patch("mdtoaudio.sf") as mock_sf:
            convert_to_audio(["chunk one", "chunk two"], str(out))
            written_audio = mock_sf.write.call_args[0][1]
            assert len(written_audio) == 24000  # two 12000-sample chunks concatenated


def test_calls_pipeline_once_per_chunk(tmp_path):
    out = tmp_path / "output.wav"
    fake_audio = np.zeros(100, dtype=np.float32)

    call_count = 0

    def side_effect(text, voice, speed):
        nonlocal call_count
        call_count += 1
        return iter([("g", "p", fake_audio)])

    mock_instance = MagicMock()
    mock_instance.side_effect = side_effect

    with patch("mdtoaudio.KPipeline", return_value=mock_instance):
        with patch("mdtoaudio.sf"):
            convert_to_audio(["one", "two", "three"], str(out))

    assert call_count == 3
