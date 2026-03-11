class RiskManager:
    def __init__(self, balance_usdt: float, base_risk_pct: float = 1.0, base_rr: float = 2.0):
        self.balance = balance_usdt
        self.base_risk_pct = base_risk_pct
        self.base_rr = base_rr

    def calculate_trade(self, signal_type: str, entry_price: float, recent_low: float, recent_high: float,
                        macro_context: dict):
        """
        Розраховує параметри з урахуванням глобального Макро-режиму (Macro Context).
        """
        multiplier = macro_context.get("multiplier", 1.0)
        rr_multiplier = macro_context.get("rr_multiplier", 1.0)

        # Якщо режим "СМЕРТЬ", ми взагалі не розраховуємо угоди
        if multiplier <= 0:
            return None

        # Динамічний ризик (напр. 1% * 2.0 = 2% в Risk ON High Liq)
        actual_risk_pct = (self.base_risk_pct * multiplier) / 100.0
        actual_rr = self.base_rr * rr_multiplier

        risk_in_dollars = self.balance * actual_risk_pct

        if "BULLISH" in signal_type:
            stop_loss = recent_low * 0.999
            risk_per_coin = entry_price - stop_loss
            if risk_per_coin <= 0: return None
            take_profit = entry_price + (risk_per_coin * actual_rr)

        elif "BEARISH" in signal_type:
            stop_loss = recent_high * 1.001
            risk_per_coin = stop_loss - entry_price
            if risk_per_coin <= 0: return None
            take_profit = entry_price - (risk_per_coin * actual_rr)
        else:
            return None

        position_size = risk_in_dollars / risk_per_coin

        return {
            "entry": round(entry_price, 2),
            "stop_loss": round(stop_loss, 2),
            "take_profit": round(take_profit, 2),
            "position_size": round(position_size, 5),
            "risk_usd": round(risk_in_dollars, 2),
            "actual_rr": round(actual_rr, 1),
            "risk_pct": round(actual_risk_pct * 100, 2)
        }