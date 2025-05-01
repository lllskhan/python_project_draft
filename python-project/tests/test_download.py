import os
import pytest
from unittest.mock import patch, MagicMock
from download_video import download_video

@patch("download_video.yt_dlp.YoutubeDL")
def test_download_video_success(mock_ytdlp):
    # Setup mocks
    mock_ydl_instance = MagicMock()
    mock_info = {"title": "test_video", "ext": "mp4"}
    mock_ydl_instance.extract_info.return_value = mock_info
    mock_ydl_instance.prepare_filename.return_value = "downloads/test_video.mp4"
    mock_ytdlp.return_value.__enter__.return_value = mock_ydl_instance

    # Call function
    result = download_video("https://example.com/video", "best")

    # Assertions
    assert result == "downloads/test_video.mp4"
    mock_ydl_instance.extract_info.assert_called_once_with("https://example.com/video", download=True)
    mock_ydl_instance.prepare_filename.assert_called_once_with(mock_info)

def test_download_video_creates_folder(tmp_path):
    with patch("download_video.yt_dlp.YoutubeDL") as mock_ytdlp:
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {"title": "abc", "ext": "mp4"}
        mock_instance.prepare_filename.return_value = tmp_path / "abc.mp4"
        mock_ytdlp.return_value.__enter__.return_value = mock_instance

        # Temporarily change working directory
        original_dir = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = download_video("https://example.com", "best")
            assert os.path.exists(tmp_path / "downloads")
            assert str(result).endswith(".mp4")
        finally:
            os.chdir(original_dir)

