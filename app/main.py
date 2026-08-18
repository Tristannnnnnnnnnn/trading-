import logging

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from app.config import load_config
from app.scheduler import alert_log, latest_data, start_scheduler

load_dotenv()
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Trading Signal Detector")
templates = Jinja2Templates(directory="templates")

config = load_config()


@app.on_event("startup")
def on_startup() -> None:
    start_scheduler(config)


@app.get("/", response_class=HTMLResponse)
def dashboard(request: Request):
    assets = sorted(latest_data.values(), key=lambda a: a["display_name"])
    signal_assets = [a for a in assets if a["status"] in ("oversold", "overbought")]
    neutral_assets = [a for a in assets if a["status"] not in ("oversold", "overbought")]
    return templates.TemplateResponse(
        "dashboard.html",
        {
            "request": request,
            "signal_assets": signal_assets,
            "neutral_assets": neutral_assets,
            "alerts": alert_log[:30],
            "thresholds": config["thresholds"],
            "refresh_seconds": config["check_interval_minutes"] * 60,
        },
    )


@app.get("/api/status")
def status():
    return {
        "assets": list(latest_data.values()),
        "alerts": alert_log[:30],
        "thresholds": config["thresholds"],
    }


@app.get("/ping")
def ping():
    """Tiny endpoint for external keep-alive pingers (cron-job.org, UptimeRobot...).
    Kept minimal on purpose: pinging "/" makes some pingers choke on the full
    dashboard HTML ("output too large") and mark the check as failed."""
    return {"status": "ok"}
