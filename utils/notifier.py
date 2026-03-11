import os
import requests
from dotenv import load_dotenv

# Завантажуємо змінні з файлу .env
load_dotenv()

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')


def send_telegram_message(text: str):
    """Надсилає повідомлення у Telegram."""
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("Помилка: Не знайдено TELEGRAM_TOKEN або CHAT_ID у файлі .env")
        return

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {
        'chat_id': CHAT_ID,
        'text': text,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()  # Перевіряє, чи немає помилок HTTP
    except requests.exceptions.RequestException as e:
        print(f"Помилка відправки в Telegram: {e}")