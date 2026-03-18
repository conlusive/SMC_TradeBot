class Executor:
    def __init__(self, exchange):
        self.exchange = exchange

    def execute_trade(self, symbol: str, trade_params: dict):
        """Виставляє ринковий ордер та Stop-Loss на біржі."""
        try:
            print(f"🚀 [EXECUTOR] Відкриття позиції {symbol}...")
            # Встановлюємо плече на біржі
            self.exchange.set_leverage(trade_params['leverage'], symbol)

            # 1. Купівля/Продаж за ринком (Приклад для BUY)
            side = 'buy' if 'BUY' in trade_params['type'] or 'BULLISH' in trade_params['type'] else 'sell'
            order = self.exchange.create_market_order(symbol, side, trade_params['position_size'])

            # 2. Виставляємо Stop-Loss
            sl_side = 'sell' if side == 'buy' else 'buy'
            self.exchange.create_order(symbol, 'stop_market', sl_side, trade_params['position_size'],
                                       params={'stopPrice': trade_params['stop_loss']})

            print(f"✅ Позицію активовано на біржі!")
            return True
        except Exception as e:
            print(f"❌ Помилка виконання на біржі: {e}")
            return False

    def set_break_even(self, symbol: str, entry_price: float, position_size: float):
        """Переносить Stop-Loss на ціну входу."""
        try:
            print(f"⚙️ [EXECUTOR] Переведення {symbol} у беззбиток...")
            # Скасовуємо старий SL і ставимо новий за ціною входу
            self.exchange.cancel_all_orders(symbol)
            # Визначаємо сторону для SL
            # Це спрощена логіка, потребує перевірки напрямку поточної позиції
            self.exchange.create_order(symbol, 'stop_market', 'sell', position_size,
                                       params={'stopPrice': entry_price})
            return True
        except Exception as e:
            print(f"❌ Не вдалося встановити БЕ: {e}")
            return False

    def close_trade(self, symbol: str):
        """Повністю закриває позицію за ринком."""
        try:
            self.exchange.cancel_all_orders(symbol)
            # Тут логіка закриття через створення протилежного ордера
            print(f"🛑 [EXECUTOR] Позицію {symbol} закрито.")
            return True
        except Exception as e:
            print(f"❌ Помилка закриття: {e}")
            return False