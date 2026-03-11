import mplfinance as mpf
import os


def create_signal_chart(df, symbol, signal_type, entry, sl, tp):
    """Генерує зображення графіка з позначеними рівнями."""
    plot_df = df.tail(50).copy()  # Беремо останні 50 свічок
    plot_df.set_index('timestamp', inplace=True)

    file_path = f"charts/{symbol.replace('/', '_')}.png"
    os.makedirs('charts', exist_ok=True)

    # Лінії рівнів
    h_lines = dict(hlines=[entry, sl, tp], colors=['blue', 'red', 'green'], linestyle='-.')

    mpf.plot(plot_df, type='candle', style='charles',
             title=f"{symbol} - {signal_type}",
             savefig=file_path,
             hlines=h_lines,
             volume=False)
    return file_path