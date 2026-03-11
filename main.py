import time
from utils.notifier import send_telegram_message, get_telegram_updates, answer_callback
from core.data_fetcher import DataFetcher
from core.smc_engine import SMCEngine
from core.risk_manager import RiskManager
from core.executor import Executor


def main():
    print("Запуск SMC Trading Bot (Smart Loop)...\n")

    fetcher = DataFetcher(exchange_id='bybit')
    risk_manager = RiskManager(balance_usdt=1000, risk_per_trade_pct=1.0, reward_ratio=2.0)
    executor = Executor()  # Ініціалізуємо нашого виконавця

    symbol = 'BTC/USDT'
    timeframe = '15m'

    last_signal_time = None
    last_scan_time = 0  # Час останнього сканування біржі
    SCAN_INTERVAL = 60  # Сканувати біржу кожні 60 секунд

    # "Пам'ять" бота для активних сетапів
    active_signals = {}

    send_telegram_message("🚀 <b>Бот оновлено!</b>\nТепер кнопки активні. Бот чекає на твої команди.")

    while True:
        try:
            current_time = time.time()

            # ==========================================
            # 1. СЛУХАЄМО TELEGRAM (Кожної секунди)
            # ==========================================
            updates = get_telegram_updates()
            for update in updates:
                if 'callback_query' in update:
                    query = update['callback_query']
                    call_id = query['id']
                    data = query['data']  # Це те, що ми передавали в callback_data

                    if data.startswith("execute_"):
                        sym = data.split("_")[1]  # Дістаємо назву пари (BTC/USDT)
                        if sym in active_signals:
                            # Передаємо збережені параметри Виконавцю
                            executor.execute_trade(sym, active_signals[sym])

                            answer_callback(call_id, f"✅ Угоду по {sym} відправлено на біржу!")
                            send_telegram_message(
                                f"✅ <b>Угоду по {sym} успішно відкрито!</b>\n<i>(Режим симуляції)</i>")

                            # Видаляємо сигнал з пам'яті, щоб не виконати двічі
                            del active_signals[sym]
                        else:
                            answer_callback(call_id, "❌ Цей сетап вже неактуальний або виконаний.")

                    elif data == "ignore":
                        answer_callback(call_id, "🗑 Сетап відхилено.")
                        send_telegram_message("🗑 <i>Ти проігнорував останній сетап. Шукаю далі...</i>")
                        active_signals.clear()

            # ==========================================
            # 2. СКАНУЄМО РИНОК (Кожні 60 секунд)
            # ==========================================
            if current_time - last_scan_time >= SCAN_INTERVAL:
                print(f"[{time.strftime('%H:%M:%S')}] Сканування графіка...")

                df = fetcher.get_historical_data(symbol, timeframe, limit=250)

                if df is not None:
                    engine = SMCEngine(df)
                    engine.analyze()
                    signal_info = engine.get_latest_signal()

                    current_candle_time = df.iloc[-2]['timestamp']

                    if signal_info and current_candle_time != last_signal_time:
                        price = df.iloc[-2]['close']
                        trade_params = risk_manager.calculate_trade(
                            signal_type=signal_info["type"], entry_price=price,
                            recent_low=signal_info["recent_low"], recent_high=signal_info["recent_high"]
                        )

                        if trade_params:
                            # ЗАПАМ'ЯТОВУЄМО ПАРАМЕТРИ ДЛЯ ЦІЄЇ ПАРИ
                            active_signals[symbol] = trade_params

                            msg = (f"🟢 <b>Сетап: {signal_info['type']}</b>\n"
                                   f"🎯 <b>Вхід:</b> {trade_params['entry']}\n"
                                   f"🛑 <b>SL:</b> {trade_params['stop_loss']}\n"
                                   f"💰 <b>Об'єм:</b> {trade_params['position_size']} {symbol.split('/')[0]}")

                            buttons = {
                                "inline_keyboard": [
                                    [{"text": "✅ Виконати", "callback_data": f"execute_{symbol}"}],
                                    [{"text": "❌ Ігнорувати", "callback_data": "ignore"}]
                                ]
                            }
                            send_telegram_message(msg, reply_markup=buttons)
                            last_signal_time = current_candle_time

                # Оновлюємо час останнього сканування
                last_scan_time = current_time

            # Пауза 1 секунда, щоб цикл не навантажував процесор комп'ютера на 100%
            time.sleep(1)

        except KeyboardInterrupt:
            print("\nЗупинка бота...")
            break
        except Exception as e:
            print(f"❌ Помилка: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()