import logging

import pandas as pd
import yfinance as yf

logger = logging.getLogger(__name__)


def fetch_close_prices(symbol: str, interval: str = "1d", lookback: str = "6mo") -> pd.Series:
    """Fetch closing prices for `symbol` from Yahoo Finance.

    `lookback` must give enough bars for Wilder's RMA to warm up
    (roughly 100+ bars recommended for a period-14 RSI to stabilize).
    """
    data = yf.download(
        symbol,
        period=lookback,
        interval=interval,
        progress=False,
        auto_adjust=True,
    )
    if data.empty:
        raise ValueError(f"Aucune donnée reçue pour {symbol}")

    close = data["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    return close.dropna()
