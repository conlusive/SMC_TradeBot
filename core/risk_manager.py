class RiskManager:
    def __init__(self, balance_usdt: float, base_risk_pct: float = 1.0):
        self.balance = balance_usdt
        self.base_risk_pct = base_risk_pct

    def calculate_trade(self, signal_type: str, entry_price: float, recent_low: float, recent_high: float,
                        macro_context: dict):
        multiplier = macro_context.get("multiplier", 1.0)
        if multiplier <= 0: return None

        # Розраховуємо ризик у доларах (наприклад, $10 від $1000)
        actual_risk_pct = (self.base_risk_pct * multiplier) / 100.0
        risk_in_dollars = self.balance * actual_risk_pct

        # Визначаємо Stop-Loss
        if "BULLISH" in signal_type:
            stop_loss = recent_low * 0.998
            risk_per_coin = entry_price - stop_loss
        else:
            stop_loss = recent_high * 1.002
            risk_per_coin = stop_loss - entry_price

        if risk_per_coin <= 0: return None

        # РОЗРАХУНОК ОБ'ЄМУ ТА ПЛЕЧА
        position_size = risk_in_dollars / risk_per_coin
        notional_value = position_size * entry_price  # Загальна вартість позиції

        # Ми хочемо використовувати максимум 10% балансу як маржу (заставу)
        allocated_margin = self.balance * 0.1
        leverage = notional_value / allocated_margin

        # Обмеження плеча (наприклад, не більше 50x)
        leverage = min(max(leverage, 1.0), 50.0)

        # Каскадні тейки
        reward = risk_per_coin
        if "BULLISH" in signal_type:
            tp1, tp2, tp3 = entry_price + reward, entry_price + reward * 2, entry_price + reward * 3
        else:
            tp1, tp2, tp3 = entry_price - reward, entry_price - reward * 2, entry_price - reward * 3

        return {
            "entry": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5),
            "tp1": round(tp1, 5), "tp2": round(tp2, 5), "tp3": round(tp3, 5),
            "position_size": round(position_size, 2),
            "leverage": round(leverage, 1),  # Твоє розумне плече
            "risk_usd": round(risk_in_dollars, 2),
            "risk_pct": round(actual_risk_pct * 100, 2)
        }