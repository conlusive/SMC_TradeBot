import pandas as pd
from core.news_analyzer import NewsAnalyzer  # Передбачається наявність цього модуля


class MacroFilter:
    def __init__(self, data_fetcher):
        self.fetcher = data_fetcher
        self.news_analyzer = NewsAnalyzer()

    def get_market_regime(self) -> dict:
        """
        Аналізує ринок на двох рівнях: 1 день (Глобальний тренд) та 4 години (Локальний настрій).
        Враховує Індекс Страху та Жадібності для коригування ризиків.
        """
        # 1. Отримуємо дані
        df_1d = self.fetcher.get_historical_data('BTC/USDT', '1d', limit=100)
        df_4h = self.fetcher.get_historical_data('BTC/USDT', '4h', limit=100)

        if df_1d is None or df_4h is None or len(df_1d) < 50:
            return {"regime": "UNKNOWN", "multiplier": 1.0, "desc": "⚠️ Очікування даних..."}

        # 2. Глобальний тренд (1 день)
        ema_50_1d = df_1d['close'].ewm(span=50, adjust=False).mean().iloc[-2]
        price_1d = df_1d['close'].iloc[-2]

        # 3. Локальний настрій (4 години)
        ema_50_4h = df_4h['close'].ewm(span=50, adjust=False).mean().iloc[-2]
        price_4h = df_4h['close'].iloc[-2]

        # 4. Ліквідність (Обсяги за 14 днів)
        vol_sma_14 = df_1d['volume'].rolling(window=14).mean().iloc[-2]
        current_vol = df_1d['volume'].iloc[-2]

        # 5. Sentiment Filter (Fear & Greed)
        fng = self.news_analyzer.get_fear_greed_index()
        fng_multiplier = 1.0
        if fng['value'] > 80:
            fng_multiplier = 0.5  # Extreme Greed (захист від перегріву)
        elif fng['value'] < 20:
            fng_multiplier = 1.2  # Extreme Fear (потенційне дно)

        is_global_bullish = price_1d > ema_50_1d
        is_local_bullish = price_4h > ema_50_4h
        is_high_liq = current_vol > vol_sma_14

        # МАТРИЦЯ РЕЖИМІВ ЗА ФІЛОСОФІЄЮ
        if is_global_bullish and is_local_bullish and is_high_liq:
            return {
                "regime": "RISK_ON_HIGH_LIQ",
                "multiplier": 2.0 * fng_multiplier,
                "desc": "🟢 RISK ON + Багато лікві: Ідеальний режим, агресивний хасл мільйонів."
            }

        elif is_global_bullish and not is_local_bullish:
            return {
                "regime": "BULL_MARKET_CORRECTION",
                "multiplier": 0.3,  # Різко ріжемо ризик під час зливу
                "desc": "🟡 КОРЕКЦІЯ: Глобальний тренд вверх, але локально ринок падає. Будь обережним."
            }

        elif not is_global_bullish and is_high_liq:
            return {
                "regime": "RISK_OFF_HIGH_LIQ",
                "multiplier": 0.5 * fng_multiplier,
                "desc": "🟠 RISK OFF + Паніка: Ведмежий ринок з великими обсягами. Тільки короткі скальп-угоди."
            }

        else:
            return {
                "regime": "RISK_OFF_LOW_LIQ",
                "multiplier": 0.0,
                "desc": "🔴 СМЕРТЬ: Ринок мертвий або летить у прірву без ліквідності. Торгівлю зупинено."
            }