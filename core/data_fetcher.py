import ccxt
import pandas as pd


class DataFetcher:
    def __init__(self, exchange_id='binance'):
        """
        Ініціалізація підключення до біржі.
        """
        try:
            exchange_class = getattr(ccxt, exchange_id)

            # Налаштування для Bybit, щоб він працював з ф'ючерсами (linear)
            config = {
                'enableRateLimit': True,
            }
            if exchange_id == 'bybit':
                config['options'] = {'defaultType': 'linear'}

            self.exchange = exchange_class(config)
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

        # Bybit вимагає суфікс :USDT для ф'ючерсних символів.
        # Оскільки сканер віддає очищені символи (напр. PIXEL/USDT),
        # ми додаємо суфікс назад перед запитом до біржі.
        fetch_symbol = symbol if ':' in symbol else f"{symbol}:USDT"

        try:
            # Використовуємо fetch_symbol з правильним суфіксом
            ohlcv = self.exchange.fetch_ohlcv(fetch_symbol, timeframe, limit=limit)

            # Перетворюємо масив у зручну таблицю
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])

            # Перетворюємо час з мілісекунд у зрозумілий формат
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

            return df

        except ccxt.NetworkError as e:
            print(f"Помилка мережі при запиті до біржі: {e}")
        except ccxt.ExchangeError as e:
            print(f"Помилка біржі ({fetch_symbol}): {e}")
        except Exception as e:
            print(f"Невідома помилка: {e}")

        return None