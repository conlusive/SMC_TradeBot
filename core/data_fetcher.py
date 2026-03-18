import ccxt
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()


class DataFetcher:
    def __init__(self, exchange_id='bybit'):
        try:
            exchange_class = getattr(ccxt, exchange_id)
            # Додаємо ключі для реальної торгівлі
            config = {
                'enableRateLimit': True,
                'apiKey': os.getenv('BYBIT_API_KEY'),
                'secret': os.getenv('BYBIT_API_SECRET'),
            }
            if exchange_id == 'bybit':
                config['options'] = {'defaultType': 'linear'}  # Для ф'ючерсів
            self.exchange = exchange_class(config)
            print(f"✅ Підключено до {exchange_id.capitalize()} (Авторизовано)")
        except Exception as e:
            print(f"❌ Помилка підключення: {e}")
            self.exchange = None

    def fetch_balance(self) -> float:
        """Отримує доступний баланс USDT."""
        try:
            balance = self.exchange.fetch_balance()
            return float(balance['total'].get('USDT', 0.0))
        except Exception as e:
            print(f"⚠️ Не вдалося отримати баланс: {e}")
            return 0.0

    def get_historical_data(self, symbol: str, timeframe: str, limit: int = 100) -> pd.DataFrame:
        if not self.exchange: return None
        fetch_symbol = symbol if ':' in symbol else f"{symbol}:USDT"
        try:
            ohlcv = self.exchange.fetch_ohlcv(fetch_symbol, timeframe, limit=limit)
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            return df
        except:
            return None

    def get_market_sentiment(self, symbol: str):
        if not self.exchange: return None
        fetch_symbol = symbol if ':' in symbol else f"{symbol}:USDT"
        try:
            ticker = self.exchange.fetch_ticker(fetch_symbol)
            info = ticker.get('info', {})
            last_price = float(ticker.get('last') or 0.0)
            funding_raw = info.get('fundingRate') or info.get('funding_rate') or 0.0

            oi_data = self.exchange.fetch_open_interest(fetch_symbol)
            oi_value = float(oi_data.get('openInterestValue') or 0.0)
            if oi_value == 0.0:
                oi_amount = float(oi_data.get('openInterestAmount') or 0.0)
                oi_value = oi_amount * last_price

            return {'funding': float(funding_raw) * 100, 'oi_value': oi_value}
        except:
            return {'funding': 0.0, 'oi_value': 0.0}