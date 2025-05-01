import yt_dlp
import os

def download_video(url, format_str):
    output_template = "downloads/%(title)s.%(ext)s"
    os.makedirs("downloads", exist_ok=True)

    ydl_opts = {
        'format': format_str,
        'outtmpl': output_template,
        'quiet': True,
        'noplaylist': True,
        'cookiesfrombrowser': ('chrome',)
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        return ydl.prepare_filename(info)

