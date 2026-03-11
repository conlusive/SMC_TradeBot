import time


class DCAInvestor:
    def __init__(self, exchange, targets=None):
        self.exchange = exchange
        # Монети для відкупу "дна"
        self.targets = targets or ['ETH/USDT', 'SOL/USDT', 'LINK/USDT', 'NEAR/USDT']
        self.last_buy_time = 0
        self.cooldown = 86400  # 24 години

    def execute_dca(self, balance_usdt: float):
        current_time = time.time()

        if current_time - self.last_buy_time < self.cooldown:
            return None

        investment_amount = balance_usdt * 0.05
        if investment_amount < 10:
            return "LOW_BALANCE"

        buy_results = []
        amount_per_coin = investment_amount / len(self.targets)

        print(f"📉 Режим DCA: закупка на суму ${round(investment_amount, 2)}")

        for symbol in self.targets:
            try:
                # Виконуємо покупку на спотовому ринку
                order = self.exchange.create_market_buy_order(
                    symbol,
                    amount_per_coin,
                    params={'type': 'spot'}
                )
                buy_results.append(f"✅ {symbol}: куплено на ${round(amount_per_coin, 2)}")
            except Exception as e:
                buy_results.append(f"❌ {symbol}: помилка {str(e)}")

        self.last_buy_time = current_time
        return buy_results