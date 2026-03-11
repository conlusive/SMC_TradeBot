import ccxt
import pandas as pd


class DataFetcher:
    def __init__(self, exchange_id='bybit'):
        try:
            exchange_class = getattr(ccxt, exchange_id)
            config = {'enableRateLimit': True}
            if exchange_id == 'bybit':
                config['options'] = {'defaultType': 'linear'}
            self.exchange = exchange_class(config)
            print(f"Успішно підключено до {exchange_id.capitalize()}")
        except AttributeError:
            self.exchange = None

    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        if not self.exchange: return None
        fetch_symbol = symbol if ':' in symbol else f"{symbol}:USDT"
        try:
            ohlcv = self.exchange.fetch_ohlcv(fetch_symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except Exception:
            return None

    def get_market_sentiment(self, symbol: str):
        """
        Отримує Funding Rate та Open Interest з автоматичним розрахунком вартості.
        """
        if not self.exchange: return None
        fetch_symbol = symbol if ':' in symbol else f"{symbol}:USDT"
        try:
            # Отримуємо ціну та фандінг
            ticker = self.exchange.fetch_ticker(fetch_symbol)
            info = ticker.get('info', {})
            last_price = float(ticker.get('last') or 0.0)

            # Безпечне отримання фандінгу
            funding_raw = info.get('fundingRate') or info.get('funding_rate') or 0.0

            oi_value = 0.0
            try:
                # Отримуємо дані про відкритий інтерес
                oi_data = self.exchange.fetch_open_interest(fetch_symbol)

                # 1. Пробуємо взяти готове значення в USDT (Value)
                oi_value = float(oi_data.get('openInterestValue') or 0.0)

                # 2. Якщо Value немає, беремо кількість монет (Amount) і множимо на ціну
                if oi_value == 0.0:
                    oi_amount = float(oi_data.get('openInterestAmount') or 0.0)
                    oi_value = oi_amount * last_price
            except:
                pass

            return {
                'funding': float(funding_raw) * 100,
                'oi_value': oi_value
            }
        except Exception as e:
            print(f"⚠️ Помилка отримання даних Sentiment для {fetch_symbol}")
            return {'funding': 0.0, 'oi_value': 0.0}