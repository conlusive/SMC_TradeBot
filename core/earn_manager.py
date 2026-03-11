class EarnManager:
    def __init__(self, exchange):
        self.exchange = exchange

    def park_funds(self, amount: float):
        """Переказує USDT в Savings (через Funding account)."""
        try:
            # На Bybit це зазвичай переказ з Unified/Spot на Funding
            print(f"🅿️ Паркування ${amount} у Bybit Savings...")
            return self.exchange.transfer(code='USDT', amount=amount, fromAccount='UNIFIED', toAccount='FUND')
        except Exception as e:
            print(f"❌ Помилка паркування: {e}")

    def withdraw_funds(self, amount: float):
        """Повертає кошти для торгівлі."""
        try:
            print(f"⚡️ Виведення ${amount} для активної угоди...")
            return self.exchange.transfer(code='USDT', amount=amount, fromAccount='FUND', toAccount='UNIFIED')
        except Exception as e:
            print(f"❌ Помилка виведення: {e}")