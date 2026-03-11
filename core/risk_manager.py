class RiskManager:
    def __init__(self, balance_usdt: float, risk_per_trade_pct: float = 1.0, reward_ratio: float = 2.0):
        """
        balance_usdt: Твій тестовий баланс (наприклад, 1000$)
        risk_per_trade_pct: Відсоток ризику на одну угоду (за замовчуванням 1%)
        reward_ratio: Відношення прибутку до ризику (Risk/Reward). 2.0 означає угоди 1 до 2.
        """
        self.balance = balance_usdt
        self.risk_pct = risk_per_trade_pct / 100.0
        self.rr = reward_ratio

    def calculate_trade(self, signal_type: str, entry_price: float, recent_low: float, recent_high: float):
        """
        Розраховує всі параметри майбутньої угоди.
        """
        # Скільки доларів ми готові втратити в найгіршому випадку
        risk_in_dollars = self.balance * self.risk_pct

        # Визначаємо Stop-Loss (трохи за екстремумом для безпеки)
        if "BULLISH" in signal_type:
            # Для лонгу стоп ставимо трохи нижче останнього мінімуму
            stop_loss = recent_low * 0.999  # Відступ 0.1% від мінімуму
            risk_per_coin = entry_price - stop_loss

            if risk_per_coin <= 0: return None  # Захист від помилок

            take_profit = entry_price + (risk_per_coin * self.rr)

        elif "BEARISH" in signal_type:
            # Для шорту стоп ставимо трохи вище останнього максимуму
            stop_loss = recent_high * 1.001  # Відступ 0.1% від максимуму
            risk_per_coin = stop_loss - entry_price

            if risk_per_coin <= 0: return None

            take_profit = entry_price - (risk_per_coin * self.rr)
        else:
            return None

        # Розраховуємо розмір позиції (скільки монет BTC купити)
        position_size = risk_in_dollars / risk_per_coin

        return {
            "entry": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "position_size": round(position_size, 5),  # 5 знаків після коми для крипти
            "risk_usd": round(risk_in_dollars, 2)
        }