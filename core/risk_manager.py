class RiskManager:
    def __init__(self, balance_usdt: float, base_risk_pct: float = 1.0):
        self.balance = balance_usdt
        self.base_risk_pct = base_risk_pct

    def calculate_trade(self, signal_type: str, entry_price: float, recent_low: float, recent_high: float, macro_context: dict):
        multiplier = macro_context.get("multiplier", 1.0)
        if multiplier <= 0: return None

        actual_risk_pct = (self.base_risk_pct * multiplier) / 100.0
        risk_in_dollars = self.balance * actual_risk_pct

        if "BULLISH" in signal_type:
            stop_loss = recent_low * 0.998 # Невеликий відступ
            risk_per_coin = entry_price - stop_loss
        elif "BEARISH" in signal_type:
            stop_loss = recent_high * 1.002
            risk_per_coin = stop_loss - entry_price
        else: return None

        if risk_per_coin <= 0: return None
        position_size = risk_in_dollars / risk_per_coin

        # Розрахунок каскаду Тейків
        if "BULLISH" in signal_type:
            tp1 = entry_price + risk_per_coin        # RR 1:1
            tp2 = entry_price + (risk_per_coin * 2)  # RR 1:2
            tp3 = entry_price + (risk_per_coin * 3)  # RR 1:3
        else:
            tp1 = entry_price - risk_per_coin
            tp2 = entry_price - (risk_per_coin * 2)
            tp3 = entry_price - (risk_per_coin * 3)

        return {
            "entry": round(entry_price, 4),
            "stop_loss": round(stop_loss, 4),
            "tp1": round(tp1, 4), "tp2": round(tp2, 4), "tp3": round(tp3, 4),
            "position_size": round(position_size, 5),
            "risk_usd": round(risk_in_dollars, 2),
            "risk_pct": round(actual_risk_pct * 100, 2)
        }