import pandas as pd


class SMCEngine:
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()

    def identify_liquidity_sweep(self):
        """Шукає 'закол' рівня: ціна виходить за хай/лой і повертається."""
        prev_high = self.df['high'].shift(1).rolling(window=10).max()
        prev_low = self.df['low'].shift(1).rolling(window=10).min()

        # Буліш: Low нижче попереднього, але Close вище
        self.df['bull_sweep'] = (self.df['low'] < prev_low) & (self.df['close'] > prev_low)
        # Беріш: High вище попереднього, але Close нижче
        self.df['bear_sweep'] = (self.df['high'] > prev_high) & (self.df['close'] < prev_high)

    def analyze(self):
        self.df['ema_200'] = self.df['close'].ewm(span=200, adjust=False).mean()
        self.identify_liquidity_sweep()

        # Стандартні SMC інструменти
        self.df['bullish_fvg'] = self.df['low'] > self.df['high'].shift(2)
        self.df['bearish_fvg'] = self.df['high'] < self.df['low'].shift(2)

        self.df['recent_high'] = self.df['high'].shift(1).rolling(window=15).max()
        self.df['recent_low'] = self.df['low'].shift(1).rolling(window=15).min()
        self.df['bullish_bos'] = self.df['close'] > self.df['recent_high']
        self.df['bearish_bos'] = self.df['close'] < self.df['recent_low']
        return self.df

    def get_latest_signal(self):
        last = self.df.iloc[-2]
        signal = None

        # Надаємо перевагу зняттю ліквідності (найсильніший сигнал)
        if last['bull_sweep']:
            signal = {"type": "LIQUIDITY_SWEEP_BUY", "strength": "💎 SMART MONEY ENTRY"}
        elif last['bear_sweep']:
            signal = {"type": "LIQUIDITY_SWEEP_SELL", "strength": "💎 SMART MONEY ENTRY"}
        elif last['bullish_bos']:
            signal = {"type": "BULLISH_BOS", "strength": "🔥 ЗЛАМ СТРУКТУРИ"}
        elif last['bearish_bos']:
            signal = {"type": "BEARISH_BOS", "strength": "🔥 ЗЛАМ СТРУКТУРИ"}

        if signal:
            signal.update({"recent_low": last['recent_low'], "recent_high": last['recent_high']})
        return signal