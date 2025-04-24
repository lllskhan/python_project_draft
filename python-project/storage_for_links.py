import yt_dlp
import json
import re
from collections import defaultdict

# Configuration
CHANNEL_URL = "https://www.youtube.com/@lectory_fpmi"
CACHE_FILE = "playlists_data.json"

def extract_subject_lecturer(playlist_title):
    """Extracts subject name from titles like 'Математика (1 курс, осень 2023)'"""
    subject = re.match(r'^[^(]*', playlist_title).group()
    lecturer = re.search(r'-(.*)', playlist_title).group(1)
    result = f"{subject}({lecturer})"
    return result
    

def scrape_playlists():
    ydl_opts = {
        'quiet': True,
        'extract_flat': True,
        'force_ipv4': True,
#        'proxy': 'http://your-proxy:port'
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Get channel ID
        channel_info = ydl.extract_info(CHANNEL_URL, download=False)
        channel_id = channel_info['channel_id']
        
        # Get all playlists
        playlists_url = f"https://www.youtube.com/channel/{channel_id}/playlists"
        playlists_info = ydl.extract_info(playlists_url, download=False)
        
        # Structure: {course: {subject: {video_title: url}}}
        structured_data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))
        
        for playlist in playlists_info['entries']:
            if not playlist.get('url'):
                continue
                
            playlist_title = playlist['title']
            
            # Extract course info
            if "1 курс, осень 2023" in playlist_title.lower():
                course = "1 курс"
                time_of_year = "осень 2023"
            elif "1 курс, весна 2024" in playlist_title.lower():
                course = "1 курс"
                time_of_year = "весна 2024"
            else:
                continue

            # Extract subject + lecturer
            subject_lecturer = extract_subject_lecturer(playlist_title)
            
            # Get videos
            try:
                videos_info = ydl.extract_info(playlist['url'], download=False)
                for video in videos_info['entries']:
                    if video.get('url'):
                        title = re.sub(r'^[^\d]*', '', video['title'])
                        structured_data[course][time_of_year][subject_lecturer][title] = video['url']
                        print(course, time_of_year, subject_lecturer, video['title'])
                
                print(f"Processed: {playlist_title}")
                
            except Exception as e:
                print(f"Skipped {playlist_title}: {str(e)}")
        
        return structured_data

def save_data(data):
    with open(CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_data():
    with open(CACHE_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

# First-time setup (run this once)
if __name__ == "__main__":
    data = scrape_playlists()
    save_data(data)
    print("Data scraped and saved successfully!")
