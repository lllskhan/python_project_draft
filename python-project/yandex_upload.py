import boto3
from botocore.client import Config
import os

YANDEX_ACCESS_KEY = os.environ.get("YANDEX_ACCESS_KEY")
YANDEX_SECRET_KEY = os.environ.get("YANDEX_SECRET_KEY")
YANDEX_BUCKET_NAME = os.environ.get("YANDEX_BUCKET_NAME")
YANDEX_REGION = "ru-central1"
YANDEX_ENDPOINT = "https://storage.yandexcloud.net"

def upload_to_yandex(video_path):
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
        s3.upload_file(video_path, YANDEX_BUCKET_NAME, object_name, ExtraArgs={'ACL': 'public-read'})

        public_url = f"{YANDEX_ENDPOINT}/{YANDEX_BUCKET_NAME}/{object_name}"
        return public_url
    except Exception as e:
        print(f"Ошибка загрузки в облако: {e}")
        return None
