import yt_dlp
import json
import re
from collections import defaultdict

# Configuration
CHANNEL_URL = "https://www.youtube.com/@lectory_fpmi"
CACHE_FILE = "playlists_data.json"

def extract_subject_lecturer(playlist_title: str) -> str:
    """Extracts subject and lecturer information from playlist title.
    
    Parses playlist titles in the format:
    "Subject (Course Info) - Lecturer Name"
    
    Args:
        playlist_title: Raw title string from YouTube playlist
            Example: "Математика (1 курс, осень 2023) - Иван Петров"
            
    Returns:
        Formatted string combining subject and lecturer
        Example: "Математика(Иван Петров)"
        
    Raises:
        AttributeError: If title format doesn't match expected pattern
    """
    subject = re.match(r'^[^(]*', playlist_title).group()
    lecturer = re.search(r'-(.*)', playlist_title).group(1)
    return f"{subject}({lecturer})"

def scrape_playlists() -> defaultdict:
    """Scrapes YouTube channel playlists and structures video data.
    
    Processes channel playlists to create nested dictionary structure:
    {
        course: {
            term: {
                subject_lecturer: {
                    video_title: url
                }
            }
        }
    }
    
    Returns:
        Nested defaultdict containing organized video data
        
    Raises:
        yt_dlp.DownloadError: If YouTube data extraction fails
        KeyError: If required data fields are missing
        
    Note:
        Currently processes only specific course/term patterns:
        - "1 курс, осень 2023"
        - "1 курс, весна 2024"
    """
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_ipv4': True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        channel_info = ydl.extract_info(CHANNEL_URL, download=False)
        channel_id = channel_info['channel_id']
        
        playlists_url = f"https://www.youtube.com/channel/{channel_id}/playlists"
        playlists_info = ydl.extract_info(playlists_url, download=False)
        
        structured_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        
        for playlist in playlists_info['entries']:
            if not playlist.get('url'):
                continue
                
            playlist_title = playlist['title']
            
            # Course detection logic
            course = "1 курс"
            time_of_year = (
                "осень 2023" if "осень 2023" in playlist_title.lower()
                else "весна 2024" if "весна 2024" in playlist_title.lower()
                else None
            )
            
            if not time_of_year:
                continue

            try:
                subject_lecturer = extract_subject_lecturer(playlist_title)
                videos_info = ydl.extract_info(playlist['url'], download=False)
                
                for video in videos_info['entries']:
                    if video.get('url'):
                        title = re.sub(r'^[^\d]*', '', video['title'])
                        structured_data[course][time_of_year][subject_lecturer][title] = video['url']
                        
            except Exception as e:
                print(f"Skipped {playlist_title}: {str(e)}")
                
        return structured_data

def save_data(data: dict) -> None:
    """Saves structured data to JSON file.
    
    Args:
        data: Dictionary containing organized video data
    """
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data() -> dict:
    """Loads structured data from JSON cache file.
    
    Returns:
        Dictionary with video data structure
        
    Raises:
        FileNotFoundError: If cache file doesn't exist
        JSONDecodeError: If cache file contains invalid JSON
    """
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# First-time setup (run this once)
if __name__ == "__main__":
    """Main execution block for initial data scraping.
    
    Usage:
        Run directly to scrape channel data and create cache file.
        Subsequent runs should use load_data() instead.
    """
    data = scrape_playlists()
    save_data(data)
    print("Data scraped and saved successfully!")