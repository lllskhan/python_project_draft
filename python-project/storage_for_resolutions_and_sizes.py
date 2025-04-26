from storage_for_links import load_data
data = load_data()

import json
import yt_dlp
import re
from collections import defaultdict

# Конфигурация
CACHE_FILE = "video_resolutions.json"
MAX_SIZE_MB = 2000  # Максимальный размер видео (МБ)

def get_video_resolutions(video_url):
    """Gets resolutions as numbers (360, 480, 720, 1080) with sizes"""
    ydl_opts = {
        'quiet': True,
        'force_ipv4': True,
        'extract_flat': False,
        'cookiesfrombrowser': ('chrome',)
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            if not info:
                return []

            formats = info.get('formats', [])
            if not formats:
                return []

            resolutions_with_sizes = []
            target_resolutions = [144, 360, 480, 720, 1080]  # Standard resolutions as numbers
            
            for res in target_resolutions:
                # Find video stream for this resolution
                video_stream = next(
                    (f for f in formats 
                     if f.get('vcodec') != 'none' 
                     and f.get('height') == res), 
                    None
                )
                
                # Find best audio stream
                audio_stream = next(
                    (f for f in formats 
                     if f.get('acodec') != 'none'),
                    None
                )

                if video_stream:
                    video_size = video_stream.get('filesize', 0) if video_stream else 0
                    audio_size = audio_stream.get('filesize', 0) if audio_stream else 0
                    total_size_mb = round((video_size + audio_size) / (1024 * 1024), 2)
                    
                    resolutions_with_sizes.append({
                        'resolution': res,  # Now stored as number
                        'filesize_mb': total_size_mb,
                        'video_url': video_stream['url'],
                        'audio_url': audio_stream['url'] if audio_stream else None,
                        'ext': video_stream.get('ext', 'mp4')
                    })

            # Sort by resolution (descending)
            resolutions_with_sizes.sort(key=lambda x: x['resolution'], reverse=True)
            
            return resolutions_with_sizes

    except Exception as e:
        print(f"⚠ Error processing {video_url}: {str(e)}")
        return []

def process_videos(input_data):
    """Обрабатывает все видео и возвращает словарь с разрешениями."""
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for course, semesters in input_data.items():
        for semester, subjects in semesters.items():
            for subject, videos in subjects.items():
                for video_title, video_url in videos.items():
                    print(f"🔍 Обрабатываю: {course} | {semester} | {subject} | {video_title}")
                    resolutions = get_video_resolutions(video_url)
                    if resolutions:
                        result[course][semester][subject][video_title] = resolutions
                    else:
                        result[course][semester][subject][video_title] = []  # Нет подходящих форматов

    return result

def save_resolution_data(data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_resolution_data():
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# First-time setup (run this once)
if __name__ == "__main__":
    resolution_data = process_videos(data)
    save_resolution_data(resolution_data)
    print("Resolution data saved successfully!")
