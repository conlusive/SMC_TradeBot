import requests


class NewsAnalyzer:
    def __init__(self, cryptopanic_api_key=None):
        self.api_key = cryptopanic_api_key

    def get_fear_greed_index(self):
        """Отримує Індекс Страху та Жадібності (0-100)."""
        try:
            response = requests.get("https://api.alternative.me/fng/").json()
            val = int(response['data'][0]['value'])
            classification = response['data'][0]['value_classification']
            return {"value": val, "label": classification}
        except:
            return {"value": 50, "label": "Neutral"}

    def get_news_sentiment(self):
        """
        Аналізує новинний фон через CryptoPanic.
        Повертає оцінку: > 0 (Bullish), < 0 (Bearish).
        """
        if not self.api_key:
            return 0  # Без ключа повертаємо нейтраль

        try:
            url = f"https://cryptopanic.com/api/v1/posts/?auth_token={self.api_key}&kind=news"
            response = requests.get(url).json()

            bullish = 0
            bearish = 0

            for post in response.get('results', [])[:10]:  # Дивимось останні 10 новин
                votes = post.get('votes', {})
                bullish += votes.get('bullish', 0)
                bearish += votes.get('bearish', 0)

            sentiment = bullish - bearish
            return sentiment
        except:
            return 0