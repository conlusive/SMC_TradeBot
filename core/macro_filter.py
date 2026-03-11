import pandas as pd


class MacroFilter:
    def __init__(self, data_fetcher):
        self.fetcher = data_fetcher

    def get_market_regime(self) -> dict:
        """
        Аналізує Денний таймфрейм (1d) Біткоїна для визначення фази ринку.
        Повертає словник з назвою режиму, описом та мультиплікатором ризику.
        """
        # Завжди дивимось на BTC для загального фону ринку
        df = self.fetcher.get_historical_data('BTC/USDT', '1d', limit=100)

        if df is None or len(df) < 50:
            return {"regime": "UNKNOWN", "multiplier": 1.0, "desc": "Немає даних для аналізу"}

        # Рахуємо Денну EMA 50 та Середній обсяг за 14 днів
        df['ema_50'] = df['close'].ewm(span=50, adjust=False).mean()
        df['vol_sma_14'] = df['volume'].rolling(window=14).mean()

        last_closed = df.iloc[-2]  # Беремо останній закритий день

        # Умови
        is_risk_on = last_closed['close'] > last_closed['ema_50']
        is_high_liq = last_closed['volume'] > last_closed['vol_sma_14']

        # Матриця з 4 режимів за твоєю філософією
        if is_risk_on and is_high_liq:
            return {
                "regime": "RISK_ON_HIGH_LIQ",
                "multiplier": 2.0,  # Збільшуємо ризик в 2 рази (агресивно)
                "rr_multiplier": 1.5,  # Ставимо довші тейки (напр. 1:3 замість 1:2)
                "desc": "🟢 RISK ON + Багато лікві: Ідеальний режим, гроші ллються рікою. Агресивні торги."
            }
        elif is_risk_on and not is_high_liq:
            return {
                "regime": "RISK_ON_LOW_LIQ",
                "multiplier": 1.0,  # Стандартний ризик
                "rr_multiplier": 1.0,
                "desc": "🟡 RISK ON + Мало лікві: Вибірковий ріст. Треба думати і ресерчити. Стандартні торги."
            }
        elif not is_risk_on and is_high_liq:
            return {
                "regime": "RISK_OFF_HIGH_LIQ",
                "multiplier": 0.5,  # Ріжемо ризик навпіл (торгуємо дуже обережно)
                "rr_multiplier": 0.8,  # Тейки коротші
                "desc": "🟠 RISK OFF + Злив/Волатильність: Небезпечний ринок, швидкі рухи вниз. Зменшений ризик."
            }
        else:
            return {
                "regime": "RISK_OFF_LOW_LIQ",
                "multiplier": 0.0,  # ЗАБОРОНА ТОРГІВЛІ
                "rr_multiplier": 0.0,
                "desc": "🔴 RISK OFF + Смерть (Мало лікві): Ринок мертвий. Збереження капіталу. Торгівлю зупинено."
            }