import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')

def send_telegram_message(text: str, reply_markup: dict = None):
    """Надсилає повідомлення і повертає його ID для подальшого редагування."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        return None

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    try:
        response = requests.post(url, data=payload).json()
        if response.get('ok'):
            return response['result']['message_id']
    except Exception as e:
        print(f"Помилка відправки в Telegram: {e}")
    return None

def edit_telegram_message(message_id: int, text: str, reply_markup: dict = None):
    """Редагує існуюче повідомлення за його ID."""
    if not TELEGRAM_TOKEN or not CHAT_ID or not message_id:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageText"
    payload = {
        'chat_id': CHAT_ID,
        'message_id': message_id,
        'text': text,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Помилка редагування в Telegram: {e}")

# Функції get_telegram_updates та answer_callback залишаються без змін
last_update_id = None
def get_telegram_updates():
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"
    params = {'timeout': 1}
    if last_update_id:
        params['offset'] = last_update_id + 1
    try:
        response = requests.get(url, params=params).json()
        if response.get('ok'):
            results = response.get('result', [])
            for update in results:
                last_update_id = update['update_id']
            return results
    except Exception as e:
        print(f"Помилка отримання оновлень: {e}")
    return []

def answer_callback(callback_query_id: str, text: str = ""):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, data={'callback_query_id': callback_query_id, 'text': text})
    except Exception:
        pass

def send_telegram_photo(photo_path: str, caption: str, reply_markup: dict = None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    with open(photo_path, 'rb') as photo:
        payload = {'chat_id': CHAT_ID, 'caption': caption, 'parse_mode': 'HTML'}
        if reply_markup: payload['reply_markup'] = json.dumps(reply_markup)
        requests.post(url, data=payload, files={'photo': photo})

def edit_telegram_caption(message_id: int, caption: str, reply_markup: dict = None):
    """Редагує підпис під фото повідомленням."""
    if not TELEGRAM_TOKEN or not CHAT_ID or not message_id:
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/editMessageCaption"
    payload = {
        'chat_id': CHAT_ID,
        'message_id': message_id,
        'caption': caption,
        'parse_mode': 'HTML'
    }
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Помилка редагування підпису: {e}")

