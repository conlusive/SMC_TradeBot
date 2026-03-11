import time
from utils.notifier import send_telegram_message
from core.data_fetcher import DataFetcher
from core.smc_engine import SMCEngine


def main():
    print("Запуск SMC Trading Bot (Bybit)...\n")

    fetcher = DataFetcher(exchange_id='bybit')
    symbol = 'BTC/USDT'
    timeframe = '15m'

    # Змінна пам'яті, щоб не спамити одним і тим самим сигналом
    last_signal_time = None

    send_telegram_message(f"🚀 <b>Бот запущено!</b>\nПара: {symbol} | Таймфрейм: {timeframe} | Біржа: Bybit")

    # Безперервний цикл
    while True:
        try:
            current_time = time.strftime('%H:%M:%S')
            print(f"[{current_time}] Сканування ринку...")

            df = fetcher.get_historical_data(symbol, timeframe, limit=20)

            if df is not None:
                engine = SMCEngine(df)
                engine.identify_fvg()
                signal = engine.get_latest_signal()

                # Час останньої закритої свічки
                current_candle_time = df.iloc[-2]['timestamp']

                # Якщо є сигнал І ми ще не відправляли повідомлення про цю свічку
                if signal and current_candle_time != last_signal_time:
                    price = df.iloc[-2]['close']
                    emoji = "🟢" if signal == "BULLISH_FVG" else "🔴"

                    msg = (f"{emoji} <b>Знайдено {signal}!</b>\n"
                           f"<b>Пара:</b> {symbol}\n"
                           f"<b>Таймфрейм:</b> {timeframe}\n"
                           f"<b>Час закриття:</b> {current_candle_time}\n"
                           f"<b>Ціна:</b> {price}")

                    send_telegram_message(msg)
                    print(f"🔔 Надіслано сигнал у Telegram: {signal}")

                    # Запам'ятовуємо цю свічку
                    last_signal_time = current_candle_time
                else:
                    print("Нових сигналів немає. Чекаємо...")

            # Робимо паузу на 60 секунд перед наступним запитом (щоб біржа не забанила)
            time.sleep(60)

        except KeyboardInterrupt:
            # Щоб можна було красиво зупинити бота комбінацією Ctrl+C
            print("\nЗупинка бота...")
            send_telegram_message("🛑 <b>Бот зупинено користувачем.</b>")
            break
        except Exception as e:
            print(f"❌ Сталася помилка: {e}")
            time.sleep(60)


if __name__ == "__main__":
    main()