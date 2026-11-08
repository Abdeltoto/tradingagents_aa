"""Scan on-disk CLI results so the desk can reopen past analyses."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.report_html import _TONE


def results_root() -> Path:
    return Path(DEFAULT_CONFIG["results_dir"])


def _read_json(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def list_saved_runs(limit: int = 40) -> list[dict]:
    root = results_root()
    runs: list[dict] = []
    if not root.exists():
        return runs

    for ticker_dir in root.iterdir():
        if not ticker_dir.is_dir() or ticker_dir.name in {"reports", "backtest"}:
            continue
        logs = ticker_dir / "TradingAgentsStrategy_logs"
        if logs.is_dir():
            for path in logs.glob("full_states_log_*.json"):
                data = _read_json(path)
                if not data:
                    continue
                date = data.get("trade_date") or path.stem.replace("full_states_log_", "")
                rating = data.get("final_rating")
                runs.append({
                    "id": f"disk:{ticker_dir.name}:{date}",
                    "source": "disk",
                    "ticker": data.get("company_of_interest") or ticker_dir.name,
                    "date": date,
                    "rating": rating,
                    "tone": _TONE.get(rating or "", "level"),
                    "decision": (data.get("final_trade_decision") or "")[:280],
                    "path": str(path),
                    "updated_at": datetime_from(path),
                    "html": _html_for(ticker_dir.name, date),
                })
        for date_dir in ticker_dir.iterdir():
            if not date_dir.is_dir() or date_dir.name == "TradingAgentsStrategy_logs":
                continue
            report = date_dir / "reports"
            if report.is_dir() and any(report.iterdir()):
                if any(r["ticker"] == ticker_dir.name and r["date"] == date_dir.name for r in runs):
                    continue
                runs.append({
                    "id": f"disk:{ticker_dir.name}:{date_dir.name}",
                    "source": "disk",
                    "ticker": ticker_dir.name,
                    "date": date_dir.name,
                    "rating": None,
                    "tone": "level",
                    "decision": "",
                    "path": str(report),
                    "updated_at": datetime_from(date_dir),
                    "html": _html_for(ticker_dir.name, date_dir.name),
                })

    reports = root / "reports"
    if reports.is_dir():
        for folder in reports.iterdir():
            html = folder / "complete_report.html"
            if html.exists():
                runs.append({
                    "id": f"report:{folder.name}",
                    "source": "report",
                    "ticker": folder.name.rsplit("_", 2)[0] if "_" in folder.name else folder.name,
                    "date": folder.name,
                    "rating": None,
                    "tone": "level",
                    "decision": "",
                    "path": str(folder),
                    "updated_at": datetime_from(folder),
                    "html": str(html),
                })

    runs.sort(key=lambda row: row.get("updated_at") or "", reverse=True)
    return runs[:limit]


def datetime_from(path: Path) -> str:
    try:
        return datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
    except OSError:
        return ""


def _html_for(ticker: str, date: str) -> str | None:
    root = results_root()
    candidates = [
        root / "reports",
        root / ticker / date,
        root / ticker / date / "reports",
    ]
    for folder in candidates:
        if not folder.exists():
            continue
        direct = folder / "complete_report.html"
        if direct.exists():
            return str(direct)
        if folder == root / "reports":
            for child in folder.glob(f"{ticker}_*"):
                page = child / "complete_report.html"
                if page.exists():
                    return str(page)
    return None


def load_saved_run(ticker: str, date: str) -> dict | None:
    root = results_root()
    path = root / ticker / "TradingAgentsStrategy_logs" / f"full_states_log_{date}.json"
    data = _read_json(path) if path.exists() else None
    reports = {}
    report_dir = root / ticker / date / "reports"
    if report_dir.is_dir():
        for file in report_dir.glob("*.md"):
            reports[file.stem] = file.read_text(encoding="utf-8")
    if not data and not reports:
        return None
    rating = (data or {}).get("final_rating")
    return {
        "ticker": (data or {}).get("company_of_interest") or ticker,
        "date": date,
        "rating": rating,
        "tone": _TONE.get(rating or "", "level"),
        "decision": (data or {}).get("final_trade_decision") or "",
        "reports": reports or _reports_from_state(data or {}),
        "settings": (data or {}).get("run_settings") or {},
        "html": _html_for(ticker, date),
        "path": str(path) if path.exists() else str(report_dir),
    }


def _reports_from_state(data: dict) -> dict:
    debate = data.get("investment_debate_state") or {}
    risk = data.get("risk_debate_state") or {}
    return {
        "market_report": data.get("market_report") or "",
        "sentiment_report": data.get("sentiment_report") or "",
        "news_report": data.get("news_report") or "",
        "fundamentals_report": data.get("fundamentals_report") or "",
        "investment_plan": "\n\n".join(
            part for part in (
                debate.get("bull_history"),
                debate.get("bear_history"),
                data.get("investment_plan"),
            ) if part
        ),
        "trader_investment_plan": data.get("trader_investment_plan") or "",
        "final_trade_decision": data.get("final_trade_decision") or "",
        "risk": {
            "aggressive": risk.get("aggressive_history") or "",
            "conservative": risk.get("conservative_history") or "",
            "neutral": risk.get("neutral_history") or "",
        },
    }
