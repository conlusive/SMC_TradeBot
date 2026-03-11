class Executor:
    def __init__(self, exchange_id='bybit'):
        self.exchange_id = exchange_id

    def execute_trade(self, symbol: str, trade_params: dict):
        print("\n" + "=" * 40)
        print(f"🚀 [EXECUTOR] ОТРИМАНО КОМАНДУ НА ВИКОНАННЯ!")
        print(f"Пара: {symbol}")
        print(f"Об'єм: {trade_params['position_size']}")
        print(f"Вхід: {trade_params['entry']}")
        print(f"SL: {trade_params['stop_loss']}")
        # Виводимо всі три тейки замість одного старого
        print(f"TP1: {trade_params['tp1']} | TP2: {trade_params['tp2']} | TP3: {trade_params['tp3']}")
        print("=" * 40 + "\n")
        return True

    def close_trade(self, symbol: str):
        print(f"🛑 [EXECUTOR] ЗАКРИТТЯ ПОЗИЦІЇ: {symbol}")
        return True