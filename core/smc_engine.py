import pandas as pd


class SMCEngine:
    def __init__(self, df: pd.DataFrame):
        """
        Ініціалізуємо двигун, передаючи йому таблицю зі свічками.
        """
        # Робимо копію, щоб не змінювати оригінальні дані випадково
        self.df = df.copy()

    def identify_fvg(self) -> pd.DataFrame:
        """
        Алгоритм пошуку Fair Value Gap (Імбалансу).
        Використовує метод .shift(2) для порівняння поточної свічки зі свічкою 2 кроки тому.
        """
        # 1. Бичачий FVG: поточний Low > High свічки, що була 2 періоди тому
        self.df['bullish_fvg'] = self.df['low'] > self.df['high'].shift(2)

        # 2. Ведмежий FVG: поточний High < Low свічки, що була 2 періоди тому
        self.df['bearish_fvg'] = self.df['high'] < self.df['low'].shift(2)

        return self.df

    def get_latest_signal(self):
        """
        Перевіряє, чи є FVG на ОСТАННІЙ ЗАКРИТІЙ свічці (індекс -2).
        Остання свічка (індекс -1) ще формується, її не можна аналізувати!
        """
        # Аналізуємо свічку, яка щойно закрилася
        last_closed_candle = self.df.iloc[-2]

        if last_closed_candle['bullish_fvg']:
            return "BULLISH_FVG"
        elif last_closed_candle['bearish_fvg']:
            return "BEARISH_FVG"

        return None