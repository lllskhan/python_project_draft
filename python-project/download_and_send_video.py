import yt_dlp
import requests
from storage_for_links import load_data
import os
import tempfile

data = load_data()

def find_url(course, year_time, subject_lecturer, topic):
    return data[course][year_time][subject_lecturer][topic]    

def get_available_resolutions(url):
    ydl_opts = {'quiet': True, 'extract_flat': False, 'cookiesfrombrowser': ('chrome',)}
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        resolutions = set()

        for f in info['formats']:
            if f.get('height') and f['height'] >= 720:
                resolutions.add(f['height'])
 
        return sorted(resolutions, reverse=True)

def ask_for_resolution(available_resolutions):
    print("\nAvailable Qualities:")
    for i, res in enumerate(available_resolutions, 1):
        print(f"{i}. {res}p")
    
    while True:
        try:
            choice = int(input("Choose quality (number): "))
            if 1 <= choice <= len(available_resolutions):
                return f"bestvideo[height<={available_resolutions[choice-1]}]+bestaudio/best[height<={available_resolutions[choice-1]}]"
            else:
                print("Invalid choice. Try again.")
        except ValueError:
            print("Пожалуйста, выберите желаемый формат.")

def download_video(url, format_spec):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        temp_filename = tmp.name

    ydl_opts = {
        'format': format_spec,
        'outtmpl': temp_filename,
        'merge_output_format': 'mp4',
        'cookiesfrombrowser': ('chrome',),
        'quiet': True
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        return temp_filename
            
    except Exception as e:
        print(f"ERROR downloading video: {str(e)}")
        raise e 
