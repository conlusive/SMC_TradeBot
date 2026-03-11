import time
from utils.notifier import send_telegram_message, get_telegram_updates, answer_callback
from core.data_fetcher import DataFetcher
from core.smc_engine import SMCEngine
from core.risk_manager import RiskManager
from core.executor import Executor
from core.macro_filter import MacroFilter
from core.scanner import MarketScanner  # Підключаємо Сканер


def main():
    print("Запуск SMC Trading Bot (Макро + Сканер Наративів)...\n")

    fetcher = DataFetcher(exchange_id='bybit')
    risk_manager = RiskManager(balance_usdt=1000, base_risk_pct=1.0, base_rr=2.0)
    executor = Executor()
    macro_filter = MacroFilter(fetcher)
    scanner = MarketScanner(fetcher)  # Ініціалізуємо сканер

    timeframe = '15m'
    SCAN_INTERVAL = 60  # Сканувати кожні 60 секунд
    last_scan_time = 0

    # Пам'ять бота (тепер зберігає час останнього сигналу та параметри для кожної монети ОКРЕМО)
    last_signal_times = {}
    active_signals = {}

    current_macro = macro_filter.get_market_regime()

    send_telegram_message(
        f"🚀 <b>Бот оновлено! Увімкнено Сканер Наративів.</b>\n\n"
        f"🌍 <b>Макро-режим:</b>\n{current_macro['desc']}"
    )

    while True:
        try:
            current_time = time.time()

            # --- 1. ОБРОБКА КНОПОК TELEGRAM ---
            updates = get_telegram_updates()
            for update in updates:
                if 'callback_query' in update:
                    query = update['callback_query']
                    call_id = query['id']
                    data = query['data']

                    if data.startswith("execute_"):
                        sym = data.split("_")[1]
                        if sym in active_signals:
                            executor.execute_trade(sym, active_signals[sym])
                            answer_callback(call_id, f"✅ Відправлено!")
                            send_telegram_message(f"✅ Угоду по {sym} відкрито!")
                            del active_signals[sym]
                        else:
                            answer_callback(call_id, "❌ Сетап неактуальний.")

                    elif data == "ignore":
                        answer_callback(call_id, "🗑 Відхилено.")
                        # Очищаємо лише той сигнал, який відхилили (потребує доробки логіки кнопок, але поки очистимо все)
                        active_signals.clear()

            # --- 2. СКАНУВАННЯ РИНКУ ---
            if current_time - last_scan_time >= SCAN_INTERVAL:

                current_macro = macro_filter.get_market_regime()

                if current_macro["multiplier"] == 0.0:
                    print(f"[{time.strftime('%H:%M:%S')}] Ринок мертвий. Відпочиваємо...")
                else:
                    # 1. Знаходимо ТОП-3 найгарячіші монети на біржі прямо зараз!
                    hot_symbols = scanner.get_hot_symbols(top_n=3)
                    print(f"🔥 Гарячі монети зараз: {', '.join(hot_symbols)}")

                    # 2. Проходимося по кожній гарячій монеті
                    for sym in hot_symbols:
                        df = fetcher.get_historical_data(sym, timeframe, limit=250)

                        if df is not None:
                            engine = SMCEngine(df)
                            engine.analyze()
                            signal_info = engine.get_latest_signal()

                            current_candle_time = df.iloc[-2]['timestamp']

                            # Перевіряємо, чи ми вже не надсилали сигнал по цій свічці ДЛЯ ЦІЄЇ МОНЕТИ
                            if signal_info and current_candle_time != last_signal_times.get(sym):
                                price = df.iloc[-2]['close']

                                trade_params = risk_manager.calculate_trade(
                                    signal_type=signal_info["type"], entry_price=price,
                                    recent_low=signal_info["recent_low"], recent_high=signal_info["recent_high"],
                                    macro_context=current_macro
                                )

                                if trade_params:
                                    active_signals[sym] = trade_params

                                    msg = (f"🟢 <b>Сетап: {signal_info['type']} ({sym})</b>\n"
                                           f"🌍 <b>Макро:</b> {current_macro['desc']}\n"
                                           f"➖➖➖➖➖➖➖➖➖➖\n"
                                           f"🎯 <b>Вхід:</b> {trade_params['entry']}\n"
                                           f"🛑 <b>SL:</b> {trade_params['stop_loss']}\n"
                                           f"🏆 <b>TP:</b> {trade_params['take_profit']}\n"
                                           f"⚠️ <b>Ризик:</b> {trade_params['risk_pct']}% (${trade_params['risk_usd']})\n"
                                           f"💰 <b>Об'єм:</b> {trade_params['position_size']}")

                                    buttons = {
                                        "inline_keyboard": [
                                            [{"text": f"✅ Виконати {sym}", "callback_data": f"execute_{sym}"}],
                                            [{"text": "❌ Ігнорувати", "callback_data": "ignore"}]
                                        ]
                                    }
                                    send_telegram_message(msg, reply_markup=buttons)
                                    # Запам'ятовуємо час останнього сигналу для цієї монети
                                    last_signal_times[sym] = current_candle_time

                        # Робимо маленьку паузу між монетами, щоб біржа не лаялася на спам запитами
                        time.sleep(1)

                last_scan_time = current_time

            time.sleep(1)

        except KeyboardInterrupt:
            print("\nЗупинка бота...")
            break
        except Exception as e:
            print(f"❌ Помилка: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()