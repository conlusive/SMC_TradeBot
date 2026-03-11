import time
from utils.notifier import send_telegram_message, get_telegram_updates, answer_callback
from core.data_fetcher import DataFetcher
from core.smc_engine import SMCEngine
from core.risk_manager import RiskManager
from core.executor import Executor
from core.macro_filter import MacroFilter
from core.scanner import MarketScanner


def main():
    print("Запуск SMC Trading Bot (Повна Автономія)...\n")

    fetcher = DataFetcher(exchange_id='bybit')
    risk_manager = RiskManager(balance_usdt=1000, base_risk_pct=1.0, base_rr=2.0)
    executor = Executor()
    macro_filter = MacroFilter(fetcher)
    scanner = MarketScanner(fetcher)

    timeframe = '15m'
    SCAN_INTERVAL = 60
    last_scan_time = 0

    last_signal_times = {}
    active_signals = {}
    last_hot_coins = []  # Пам'ять для відстеження змін у списку монет

    send_telegram_message("🚀 <b>Бот онлайн!</b>\nАналізую макро-режим та шукаю ліквідність...")

    while True:
        try:
            current_time = time.time()

            # --- ОБРОБКА КНОПОК ---
            updates = get_telegram_updates()
            for update in updates:
                if 'callback_query' in update:
                    query = update['callback_query']
                    data = query['data']
                    if data.startswith("execute_"):
                        sym = data.split("_")[1]
                        if sym in active_signals:
                            executor.execute_trade(sym, active_signals[sym])
                            answer_callback(query['id'], "✅ Виконано!")
                            send_telegram_message(f"✅ Угоду по {sym} активовано!")
                            del active_signals[sym]
                    elif data == "ignore":
                        answer_callback(query['id'], "🗑 Відхилено.")

            # --- СКАНУВАННЯ ---
            if current_time - last_scan_time >= SCAN_INTERVAL:
                current_macro = macro_filter.get_market_regime()

                if current_macro["multiplier"] > 0:
                    hot_symbols = scanner.get_hot_symbols(top_n=3)

                    # Якщо список монет змінився — повідомляємо в Telegram
                    if hot_symbols != last_hot_coins:
                        coins_list = ", ".join(hot_symbols)
                        status_msg = (f"🔍 <b>Оновлено цілі сканування:</b>\n"
                                      f"🔥 Монети: <code>{coins_list}</code>\n"
                                      f"📊 Режим: {current_macro['regime']}")
                        send_telegram_message(status_msg)
                        last_hot_coins = hot_symbols

                    for sym in hot_symbols:
                        df = fetcher.get_historical_data(sym, timeframe, limit=250)
                        if df is not None:
                            engine = SMCEngine(df)
                            engine.analyze()
                            signal_info = engine.get_latest_signal()

                            if signal_info and df.iloc[-2]['timestamp'] != last_signal_times.get(sym):
                                trade_params = risk_manager.calculate_trade(
                                    signal_info["type"], df.iloc[-2]['close'],
                                    signal_info["recent_low"], signal_info["recent_high"], current_macro
                                )
                                if trade_params:
                                    active_signals[sym] = trade_params
                                    msg = (f"🎯 <b>НОВИЙ СЕТАП: {sym}</b>\n"
                                           f"Тип: {signal_info['type']}\n"
                                           f"Вхід: {trade_params['entry']}\n"
                                           f"Ризик: {trade_params['risk_pct']}%")

                                    buttons = {"inline_keyboard": [[
                                        {"text": "✅ Trade", "callback_data": f"execute_{sym}"},
                                        {"text": "❌ Skip", "callback_data": "ignore"}
                                    ]]}
                                    send_telegram_message(msg, reply_markup=buttons)
                                    last_signal_times[sym] = df.iloc[-2]['timestamp']
                        time.sleep(1)

                last_scan_time = current_time
            time.sleep(1)

        except Exception as e:
            print(f"❌ Помилка: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()