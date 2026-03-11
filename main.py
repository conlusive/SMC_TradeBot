import time
import os
from utils.notifier import (
    send_telegram_message,
    edit_telegram_message,
    send_telegram_photo,
    get_telegram_updates,
    answer_callback
)
from core.data_fetcher import DataFetcher
from core.smc_engine import SMCEngine
from core.risk_manager import RiskManager
from core.executor import Executor
from core.macro_filter import MacroFilter
from core.scanner import MarketScanner
from core.dca_investor import DCAInvestor
from core.sentiment_analyzer import SentimentAnalyzer
from core.earn_manager import EarnManager
from utils.visualizer import create_signal_chart


def main():
    print("🚀 Запуск SMC Trading Bot (Professional Edition)...\n")

    # 1. Ініціалізація всіх систем
    fetcher = DataFetcher(exchange_id='bybit')
    risk_manager = RiskManager(balance_usdt=1000, base_risk_pct=1.0)
    executor = Executor()
    macro_filter = MacroFilter(fetcher)
    scanner = MarketScanner(fetcher)
    dca_investor = DCAInvestor(fetcher.exchange)
    earn_manager = EarnManager(fetcher.exchange)

    timeframe = '15m'
    SCAN_INTERVAL = 60
    last_scan_time = 0

    last_signal_times = {}
    active_signals = {}

    # ID повідомлення для "Живого статусу"
    status_message_id = None

    while True:
        try:
            current_time = time.time()

            # --- 2. ОБРОБКА КНОПОК TELEGRAM ---
            updates = get_telegram_updates()
            for update in updates:
                if 'callback_query' in update:
                    query = update['callback_query']
                    data = query['data']
                    call_id = query['id']

                    if data.startswith("execute_"):
                        sym = data.split("_")[1]
                        if sym in active_signals:
                            # Перед угодою можна вивести кошти з Earn, якщо реалізовано автоматику
                            # earn_manager.withdraw_funds(active_signals[sym]['risk_usd'])
                            executor.execute_trade(sym, active_signals[sym])
                            answer_callback(call_id, f"✅ Активуємо: {sym}")
                            send_telegram_message(f"🚀 <b>Угоду по {sym} відправлено на біржу!</b>")
                            del active_signals[sym]
                        else:
                            answer_callback(call_id, "❌ Сетап застарів")

                    elif data == "ignore":
                        answer_callback(call_id, "🗑 Видалено")

            # --- 3. ЦИКЛ СКАНУВАННЯ ТА МОНІТОРИНГУ ---
            if current_time - last_scan_time >= SCAN_INTERVAL:
                # Отримуємо глобальний контекст
                current_macro = macro_filter.get_market_regime()
                btc_sentiment = fetcher.get_market_sentiment('BTC/USDT')
                btc_analysis = SentimentAnalyzer.analyze(btc_sentiment, 'BTC/USDT')

                # Пошук активності
                hot_symbols = scanner.get_hot_symbols(top_n=3)
                coins_formatted = ", ".join([f"<code>{s}</code>" for s in hot_symbols])

                # Оновлення "Живого статусу" (Пилосос повідомлень)
                status_text = (
                    f"🛡 <b>SMC TRADE BOT STATUS</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Стан:</b> {current_macro['desc']}\n"
                    f"💰 <b>BTC Funding:</b> <code>{btc_analysis['funding']}%</code> | {btc_analysis['status']}\n"
                    f"📈 <b>BTC OI:</b> <code>{btc_analysis['oi_formatted']}</code>\n"
                    f"🔥 <b>Цілі:</b> {coins_formatted}\n"
                    f"⏰ <b>Оновлено:</b> <code>{time.strftime('%H:%M:%S')}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"{btc_analysis['warning'] if btc_analysis['warning'] else '🛰 <i>Сканування ринку активоване...</i>'}"
                )

                if status_message_id is None:
                    status_message_id = send_telegram_message(status_text)
                else:
                    edit_telegram_message(status_message_id, status_text)

                # --- 4. ВИКОНАННЯ СТРАТЕГІЇ ---

                # РЕЖИМ DCA (Капітуляція / Смерть)
                if current_macro["multiplier"] == 0.0:
                    dca_report = dca_investor.execute_dca(risk_manager.balance)
                    if dca_report and dca_report != "LOW_BALANCE":
                        send_telegram_message(f"🛒 <b>DCA ЗАКУПКА:</b>\n" + "\n".join(dca_report))

                # РЕЖИМ ТОРГІВЛІ (Активні ф'ючерси)
                else:
                    for sym in hot_symbols:
                        df = fetcher.get_historical_data(sym, timeframe, limit=100)

                        if df is not None:
                            engine = SMCEngine(df)
                            engine.analyze()
                            signal_info = engine.get_latest_signal()

                            # Перевірка нового сигналу
                            if signal_info and df.iloc[-2]['timestamp'] != last_signal_times.get(sym):
                                coin_sentiment = fetcher.get_market_sentiment(sym)
                                coin_analysis = SentimentAnalyzer.analyze(coin_sentiment, sym)

                                trade_params = risk_manager.calculate_trade(
                                    signal_info["type"], df.iloc[-2]['close'],
                                    signal_info["recent_low"], signal_info["recent_high"], current_macro
                                )

                                if trade_params:
                                    active_signals[sym] = trade_params

                                    # ГЕНЕРУЄМО ГРАФІК (Screenshot)
                                    chart_path = create_signal_chart(
                                        df, sym, signal_info["type"],
                                        trade_params['entry'], trade_params['stop_loss'], trade_params['tp1']
                                    )

                                    # Формуємо повідомлення з каскадними тейками
                                    msg = (
                                        f"🎯 <b>НОВИЙ СЕТАП: {sym}</b>\n"
                                        f"━━━━━━━━━━━━━━━━━━━━\n"
                                        f"Тип: <code>{signal_info['type']}</code>\n"
                                        f"Сила: {signal_info['strength']}\n"
                                        f"Funding: <code>{coin_analysis['funding']}%</code>\n"
                                        f"Sentiment: <b>{coin_analysis['status']}</b>\n"
                                        f"━━━━━━━━━━━━━━━━━━━━\n"
                                        f"🎯 Вхід: <b>{trade_params['entry']}</b>\n"
                                        f"🛑 SL: <code>{trade_params['stop_loss']}</code>\n"
                                        f"✅ TP1: <code>{trade_params['tp1']}</code> (50%)\n"
                                        f"✅ TP2: <code>{trade_params['tp2']}</code> (25%)\n"
                                        f"✅ TP3: <code>{trade_params['tp3']}</code> (25%)\n"
                                        f"⚖️ Ризик: {trade_params['risk_pct']}% (${trade_params['risk_usd']})"
                                    )

                                    buttons = {"inline_keyboard": [[
                                        {"text": f"🚀 Trade {sym}", "callback_data": f"execute_{sym}"},
                                        {"text": "🗑 Skip", "callback_data": "ignore"}
                                    ]]}

                                    # Надсилаємо сигнал з картинкою
                                    send_telegram_photo(chart_path, msg, reply_markup=buttons)
                                    last_signal_times[sym] = df.iloc[-2]['timestamp']

                        time.sleep(0.5)

                last_scan_time = current_time

            time.sleep(1)

        except Exception as e:
            print(f"❌ Критична помилка: {e}")
            time.sleep(10)


if __name__ == "__main__":
    main()