import os
import asyncio
import telebot.async_telebot as async_telebot
from telebot import types
from telebot import asyncio_helper
from telebot.asyncio_helper import ApiTelegramException
from download_video import download_video, send_telegram_video
from storage_for_links import load_data
from storage_for_resolutions_and_sizes import load_resolution_data

# Global variables initialization
data = load_data()
resolution_data = load_resolution_data()
bot_data = {}  # Stores temporary user session data

BOT_TOKEN = os.environ.get('BOT_TOKEN')
bot = async_telebot.AsyncTeleBot(BOT_TOKEN)

# Configure custom API endpoints
bot.api_base_url = 'http://localhost:8081/bot{0}/{1}'
bot.file_base_url = 'http://localhost:8081/file/bot{0}/{1}'

# Set timeouts for requests
asyncio_helper.READ_TIMEOUT = 60
asyncio_helper.CONNECT_TIMEOUT = 60

@bot.message_handler(commands=['start'])
async def send_welcome(message):
    """Handle /start command and send welcome message.
    
    Args:
        message (types.Message): Message object from user
    """
    await bot.reply_to(message, "Welcome! The bot is ready to present you relevant lecture.")

@bot.message_handler(commands=['lecture'])
async def ask_for_course(message):
    """Display available courses for selection.
    
    Args:
        message (types.Message): Message object from user
        
    Shows:
        Reply keyboard with available course options
    """
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True)
    for course in data.keys():
        markup.add(course)
    await bot.send_message(message.chat.id, "Select a course:", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text in data.keys())
async def ask_for_term(message):
    """Display available terms for selected course.
    
    Args:
        message (types.Message): Message containing selected course
        
    Shows:
        Reply keyboard with available term options for the course
    """
    selected_course = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for term in data[selected_course].keys():
        markup.add(term)
    await bot.send_message(message.chat.id, f"Selected: {selected_course}\nChoose term:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in data[course] for course in data))
async def ask_for_subject(message):
    """Display available subjects for selected term.
    
    Args:
        message (types.Message): Message containing selected term
        
    Shows:
        Reply keyboard with available subject options
    """
    for course in data:
        if message.text in data[course]:
            selected_course = course
            selected_term = message.text
            break
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    for subject in data[selected_course][selected_term].keys():
        markup.add(subject)
    await bot.send_message(message.chat.id, f"Selected: {selected_course} - {selected_term}\nChoose subject:", reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in data[course][term] 
                                     for course in data 
                                     for term in data[course]))
async def ask_for_title(message):
    """Display available topics for selected subject.
    
    Args:
        message (types.Message): Message containing selected subject
        
    Shows:
        Reply keyboard with available topic options
    """
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
    await bot.send_message(message.chat.id, 
                    f"Selected: {selected_course} - {selected_term}  - {selected_subject}\nChoose topic:", 
                    reply_markup=markup)

@bot.message_handler(func=lambda m: any(m.text in data[course][term][subject] 
                                    for course in data 
                                    for term in data[course] 
                                    for subject in data[course][term]))
async def video_request(message):
    """Handle topic selection and show available video resolutions.
    
    Args:
        message (types.Message): Message containing selected topic
        
    Raises:
        KeyError: If requested topic not found in data
        
        RuntimeError: If resolution data is missing
    """
    try:
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
        
        user_id = message.from_user.id
        bot_data[user_id] = {
            'url': url,
            'course': selected_course,
            'term': selected_term,
            'subject': selected_subject,            
            'topic': selected_topic
        }
        
        await bot.send_message(message.chat.id, f"📹 {topic}", reply_markup=markup)
            
    
    except Exception as e:
        bot.reply_to(message, f"❌ Error: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('dl_'))
async def handle_video_request(call):
    """Handle video download request and send file to user.
    
    Args:
        call (types.CallbackQuery): Callback query object
        
    Process:
        1. Validate user session
        2. Download video from YouTube
        3. Show download progress
        4. Upload to Telegram
        5. Handle errors and clean temporary files
    """
    try:
        user_id = call.from_user.id
        context = bot_data.get(user_id, {})
        
        if not context:
            await bot.answer_callback_query(call.id, "Session expired!")
            return
        
        resolution = int(call.data.split('_')[1])
        url = context['url']      
        format_spec = f"best[height<={resolution}][filesize<1900M]"

        await bot.answer_callback_query(call.id, "⏳ Downloading video...")
        
        progress_message = await bot.send_message(call.message.chat.id, "⌛ Download progress: 0%")
        
        last_update = 0
        def progress_callback(downloaded, total, speed, eta):
            """Update download progress display.
            
            Args:
                downloaded (int): Bytes downloaded
                total (int): Total bytes to download
                speed (float): Download speed in bytes/sec
                eta (int): Estimated time remaining in seconds
            """
            nonlocal last_update
            current_time = time.time()
            if current_time - last_update > 1:
                percent = (downloaded / total) * 100 if total > 0 else 0
                asyncio.create_task(
                    bot.edit_message_text(
                        f"⌛ Download progress: {percent:.1f}%\n"
                        f"📊 {downloaded/(1024*1024):.1f}MB / {total/(1024*1024):.1f}MB\n"
                        f"⚡ Speed: {speed/(1024*1024):.1f}MB/s\n"
                        f"⏱ ETA: {eta}s",
                        chat_id=progress_message.chat.id,
                        message_id=progress_message.message_id
                    )
                )
                last_update = current_time
        

        try:
            video_path = await asyncio.to_thread(
                download_video, 
                url, 
                f"best[height<={resolution}]",
                progress_callback
            )
            
            await bot.edit_message_text(
                "📤 Uploading to Telegram...",
                chat_id=progress_message.chat.id,
                message_id=progress_message.message_id
            )
            
            caption = f"📹 {context['topic']} ({resolution}p)"
            result = await send_telegram_video(bot, call.message.chat.id, video_path, caption)
            
            if result is True:
                await bot.delete_message(
                    chat_id=progress_message.chat.id,
                    message_id=progress_message.message_id
                )
            else:
                await bot.edit_message_text(
                    f"❌ {result}",
                    chat_id=progress_message.chat.id,
                    message_id=progress_message.message_id
                )
                
        except Exception as e:
            await bot.edit_message_text(
                f"❌ Download failed: {str(e)}",
                chat_id=progress_message.chat.id,
                message_id=progress_message.message_id
            )
            
    except Exception as e:
        await bot.send_message(call.message.chat.id, f"⚠️ Error: {str(e)}")
    finally:
        if 'video_path' in locals() and os.path.exists(video_path):
            os.remove(video_path)

async def main():
    """Main function to start the bot.
    
    Starts asynchronous polling with configured settings
    """
    await bot.polling(none_stop=True)

if __name__ == '__main__':
    print("Bot is running!")
    asyncio.run(main())