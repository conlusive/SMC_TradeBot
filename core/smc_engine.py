import pandas as pd


class SMCEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def add_context(self):
        self.df['ema_200'] = self.df['close'].ewm(span=200, adjust=False).mean()
        return self.df

    def identify_fvg(self):
        self.df['bullish_fvg'] = self.df['low'] > self.df['high'].shift(2)
        self.df['bearish_fvg'] = self.df['high'] < self.df['low'].shift(2)
        return self.df

    def identify_order_blocks(self):
        self.df['is_bearish_candle'] = self.df['close'] < self.df['open']
        self.df['is_bullish_candle'] = self.df['close'] > self.df['open']
        self.df['bullish_ob'] = self.df['bullish_fvg'] & self.df['is_bearish_candle'].shift(2)
        self.df['bearish_ob'] = self.df['bearish_fvg'] & self.df['is_bullish_candle'].shift(2)
        return self.df

    def identify_bos(self):
        """Пошук Зламу Структури (Break of Structure)."""
        # Знаходимо найвищий High та найнижчий Low за попередні 15 свічок
        self.df['recent_high'] = self.df['high'].shift(1).rolling(window=15).max()
        self.df['recent_low'] = self.df['low'].shift(1).rolling(window=15).min()

        # Пробій цих рівнів тілом свічки (close)
        self.df['bullish_bos'] = self.df['close'] > self.df['recent_high']
        self.df['bearish_bos'] = self.df['close'] < self.df['recent_low']
        return self.df

    def analyze(self):
        self.add_context()
        self.identify_fvg()
        self.identify_order_blocks()
        self.identify_bos()  # Додали новий метод
        return self.df

    def get_latest_signal(self):
        last = self.df.iloc[-2]
        trend = "UP" if last['close'] > last['ema_200'] else "DOWN"
        signal_data = None

        if last['bullish_bos']:
            signal_data = {"type": "BULLISH_BOS", "strength": "🔥 ЗЛАМ СТРУКТУРИ"}
        elif last['bearish_bos']:
            signal_data = {"type": "BEARISH_BOS", "strength": "🔥 ЗЛАМ СТРУКТУРИ"}
        elif last['bullish_ob'] and trend == "UP":
            signal_data = {"type": "BULLISH_OB", "strength": "💪 СИЛЬНИЙ (За трендом)"}
        elif last['bearish_ob'] and trend == "DOWN":
            signal_data = {"type": "BEARISH_OB", "strength": "💪 СИЛЬНИЙ (За трендом)"}
        elif last['bullish_fvg']:
            signal_data = {"type": "BULLISH_FVG", "strength": "👀 Звичайний (Без OB)"}
        elif last['bearish_fvg']:
            signal_data = {"type": "BEARISH_FVG", "strength": "👀 Звичайний (Без OB)"}

        if signal_data:
            signal_data["trend"] = trend
            signal_data["ema_200"] = round(last['ema_200'], 2)
            # ДОДАЄМО ЦІ ДВА РЯДКИ:
            signal_data["recent_low"] = last['recent_low']
            signal_data["recent_high"] = last['recent_high']
            return signal_data

        return None