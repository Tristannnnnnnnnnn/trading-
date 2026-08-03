import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler

from app.data_source import fetch_close_prices
from app.notifier import send_telegram_message
from app.rsi import compute_rsi

logger = logging.getLogger(__name__)

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "alert_state.json"

# In-memory snapshot the dashboard reads from.
latest_data: dict = {}


def _load_state() -> dict:
    if STATE_PATH.exists():
        with open(STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save_state(state: dict) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)


def _zone_for_rsi(rsi: float, oversold: float, overbought: float) -> str:
    if rsi <= oversold:
        return "oversold"
    if rsi >= overbought:
        return "overbought"
    return "neutral"


def check_asset(asset: dict, rsi_period: int, default_interval: str, thresholds: dict, state: dict) -> None:
    symbol = asset["yahoo_symbol"]
    interval = asset.get("interval", default_interval)

    try:
        close = fetch_close_prices(symbol, interval=interval)
        rsi_series = compute_rsi(close, period=rsi_period)
        rsi_value = float(rsi_series.dropna().iloc[-1])
    except Exception:
        logger.exception("Échec du calcul RSI pour %s", symbol)
        latest_data[symbol] = {
            **asset,
            "rsi": None,
            "status": "error",
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        return

    zone = _zone_for_rsi(rsi_value, thresholds["oversold"], thresholds["overbought"])
    previous_zone = state.get(symbol, "neutral")

    if zone != "neutral" and zone != previous_zone:
        send_telegram_message(
            f"[{asset['platform']}] {asset['display_name']}: RSI {rsi_value:.1f} "
            f"({'survente' if zone == 'oversold' else 'surachat'})"
        )

    state[symbol] = zone
    latest_data[symbol] = {
        **asset,
        "rsi": round(rsi_value, 1),
        "status": zone,
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


def run_check_cycle(config: dict) -> None:
    state = _load_state()
    for asset in config["assets"]:
        check_asset(
            asset,
            rsi_period=config["rsi_period"],
            default_interval=config["default_interval"],
            thresholds=config["thresholds"],
            state=state,
        )
    _save_state(state)


def start_scheduler(config: dict) -> BackgroundScheduler:
    run_check_cycle(config)  # immediate first pass so the dashboard isn't empty

    scheduler = BackgroundScheduler()
    scheduler.add_job(
        run_check_cycle,
        "interval",
        minutes=config["check_interval_minutes"],
        args=[config],
    )
    scheduler.start()
    return scheduler
