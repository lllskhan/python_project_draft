import os
import telebot
from telebot import types
from download_video import download_video
from yandex_upload import upload_to_yandex
from storage_for_links import load_data
from storage_for_resolutions_and_sizes import load_resolution_data, save_resolution_data

data = load_data()
resolution_data = load_resolution_data()
bot_data = {}

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = telebot.TeleBot(BOT_TOKEN)

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
        
        resolutions_with_sizes = []
        for i in resolution_data[selected_course][selected_term][selected_subject][selected_topic]:
            resolution = i["resolution"]
            file_size = i["filesize_mb"]
            resolutions_with_sizes.append((resolution, file_size))

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
def handle_video_request(call):
    try:
        user_id = call.from_user.id
        context = bot_data.get(user_id, {})
        if not context:
            bot.answer_callback_query(call.id, "Истекло время ожидания сессии!")
            return

        resolution = int(call.data.split('_')[1])
        url = context['url']
        topic = context['topic']

        resolutions = resolution_data[context['course']][context['term']][context['subject']][context['topic']]
        selected_res = next((r for r in resolutions if r["resolution"] == resolution), None)

        if not selected_res:
            bot.answer_callback_query(call.id, "❌ Ошибка: разрешение не найдено")
            return

        # Если видео уже есть в облаке — сразу отправляем ссылку
        if selected_res.get("cloud_url"):
            bot.send_message(
                call.message.chat.id,
                f"🎥 **{topic}** ({resolution}p)\n[Скачать лекцию/семинар]({selected_res['cloud_url']})",
                parse_mode="Markdown",
                disable_web_page_preview=False
            )
            bot.answer_callback_query(call.id, "✅ Ссылка отправлена!")
            return

        bot.answer_callback_query(call.id, "⏳ Началась загрузка видео...")
        progress_message = bot.send_message(call.message.chat.id, "⌛ Продолжается загрузка видео...")

        video_path = download_video(url, f"best[height<={resolution}]")
        
        bot.edit_message_text(
            "📤 Выгружаю на Облако...",
            chat_id=progress_message.chat.id,
            message_id=progress_message.message_id
        )

        public_url = upload_to_yandex(video_path)
        
        selected_res["cloud_url"] = public_url
        save_resolution_data(resolution_data)

        bot.edit_message_text(
            f"✅ Завершено! [Скачать лекцию/семинар]({public_url})",
            chat_id=progress_message.chat.id,
            message_id=progress_message.message_id,
            parse_mode="Markdown"
        )

    except Exception as e:
        bot.send_message(call.message.chat.id, f"⚠Произошла ошибка: {str(e)}")
    finally:
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)

if __name__ == '__main__':
    print("Bot is running!")
    bot.polling(none_stop=True, timeout=600)
