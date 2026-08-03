import numpy as np
import pandas as pd


def wilder_rma(series: pd.Series, period: int) -> pd.Series:
    """Wilder's smoothing (RMA): seeded with an SMA of the first `period`
    values, then recursively smoothed. This is what TradingView/eToro use
    for RSI, and differs from a plain EMA or SMA."""
    values = series.to_numpy(dtype=float)
    result = np.full(len(values), np.nan)
    if len(values) < period:
        return pd.Series(result, index=series.index)

    result[period - 1] = values[:period].mean()
    for i in range(period, len(values)):
        result[i] = (result[i - 1] * (period - 1) + values[i]) / period

    return pd.Series(result, index=series.index)


def compute_rsi(close: pd.Series, period: int = 14) -> pd.Series:
    """RSI(period) using Wilder's smoothing, matching TradingView/eToro."""
    delta = close.diff().dropna()  # drop() the leading NaN so it can't poison the SMA seed
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)

    avg_gain = wilder_rma(gain, period)
    avg_loss = wilder_rma(loss, period)

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    rsi[avg_loss == 0] = 100
    rsi[(avg_gain == 0) & (avg_loss == 0)] = np.nan

    return rsi.reindex(close.index)
