import os
from unittest.mock import patch, MagicMock
import pytest
from yandex_upload import upload_to_yandex  # Adjust according to your file structure

YANDEX_BUCKET_NAME = os.environ.get("YANDEX_BUCKET_NAME")

# Mock the boto3 session and client
@patch("boto3.session.Session.client")
def test_upload_to_yandex_success(mock_client):
    # Arrange
    mock_s3 = MagicMock()
    mock_client.return_value = mock_s3
    
    # Mock successful file upload
    mock_s3.upload_file.return_value = None  # No error, successful upload
    
    video_path = "/path/to/video.mp4"
    expected_url = f"https://storage.yandexcloud.net/{YANDEX_BUCKET_NAME}/video.mp4"

    # Act
    result = upload_to_yandex(video_path)
    
    # Assert
    assert result == expected_url
    mock_s3.upload_file.assert_called_once_with(video_path, YANDEX_BUCKET_NAME, "video.mp4", ExtraArgs={'ACL': 'public-read'})
    mock_s3.upload_file.assert_called_once()  # Ensure upload_file was called exactly once

@patch("boto3.session.Session.client")
def test_upload_to_yandex_failure(mock_client):
    # Arrange
    mock_s3 = MagicMock()
    mock_client.return_value = mock_s3
    
    # Simulate an exception during upload
    mock_s3.upload_file.side_effect = Exception("Upload failed")
    
    video_path = "/path/to/video.mp4"

    # Act
    result = upload_to_yandex(video_path)
    
    # Assert
    assert result is None  # Ensure None is returned on failure
    mock_s3.upload_file.assert_called_once_with(video_path, YANDEX_BUCKET_NAME, "video.mp4", ExtraArgs={'ACL': 'public-read'})

