import yt_dlp
import os
import tempfile
from pathlib import Path

def download_video(url, format_spec='best[filesize<1900M][height<=1080]'):
    """
    Синхронная функция для скачивания видео (будет запускаться в потоке)
    """
    temp_dir = tempfile.mkdtemp(prefix='ytdl_')
    outtmpl = os.path.join(temp_dir, '%(title)s.%(ext)s')

    def progress_hook(d):
        if progress_callback and d['status'] == 'downloading':
            progress_callback(
                d.get('downloaded_bytes', 0),
                d.get('total_bytes', 0),
                d.get('speed', 0),
                d.get('eta', 0)
            )

    ydl_opts = {
        'format': format_spec,
        'outtmpl': outtmpl,
        'merge_output_format': 'mp4',
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
        'extractor_args': {'youtube': {'skip': ['dash', 'hls']}},
        'max_filesize': 1900 * 1024 * 1024,
        'progress_hooks': [progress_hook],
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # Проверка размера файла
            filesize = os.path.getsize(filename) / (1024 * 1024)
            if filesize > 1900:
                raise ValueError(f"File size {filesize:.1f}MB exceeds Telegram limit")
                
            return filename
    except Exception as e:
        # Очистка временных файлов
        for f in Path(temp_dir).glob('*'):
            try:
                f.unlink()
            except:
                pass
        raise

async def send_telegram_video(bot, chat_id, video_path, caption="", timeout=100):
    """
    Асинхронная функция отправки видео
    """
    try:
        filesize = os.path.getsize(video_path) / (1024 * 1024)
        
        with open(video_path, 'rb') as video_file:
            if filesize <= 50:
                await bot.send_video(
                    chat_id=chat_id,
                    video=video_file,
                    caption=caption,
                    parse_mode='Markdown',
                    timeout=timeout,
                    supports_streaming=True
                )
            elif filesize <= 2000:
                await bot.send_document(
                    chat_id=chat_id,
                    document=video_file,
                    caption=caption,
                    parse_mode='Markdown',
                    timeout=timeout,
                    visible_file_name=os.path.basename(video_path)
                )
            else:
                return "File exceeds 2GB limit"
        return True
    except Exception as e:
        return f"Send error: {str(e)}"
