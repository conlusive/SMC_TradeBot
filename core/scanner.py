import pandas as pd


class MarketScanner:
    def __init__(self, data_fetcher):
        self.exchange = data_fetcher.exchange

    def get_hot_symbols(self, top_n: int = 5) -> list:
        """
        Сканує всю біржу в пошуках альткоїнів, куди перетікає ліквідність.
        """
        try:
            print("🔍 Сканування біржі на пошук 'гарячих' монет...")

            # Примусово завантажуємо ринки
            self.exchange.load_markets()
            tickers = self.exchange.fetch_tickers()

            data = []

            for symbol, ticker in tickers.items():
                # Bybit віддає ф'ючерси у форматі "COIN/USDT:USDT"
                if symbol.endswith(':USDT') and '-' not in symbol:

                    # Відрізаємо суфікс для краси
                    clean_symbol = symbol.split(':')[0]

                    if clean_symbol in ['USDC/USDT', 'BUSD/USDT', 'DAI/USDT']:
                        continue

                    try:
                        base_vol = float(ticker.get('baseVolume') or 0.0)
                        last_price = float(ticker.get('last') or 0.0)
                        quote_vol = float(ticker.get('quoteVolume') or 0.0)
                        perc_change = float(ticker.get('percentage') or 0.0)

                        # Розрахунок обсягу, якщо quoteVolume порожній
                        if quote_vol == 0.0 and base_vol > 0.0 and last_price > 0.0:
                            quote_vol = base_vol * last_price

                        # Фільтр за обсягом ($5 млн)
                        if quote_vol > 5000000:
                            data.append({
                                'symbol': clean_symbol,
                                'volume': quote_vol,
                                'volatility': abs(perc_change),
                                'score': quote_vol * abs(perc_change)
                            })
                    except Exception:
                        continue

            if not data:
                return ['BTC/USDT']

            df = pd.DataFrame(data)
            df = df.sort_values(by='score', ascending=False)

            return df.head(top_n)['symbol'].tolist()

        except Exception as e:
            print(f"❌ Помилка роботи сканера: {e}")
            return ['BTC/USDT']