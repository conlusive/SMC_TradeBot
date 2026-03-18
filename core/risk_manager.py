class RiskManager:
    def __init__(self, balance_usdt: float, base_risk_pct: float = 1.0):
        self.balance = balance_usdt
        self.base_risk_pct = base_risk_pct

    def calculate_trade(self, signal_type: str, entry_price: float, recent_low: float, recent_high: float,
                        macro_context: dict):
        regime = macro_context.get("regime", "UNKNOWN")
        multiplier = macro_context.get("multiplier", 1.0)

        if multiplier <= 0: return None

        # --- ЛОГІКА ULTRA AGGRESSIVE ---
        if regime == "RISK_ON_HIGH_LIQ":
            # 10% РИЗИКУ (Для розгону малих депозитів)
            actual_risk_pct = 10.0 / 100.0
            margin_usage_pct = 0.80  # Використовуємо до 80% банку під маржу
        else:
            # Стандартний ризик 1-2% для захисту
            actual_risk_pct = (self.base_risk_pct * multiplier) / 100.0
            margin_usage_pct = 0.20

        risk_in_dollars = self.balance * actual_risk_pct

        if "BULLISH" in signal_type or "BUY" in signal_type:
            stop_loss = recent_low * 0.998
            risk_per_coin = entry_price - stop_loss
        else:
            stop_loss = recent_high * 1.002
            risk_per_coin = stop_loss - entry_price

        if risk_per_coin <= 0: return None

        position_size = risk_in_dollars / risk_per_coin
        notional_value = position_size * entry_price

        # Розрахунок плеча
        leverage = notional_value / (self.balance * margin_usage_pct)
        leverage = round(min(max(leverage, 1.0), 50.0), 1)

        reward = risk_per_coin
        if "BULLISH" in signal_type or "BUY" in signal_type:
            tp1, tp2, tp3 = entry_price + reward, entry_price + reward * 2, entry_price + reward * 3
        else:
            tp1, tp2, tp3 = entry_price - reward, entry_price - reward * 2, entry_price - reward * 3

        return {
            "entry": round(entry_price, 5),
            "stop_loss": round(stop_loss, 5),
            "tp1": round(tp1, 5), "tp2": round(tp2, 5), "tp3": round(tp3, 5),
            "position_size": round(position_size, 3),
            "leverage": leverage,
            "risk_usd": round(risk_in_dollars, 2),
            "risk_pct": round(actual_risk_pct * 100, 2)
        }