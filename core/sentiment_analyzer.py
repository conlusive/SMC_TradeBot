class SentimentAnalyzer:
    @staticmethod
    def analyze(sentiment_data: dict, symbol: str):
        # Якщо даних немає зовсім
        if not sentiment_data:
            return {
                'funding': 0.0,
                'status': "OFFLINE",
                'warning': "⚠️ Дані Sentiment тимчасово недоступні",
                'oi_formatted': "$0M"
            }

        funding = sentiment_data.get('funding', 0.0)
        oi_value = sentiment_data.get('oi_value', 0.0)

        status = "NORMAL"
        warning = ""

        # Визначаємо критичні рівні
        if funding >= 0.03:
            status = "EXTREME_LONG"
            warning = "⚠️ НАТОВП У ЛОНГАХ (High Risk)"
        elif funding <= -0.03:
            status = "EXTREME_SHORT"
            warning = "⚠️ НАТОВП У ШОРТАХ (Squeeze Risk)"

        return {
            'funding': round(funding, 4),
            'status': status,
            'warning': warning,
            'oi_formatted': f"${round(oi_value / 1_000_000, 1)}M"
        }