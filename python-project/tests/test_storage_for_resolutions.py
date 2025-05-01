import json
import pytest
from unittest.mock import patch, MagicMock, mock_open
from storage_for_resolutions_and_sizes import (
    get_video_resolutions,
    save_resolution_data,
    load_resolution_data,
    process_videos
)

@patch('builtins.open', new_callable=mock_open)
def test_save_and_load_resolution_data(mock_file):
    mock_data = {
        "1 курс": {
            "осень 2023": {
                "Математика(Иванов Иван)": {
                    "Лекция 1": [
                        {"resolution": 720, "filesize_mb": 600, "video_url": "v_url", "audio_url": "a_url", "ext": "mp4"}
                    ]
                }
            }
        }
    }

    # Test save
    save_resolution_data(mock_data)
    handle = mock_file()
    expected_json = json.dumps(mock_data, ensure_ascii=False, indent=2)
    handle.write.assert_called()  # Write called with chunks

@patch('storage_for_resolutions_and_sizes.get_video_resolutions')
def test_process_videos(mock_get_res):
    mock_get_res.return_value = [
        {'resolution': 720, 'filesize_mb': 100, 'video_url': 'v', 'audio_url': 'a', 'ext': 'mp4'}
    ]

    mock_input = {
        "1 курс": {
            "осень 2023": {
                "Математика(Иванов Иван)": {
                    "Видео 1": "https://test.com"
                }
            }
        }
    }

    result = process_videos(mock_input)
    assert "1 курс" in result
    assert "осень 2023" in result["1 курс"]
    assert "Математика(Иванов Иван)" in result["1 курс"]["осень 2023"]
    assert "Видео 1" in result["1 курс"]["осень 2023"]["Математика(Иванов Иван)"]

