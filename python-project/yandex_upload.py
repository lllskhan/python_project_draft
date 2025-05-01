import boto3
from botocore.client import Config
import os

# Yandex Cloud authentication credentials
YANDEX_ACCESS_KEY = os.environ.get("YANDEX_ACCESS_KEY")  # Access key ID from Yandex Cloud IAM
YANDEX_SECRET_KEY = os.environ.get("YANDEX_SECRET_KEY")  # Secret access key from Yandex Cloud IAM
YANDEX_BUCKET_NAME = os.environ.get("YANDEX_BUCKET_NAME")  # Target bucket name
YANDEX_REGION = "ru-central1"  # Yandex Cloud storage region
YANDEX_ENDPOINT = "https://storage.yandexcloud.net"  # Yandex Object Storage endpoint

def upload_to_yandex(video_path: str) -> str | None:
    """Uploads a video file to Yandex Object Storage and returns public URL.
    
    Uses Yandex Cloud's S3-compatible API through boto3 client.
    
    Args:
        video_path (str): Local filesystem path to the video file
        
    Returns:
        str | None: Publicly accessible URL of the uploaded file if successful,
        None if upload fails
        
    Raises:
        botocore.exceptions.ClientError: For AWS/Yandex API errors
        FileNotFoundError: If local video file doesn't exist
        PermissionError: If lacking file access permissions
        
    Example:
        >>> upload_to_yandex("/videos/myvideo.mp4")
        'https://storage.yandexcloud.net/my-bucket/myvideo.mp4'
    """
    session = boto3.session.Session()
    s3 = session.client(
        service_name='s3',
        endpoint_url=YANDEX_ENDPOINT,
        aws_access_key_id=YANDEX_ACCESS_KEY,
        aws_secret_access_key=YANDEX_SECRET_KEY,
        config=Config(signature_version='s3v4'),
        region_name=YANDEX_REGION
    )
   
    try:
        object_name = os.path.basename(video_path)
        s3.upload_file(
            video_path,
            YANDEX_BUCKET_NAME,
            object_name,
            ExtraArgs={'ACL': 'public-read'}  # Set public read access
        )

        return f"{YANDEX_ENDPOINT}/{YANDEX_BUCKET_NAME}/{object_name}"
    except Exception as e:
        print(f"Upload error: {e}")
        return None
