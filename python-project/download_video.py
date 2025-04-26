import yt_dlp
import os
from storage_for_links import load_data

data = load_data()

def download_video(url, format_spec):
    outtmpl = os.path.join(os.getcwd(), f"video_{os.getpid()}.%(ext)s")

    ydl_opts = {
        'format': format_spec,
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'quiet': True,
        'noplaylist': True,
        'cookiesfrombrowser': ('chrome',),
        'geo_bypass': True,
        'geo_bypass_country': 'US',
        'extractor_args': {
            'youtube': {
                'skip': ['dash', 'hls']
            }
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])

        # Найди файл с расширением .mp4
        downloaded_files = [f for f in os.listdir(os.getcwd()) if f.startswith(f"video_{os.getpid()}") and f.endswith(".mp4")]
        if downloaded_files:
            return os.path.join(os.getcwd(), downloaded_files[0])
        else:
            raise FileNotFoundError("Video file not found")

    except Exception as e:
        print(f"Download failed: {str(e)}")
        raise Exception("Video download failed")

