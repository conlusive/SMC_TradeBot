from utils.notifier import send_telegram_message


def main():
    print("Запуск SMC Trading Bot...")

    # Тестуємо модуль сповіщень
    send_telegram_message("✅ <b>Архітектура налаштована!</b>\nБот готовий до підключення модулів аналізу.")


if __name__ == "__main__":
    main()