import ccxt
import pandas as pd


class DataFetcher:
    def __init__(self, exchange_id='binance'):
        """
        Ініціалізація підключення до біржі.
        За замовчуванням використовуємо Binance, але можна передати 'bybit', 'okx' тощо.
        """
        try:
            # Динамічно отримуємо клас біржі з ccxt
            exchange_class = getattr(ccxt, exchange_id)
            self.exchange = exchange_class({
                'enableRateLimit': True,  # Життєво важливо! Захищає від бану за часті запити
            })
            print(f"Успішно підключено до {exchange_id.capitalize()}")
        except AttributeError:
            print(f"Помилка: Біржа {exchange_id} не підтримується ccxt.")
            self.exchange = None

    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        """
        Отримує історичні свічки з біржі та перетворює їх у Pandas DataFrame.
        """
        if not self.exchange:
            return None

        try:
            # fetch_ohlcv повертає сирий масив: [timestamp, open, high, low, close, volume]
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

            # Перетворюємо масив у зручну таблицю
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Перетворюємо час з мілісекунд у зрозумілий формат (рік-місяць-день година:хвилина)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            return df

        except ccxt.NetworkError as e:
            print(f"Помилка мережі при запиті до біржі: {e}")
        except ccxt.ExchangeError as e:
            print(f"Помилка біржі (можливо неправильний символ): {e}")
        except Exception as e:
            print(f"Невідома помилка: {e}")

        return None