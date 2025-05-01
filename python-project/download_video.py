import yt_dlp
import os

def download_video(url: str, format_str: str) -> str:
    """Download a video from YouTube using specified format parameters.
    
    Args:
        url (str): URL of the YouTube video to download
        format_str (str): yt-dlp format selector string (e.g., 'bestvideo+bestaudio/best')
        
    Returns:
        str: Full path to the downloaded video file
        
    Raises:
        yt_dlp.DownloadError: If video download fails
        OSError: If there are file system errors
        
    """
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
