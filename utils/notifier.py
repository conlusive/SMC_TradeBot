import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def send_telegram_message(text: str, reply_markup: dict = None):
    """Надсилає повідомлення у Telegram з можливістю додавання кнопок."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Помилка: Не знайдено TELEGRAM_TOKEN або CHAT_ID у файлі .env")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }

    # Якщо ми передали кнопки, додаємо їх до запиту
    if reply_markup:
        payload['reply_markup'] = json.dumps(reply_markup)

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"Помилка відправки в Telegram: {e}")


last_update_id = None


def get_telegram_updates():
    """Перевіряє, чи натискав користувач якісь кнопки."""
    global last_update_id
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates"

    # timeout=1 означає, що запит не буде висіти довго
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
        print(f"Помилка отримання оновлень Telegram: {e}")
    return []


def answer_callback(callback_query_id: str, text: str = ""):
    """Відповідає Telegram, що ми прийняли клік по кнопці (знімає іконку завантаження)."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    try:
        requests.post(url, data={'callback_query_id': callback_query_id, 'text': text})
    except Exception as e:
        pass