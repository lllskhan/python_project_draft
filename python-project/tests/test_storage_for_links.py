import pytest
import json
from unittest.mock import patch, mock_open, MagicMock
from collections import defaultdict
from storage_for_links import (
    extract_subject_lecturer,
    scrape_playlists,
    save_data,
    load_data
)

# ======== ТЕСТ 1: extract_subject_lecturer ========
def test_extract_subject_lecturer():
    playlist_title = "Математика (1 курс, осень 2023) - Иванов Иван"
    result = extract_subject_lecturer(playlist_title)
    assert result == "Математика(Иванов Иван)"


# ======== ТЕСТ 2: scrape_playlists ========
@patch('yt_dlp.YoutubeDL')
def test_scrape_playlists(mock_ytdl):
    # Setup mock yt_dlp
    mock_ydl_instance = MagicMock()
    mock_ytdl.return_value.__enter__.return_value = mock_ydl_instance

    mock_channel_info = {
        'channel_id': 'test_channel'
    }
    mock_playlists_info = {
        'entries': [
            {'title': "Математика (1 курс, осень 2023) - Иванов Иван", 'url': 'playlist_url_1'},
            {'title': "Физика (1 курс, весна 2024)", 'url': 'playlist_url_2'}
        ]
    }
    mock_video_info = {
        'entries': [
            {'title': 'Лекция 1', 'url': 'https://example.com/video1'},
            {'title': 'Лекция 2', 'url': 'https://example.com/video2'}
        ]
    }

    mock_ydl_instance.extract_info.side_effect = [
        mock_channel_info,    # channel info
        mock_playlists_info,  # playlists page
        mock_video_info,      # playlist 1
        mock_video_info       # playlist 2
    ]

    result = scrape_playlists()

    expected = {
        "1 курс": {
            "осень 2023": {
                "Математика(Иванов Иван)": {
                    '1': 'https://example.com/video1',
                    '2': 'https://example.com/video2'
                }
            },
            "весна 2024": {
                "Физика()": {
                    '1': 'https://example.com/video1',
                    '2': 'https://example.com/video2'
                }
            }
        }
    }

    # Сравниваем обычные словари (не defaultdict)
    def to_dict(d):
        if isinstance(d, defaultdict):
            return {k: to_dict(v) for k, v in d.items()}
        elif isinstance(d, dict):
            return {k: to_dict(v) for k, v in d.items()}
        return d

    assert to_dict(result) == expected


@patch("builtins.open", new_callable=mock_open)
def test_save_and_load_data(mock_open):
    mock_data = {"key": "value"}

    # Save
    save_data(mock_data)

    # Получаем все куски, которые были записаны
    handle = mock_open()
    written = "".join(call.args[0] for call in handle.write.call_args_list)
    expected = json.dumps(mock_data, ensure_ascii=False, indent=2)

    assert written == expected

    # Load
    mock_open().read.return_value = expected
    with patch("json.load", return_value=mock_data):
        loaded = load_data()
        assert loaded == mock_data

