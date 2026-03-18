import time
import os
import sys
from datetime import datetime
from utils.notifier import (
    send_telegram_message,
    edit_telegram_message,
    send_telegram_photo,
    edit_telegram_caption,
    get_telegram_updates,
    answer_callback
)
from core.data_fetcher import DataFetcher
from core.smc_engine import SMCEngine
from core.risk_manager import RiskManager
from core.executor import Executor
from core.macro_filter import MacroFilter
from core.scanner import MarketScanner
from core.database import Database
from core.sentiment_analyzer import SentimentAnalyzer
from core.news_analyzer import NewsAnalyzer
from utils.visualizer import create_signal_chart


def main():
    print("🚀 Запуск SMC Trading Bot (ULTRA AGGRESSIVE EDITION)...\n")

    # 1. Ініціалізація всіх систем
    fetcher = DataFetcher(exchange_id='bybit')
    db = Database()
    risk_manager = RiskManager(balance_usdt=100, base_risk_pct=1.0)  # Початковий банк $100
    executor = Executor()
    macro_filter = MacroFilter(fetcher)
    scanner = MarketScanner(fetcher)
    news_analyzer = NewsAnalyzer()

    timeframe = '15m'
    SCAN_INTERVAL = 60
    last_scan_time = 0
    last_report_date = ""

    last_signal_times = {}
    active_signals = {}
    status_message_id = None

    try:
        while True:
            current_time = time.time()
            now = datetime.now()

            # --- 2. ЩОДЕННИЙ ЗВІТ (о 09:00 ранку) ---
            if now.hour == 9 and now.minute == 0 and last_report_date != now.strftime("%Y-%m-%d"):
                stats = db.get_daily_stats()
                report = (
                    f"📅 <b>DAILY PERFORMANCE REPORT</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"✅ Угод у базі: {stats['count']}\n"
                    f"💰 Поточний баланс: ${risk_manager.balance}\n"
                    f"🖥 Статус сервера: <b>ONLINE</b>"
                )
                send_telegram_message(report)
                last_report_date = now.strftime("%Y-%m-%d")

            # --- 3. ОБРОБКА КНОПОК ТА ІСТОРІЇ ---
            updates = get_telegram_updates()
            for update in updates:
                if 'callback_query' in update:
                    query = update['callback_query']
                    data, msg_id, call_id = query['data'], query['message']['message_id'], query['id']

                    if data.startswith("execute_"):
                        sym = data.split("_")[1]
                        if sym in active_signals:
                            trade = active_signals[sym]
                            executor.execute_trade(sym, trade)
                            db.log_trade(sym, trade['type'], trade['entry'])  # Запис в БД

                            manage_caption = (
                                f"🔥 <b>ПОЗИЦІЯ ВІДКРИТА: {sym}</b>\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"⚙️ Плече: <b>{trade['leverage']}x</b>\n"
                                f"🎯 Вхід: {trade['entry']}\n"
                                f"🛑 SL: {trade['stop_loss']}\n"
                                f"✅ TP: {trade['tp1']} | {trade['tp2']}\n"
                                f"━━━━━━━━━━━━━━━━━━━━\n"
                                f"🛰 <i>Моніторинг активний...</i>"
                            )
                            edit_telegram_caption(msg_id, manage_caption, {
                                "inline_keyboard": [[{"text": f"🛑 Закрити {sym}", "callback_data": f"close_{sym}"}]]})
                            answer_callback(call_id, "🚀 Угоду активовано!")

                    elif data.startswith("close_"):
                        sym = data.split("_")[1]
                        executor.close_trade(sym)
                        edit_telegram_caption(msg_id, f"🏁 <b>УГОДУ ПО {sym} ЗАВЕРШЕНО</b>", {"inline_keyboard": []})
                        answer_callback(call_id, "Закрито!")

            # --- 4. СКАНУВАННЯ ТА ЖИВИЙ СТАТУС ---
            if current_time - last_scan_time >= SCAN_INTERVAL:
                current_macro = macro_filter.get_market_regime()
                btc_sentiment = fetcher.get_market_sentiment('BTC/USDT')
                btc_analysis = SentimentAnalyzer.analyze(btc_sentiment, 'BTC/USDT')
                fng = news_analyzer.get_fear_greed_index()

                hot_symbols = scanner.get_hot_symbols(top_n=3)
                coins_formatted = ", ".join([f"<code>{s}</code>" for s in hot_symbols])

                status_text = (
                    f"🛡 <b>SMC TRADE BOT STATUS</b>\n"
                    f"━━━━━━━━━━━━━━━━━━━━\n"
                    f"📊 <b>Стан:</b> {current_macro['desc']}\n"
                    f"🧠 <b>Настрій:</b> {fng['label']} ({fng['value']}/100)\n"
                    f"💰 BTC Funding: <code>{btc_analysis['funding']}%</code>\n"
                    f"📈 BTC OI: <code>{btc_analysis['oi_formatted']}</code>\n"
                    f"🔥 Цілі: {coins_formatted}\n"
                    f"⏰ Update: <code>{now.strftime('%H:%M:%S')}</code>\n"
                    f"━━━━━━━━━━━━━━━━━━━━"
                )

                if status_message_id is None:
                    status_message_id = send_telegram_message(status_text)
                else:
                    edit_telegram_message(status_message_id, status_text)

                # --- 5. ПОШУК СИГНАЛІВ (MTF 1H + 15M) ---
                if current_macro["multiplier"] > 0:
                    for sym in hot_symbols:
                        # Тренд на 1 годину (Multi-Timeframe Filter)
                        df_1h = fetcher.get_historical_data(sym, '1h', limit=50)
                        if df_1h is None: continue
                        ema_1h = df_1h['close'].ewm(span=50).mean().iloc[-1]
                        trend_1h = "UP" if df_1h.iloc[-1]['close'] > ema_1h else "DOWN"

                        # Аналіз 15 хвилин (SMC Strategy)
                        df = fetcher.get_historical_data(sym, timeframe, limit=100)
                        if df is not None:
                            engine = SMCEngine(df)
                            engine.analyze()
                            signal = engine.get_latest_signal()

                            if signal and df.iloc[-2]['timestamp'] != last_signal_times.get(sym):
                                # Фільтр за годинним трендом
                                if ("BUY" in signal['type'] and trend_1h == "UP") or (
                                        "SELL" in signal['type'] and trend_1h == "DOWN"):
                                    trade = risk_manager.calculate_trade(signal['type'], df.iloc[-2]['close'],
                                                                         signal['recent_low'], signal['recent_high'],
                                                                         current_macro)
                                    if trade:
                                        active_signals[sym] = {**trade, "type": signal['type']}
                                        chart = create_signal_chart(df, sym, signal['type'], trade['entry'],
                                                                    trade['stop_loss'], trade['tp1'])

                                        tag = "🔥 <b>ULTRA AGGRESSIVE ENTRY</b>" if current_macro[
                                                                                       'regime'] == "RISK_ON_HIGH_LIQ" else "🛡 NORMAL ENTRY"

                                        msg = (
                                            f"🎯 <b>НОВИЙ СЕТАП: {sym}</b>\n"
                                            f"━━━━━━━━━━━━━━━━━━━━\n"
                                            f"📈 Режим: {tag}\n"
                                            f"⚙️ Плече: <b>{trade['leverage']}x</b>\n"
                                            f"💰 Funding: <code>{fetcher.get_market_sentiment(sym)['funding']}%</code>\n"
                                            f"━━━━━━━━━━━━━━━━━━━━\n"
                                            f"🎯 Вхід: <b>{trade['entry']}</b>\n"
                                            f"🛑 SL: <code>{trade['stop_loss']}</code>\n"
                                            f"✅ TP1: <code>{trade['tp1']}</code> (50%)\n"
                                            f"⚖️ Ризик: {trade['risk_pct']}% (${trade['risk_usd']})"
                                        )
                                        send_telegram_photo(chart, msg, reply_markup={"inline_keyboard": [
                                            [{"text": f"🚀 Trade {sym}", "callback_data": f"execute_{sym}"},
                                             {"text": "🗑 Skip", "callback_data": "ignore"}]]})
                                        last_signal_times[sym] = df.iloc[-2]['timestamp']

                last_scan_time = current_time
            time.sleep(1)

    except KeyboardInterrupt:
        print("\n🛑 Роботу бота зупинено користувачем.")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Критична помилка: {e}")
        time.sleep(10)


if __name__ == "__main__":
    main()