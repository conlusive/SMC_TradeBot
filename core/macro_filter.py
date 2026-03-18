import pandas as pd


class MacroFilter:
    def __init__(self, data_fetcher):
        self.fetcher = data_fetcher

    def get_market_regime(self) -> dict:
        """
        Аналізує 4-годинний таймфрейм (4h) для швидкого реагування на зливи.
        """
        # Дивимось на 4-годинний графік BTC
        df = self.fetcher.get_historical_data('BTC/USDT', '4h', limit=50)

        if df is None or len(df) < 30:
            return {"regime": "UNKNOWN", "multiplier": 1.0, "desc": "Дані недоступні для аналізу"}

        # Розрахунок середньої EMA 20 та обсягу
        df['ema_20'] = df['close'].ewm(span=20, adjust=False).mean()
        df['vol_sma_20'] = df['volume'].rolling(window=20).mean()

        last = df.iloc[-1]

        # ПЕРЕВІРКА НА ПАНІКУ (Crash Detection)
        # Якщо за останні 12 годин (3 свічки по 4г) ціна впала більше ніж на 2%
        price_change_recent = ((last['close'] - df.iloc[-4]['close']) / df.iloc[-4]['close']) * 100
        is_crashing = price_change_recent < -2.0

        is_risk_on = last['close'] > last['ema_20'] and not is_crashing
        is_high_liq = last['volume'] > last['vol_sma_20']

        # Матриця режимів згідно з твоєю філософією
        if is_risk_on and is_high_liq:
            return {
                "regime": "RISK_ON_HIGH_LIQ",
                "multiplier": 2.0,  # Режим ULTRA AGGRESSIVE (10% ризику)
                "desc": "🟢 RISK ON + Багато лікви: Ідеальний режим. Хаслимо мільйони!"
            }
        elif is_risk_on:
            return {
                "regime": "RISK_ON_LOW_LIQ",
                "multiplier": 1.0,
                "desc": "🟡 RISK ON + Мало лікви: Вибірковий ріст. Треба багато ресерчити."
            }
        elif is_crashing:
            return {
                "regime": "CRASH_DETECTION",
                "multiplier": 0.0,
                "desc": "🚨 ПАНІКА/ЗЛИВ: Ринковий обвал! Рятуємо капітал. Торги зупинено."
            }
        else:
            return {
                "regime": "RISK_OFF",
                "multiplier": 0.0,
                "desc": "🔴 RISK OFF: Ведмежий тренд або смерть ліквідності. Тільки спот/DCA."
            }