import os
import telebot
import requests
from telebot import types
import json
import yt_dlp
from telebot import apihelper

from download_and_send_video import  get_available_resolutions, ask_for_resolution, download_video
from storage_for_links import load_data

data = load_data()
bot_data = {}

from dotenv import load_dotenv
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')

# # В main.py замените:
# apihelper.proxy = {'https': 'socks5://127.0.0.1:5454'}


# session = requests.Session()
# session.proxies = {
#     'http': 'socks5://127.0.0.1:5454',
#     'https': 'socks5://127.0.0.1:5454'
# }

bot = telebot.TeleBot(
    BOT_TOKEN, 
    # timeout=60,
    # threaded=True,
    # num_threads=5
)

@bot.message_handler(commands=['start'])
def send_welcome(message):
	bot.reply_to(message, "Welcome! The bot is ready to present you relevant lecture.")

@bot.message_handler(commands=['lecture'])
def ask_for_course(message):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for course in data.keys():
        markup.add(course)
    bot.send_message(message.chat.id, "Select a course:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in data.keys())
def ask_for_term(message):
    selected_course = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for term in data[selected_course].keys():
        markup.add(term)
    bot.send_message(message.chat.id, f"Selected: {selected_course}\nChoose term:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in data[course] for course in data))
def ask_for_subject(message):
    # Find which course this term belongs to
    for course in data:
        if message.text in data[course]:
            selected_course = course
            selected_term = message.text
            break
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for subject in data[selected_course][selected_term].keys():
        markup.add(subject)
    bot.send_message(message.chat.id, f"Selected: {selected_course} - {selected_term}\nChoose subject:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in data[course][term] 
                                     for course in data 
                                     for term in data[course]))
def ask_for_title(message):
    # Find which course and term this subject belongs to
    for course in data:
        for term in data[course]:
            if message.text in data[course][term]:
                selected_course = course
                selected_term = term
                selected_subject = message.text
                break
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for topic in data[selected_course][selected_term][selected_subject].keys():
        markup.add(topic)
    bot.send_message(message.chat.id, 
                    f"Selected: {selected_course} - {selected_term}  - {selected_subject}\nChoose topic:", 
                    reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in data[course][term][subject] 
                                      for course in data 
                                      for term in data[course] 
                                      for subject in data[course][term]))
def video_request(message):
    try:
        # Find which course, term and subject this topic belongs to
        for course in data:
            for term in data[course]:
                for subject in data[course][term]:
                    if message.text in data[course][term][subject]:
                        selected_course = course
                        selected_term = term
                        selected_subject = subject
                        selected_topic = message.text
                        url = data[course][term][subject][message.text]
                        break
        
        topic = selected_topic
        resolutions = get_available_resolutions(url)
        
        # Get file sizes for each resolution
        resolutions_with_sizes = []
        for res in resolutions[:3]:  # Show top 3 resolutions max
            format_spec = f"bestvideo[height<={res}]+bestaudio/best[height<={res}]"
            ydl_opts = {
            'format': format_spec,
            'socket_timeout': 30,
            'force_ipv4': True,
            'verbose': True,
            'cookiefile': 'cookies.txt',
            'outtmpl': '%(title)s.%(ext)s',
            'merge_output_format': 'mp4',   
            # 'cookiesfrombrowser': ('chrome',),
            'cookiesfrombrowser': ('firefox',),
            # 'proxy': 'socks5://127.0.0.1:5454',
            'verbose': True,  # Show detailed logs
            'ignoreerrors': False   
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                formats = info.get('formats', [])

                video_stream = next((f for f in formats if f.get('vcodec') != 'none' and f.get('height') == res), None)
                audio_stream = next((f for f in formats if f.get('acodec') != 'none'), None)

                video_size = video_stream.get('filesize', 0) if video_stream else 0
                audio_size = audio_stream.get('filesize', 0) if audio_stream else 0

                total_size_mb = (video_size + audio_size) / (1024 * 1024)
                resolutions_with_sizes.append((res, total_size_mb))
        
        markup = types.InlineKeyboardMarkup()
        for res, size_mb in resolutions_with_sizes:
            if size_mb == 0:
                label = f"{res}p (Size unknown)"
            else:
                label = f"{res}p ({size_mb:.1f} MB)"
            markup.add(types.InlineKeyboardButton(label, callback_data=f"dl_{res}"))
        
        # Store context in memory instead
        user_id = message.from_user.id
        bot_data[user_id] = {  # Use a dict to store temp data
            'url': url,
            'course': selected_course,
            'term': selected_term,
            'subject': selected_subject,            
            'topic': selected_topic
        }
        
        bot.send_message(message.chat.id, f"📹 {topic}", reply_markup=markup)
            
    
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
def send_video_file(call):
    try:
        # Parse all parameters from callback data
        user_id = call.from_user.id
        context = bot_data.get(user_id, {})
        
        if not context:
            return bot.answer_callback_query(call.id, "Session expired!")
        
        resolution = int(call.data.split('_')[1])
        url = context['url']      
        
        bot.answer_callback_query(call.id, "⏳ Downloading...")
        format_spec = f"bestvideo[height<={resolution}]+bestaudio/best[height<={resolution}]"

        video_path = download_video(url, format_spec)
        file_size_mb = os.path.getsize(video_path) / (1024 * 1024)

        course = bot_data[user_id]['course']
        term = bot_data[user_id]['term']
        subject = bot_data[user_id]['subject']
        topic = bot_data[user_id]['topic']
        
        caption = (f"📚 *Course:* {course}\n"
                  f"📅 *Term:* {term}\n"
                  f"🧑‍🏫 *Subject:* {subject}\n"
                  f"📹 *Topic:* {topic}\n"
                  f"🖥 *Quality:* {resolution}\n")
        
        if file_size_mb <= 50:
            with open(video_path, 'rb') as f:
                bot.send_video(call.message.chat.id, f, caption=caption, parse_mode='Markdown')
        elif file_size_mb <= 2000:
            with open(video_path, 'rb') as f:
                bot.send_document(call.message.chat.id, f, caption=caption, parse_mode='Markdown')
        else:
            bot.send_message(call.message.chat.id, "File size exceeds Telegram's 2GB limit.")
    
        os.remove(video_path)    
    
    except Exception as e:
        bot.send_message(call.message.chat.id, f"🔥 Failed: {str(e)}")

# --- Run Bot ---
if __name__ == '__main__':
    print("Bot is running...")
    bot.infinity_polling()
