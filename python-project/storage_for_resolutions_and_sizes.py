from storage_for_links import load_data
data = load_data()

import json
import yt_dlp
import re
from collections import defaultdict

# Configuration
CACHE_FILE = "video_resolutions.json"
MAX_SIZE_MB = 2000  # Maximum video size in megabytes

def get_video_resolutions(video_url: str) -> list[dict]:
    """Retrieves available video resolutions and technical details from YouTube URL.
    
    Args:
        video_url (str): YouTube video URL to analyze
        
    Returns:
        list[dict]: Sorted list of resolution entries with metadata, ordered by 
        resolution descending. Each entry contains:
        - resolution (int): Vertical resolution in pixels
        - filesize_mb (float): Total size of video+audio in megabytes
        - video_url (str): Direct video stream URL
        - audio_url (str|None): Separate audio stream URL if available
        - ext (str): File extension/container format
        
    Raises:
        yt_dlp.DownloadError: If video information extraction fails
    """
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
            target_resolutions = [144, 360, 480, 720, 1080]
            
            for res in target_resolutions:
                video_stream = next(
                    (f for f in formats 
                     if f.get('vcodec') != 'none' 
                     and f.get('height') == res), 
                    None
                )
                
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
                        'resolution': res,
                        'filesize_mb': total_size_mb,
                        'video_url': video_stream['url'],
                        'audio_url': audio_stream['url'] if audio_stream else None,
                        'ext': video_stream.get('ext', 'mp4')
                    })

            resolutions_with_sizes.sort(key=lambda x: x['resolution'], reverse=True)
            return resolutions_with_sizes

    except Exception as e:
        print(f"⚠ Error processing {video_url}: {str(e)}")
        return []

def process_videos(input_data: dict) -> defaultdict:
    """Processes video data to collect resolution information for all entries.
    
    Args:
        input_data (dict): Nested dictionary structure containing video URLs.
        Expected format:
        {
            course: {
                semester: {
                    subject: {
                        video_title: video_url
                    }
                }
            }
        }
        
    Returns:
        defaultdict: Nested dictionary with resolution data added. Structure:
        {
            course: {
                semester: {
                    subject: {
                        video_title: [resolution_entries]
                    }
                }
            }
        }
    """
    result = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for course, semesters in input_data.items():
        for semester, subjects in semesters.items():
            for subject, videos in subjects.items():
                for video_title, video_url in videos.items():
                    print(f"Processing: {course} | {semester} | {subject} | {video_title}")
                    resolutions = get_video_resolutions(video_url)
                    if resolutions:
                        result[course][semester][subject][video_title] = resolutions
                    else:
                        result[course][semester][subject][video_title] = []

    return result

def save_resolution_data(data: dict) -> None:
    """Saves resolution data to JSON cache file.
    
    Args:
        data (dict): Resolution data dictionary to save
    """
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_resolution_data() -> dict:
    """Loads resolution data from cache file.
    
    Returns:
        dict: Previously saved resolution data
        
    Raises:
        FileNotFoundError: If cache file doesn't exist
        JSONDecodeError: If cache file contains invalid JSON
    """
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# First-time setup (run this once)
if __name__ == "__main__":
    """Initial data processing and caching routine.
    
    Usage:
        Run directly to generate resolution data cache from source URLs.
        Subsequent runs should use load_resolution_data() instead.
    """
    resolution_data = process_videos(data)
    save_resolution_data(resolution_data)
    print("Resolution data saved successfully!")