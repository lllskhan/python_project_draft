import pytest
from unittest.mock import MagicMock, patch
from main import bot, bot_data, data, resolution_data

@pytest.fixture
def message():
    return MagicMock()

@pytest.fixture
def call():
    mock_call = MagicMock()
    mock_call.data = 'dl_720'
    mock_call.from_user.id = 123
    mock_call.message.chat.id = 12345
    mock_call.id = 'abc123'
    return mock_call

def test_start_handler(message):
    message.text = '/start'
    bot.reply_to = MagicMock()
    from main import send_welcome
    send_welcome(message)
    bot.reply_to.assert_called_once_with(message, "Welcome! The bot is ready to present you relevant lecture.")

def test_lecture_handler(message):
    message.text = '/lecture'
    bot.send_message = MagicMock()
    from main import ask_for_course
    ask_for_course(message)
    bot.send_message.assert_called()

def test_course_selection(message):
    course = list(data.keys())[0]
    message.text = course
    message.chat.id = 1
    bot.send_message = MagicMock()
    from main import ask_for_term
    ask_for_term(message)
    bot.send_message.assert_called()
    assert course in bot.send_message.call_args[0][1]

def test_term_selection(message):
    course = list(data.keys())[0]
    term = list(data[course].keys())[0]
    message.text = term
    message.chat.id = 1
    bot.send_message = MagicMock()
    from main  import ask_for_subject
    ask_for_subject(message)
    bot.send_message.assert_called()

def test_subject_selection(message):
    course = list(data.keys())[0]
    term = list(data[course].keys())[0]
    subject = list(data[course][term].keys())[0]
    message.text = subject
    message.chat.id = 1
    bot.send_message = MagicMock()
    from main import ask_for_title
    ask_for_title(message)
    bot.send_message.assert_called()

@patch('main.download_video')
@patch('main.upload_to_yandex')
def test_video_callback_success(mock_upload, mock_download, call):
    # Setup mock data
    mock_download.return_value = 'mock_path.mp4'
    mock_upload.return_value = 'https://mock.yandex.url'

    course = list(data.keys())[0]
    term = list(data[course].keys())[0]
    subject = list(data[course][term].keys())[0]
    topic = list(data[course][term][subject].keys())[0]

    bot_data[123] = {
        'url': data[course][term][subject][topic],
        'course': course,
        'term': term,
        'subject': subject,
        'topic': topic
    }

    res = resolution_data[course][term][subject][topic][0]
    res["cloud_url"] = None
    res["resolution"] = 720
    res["filesize_mb"] = 10.5

    bot.answer_callback_query = MagicMock()
    bot.send_message = MagicMock()
    bot.edit_message_text = MagicMock()

    from main import handle_video_request
    handle_video_request(call)

    bot.send_message.assert_called_once_with(call.message.chat.id, "⌛ Продолжается загрузка видео...")
    bot.edit_message_text.assert_called()
    bot.answer_callback_query.assert_called()

