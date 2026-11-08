"""FastAPI desk: same TradingAgents engine as the CLI, with a visual front-end."""

from __future__ import annotations

import asyncio
import os
import queue
from pathlib import Path

from dotenv import find_dotenv, set_key
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from webui.catalog import detect_ticker_kind, meta
from webui.history import list_saved_runs, load_saved_run, results_root
from webui.runner import hub, run_analysis, run_backtest_job

STATIC = Path(__file__).parent / "static"

app = FastAPI(title="TradingDesk", version="0.1.0")
app.mount("/static", StaticFiles(directory=STATIC), name="static")


class AnalysisRequest(BaseModel):
    ticker: str = "SPY"
    date: str | None = None
    analysts: list[str] = Field(default_factory=lambda: ["market", "social", "news", "fundamentals"])
    research_depth: int = 1
    llm_provider: str | None = None
    quick_think_llm: str | None = None
    deep_think_llm: str | None = None
    backend_url: str | None = None
    output_language: str = "English"
    checkpoint_enabled: bool = False
    portfolio: dict | None = None


class BacktestRequest(BaseModel):
    tickers: str
    start: str
    end: str
    every: int = 7
    analysts: list[str] | None = None
    asset_type: str = "stock"
    llm_provider: str | None = None
    quick_think_llm: str | None = None
    deep_think_llm: str | None = None
    run_id: str | None = None


class SettingsPatch(BaseModel):
    values: dict[str, str]


@app.get("/", response_class=HTMLResponse)
def index():
    return (STATIC / "index.html").read_text(encoding="utf-8")


@app.get("/api/meta")
def api_meta():
    return meta()


@app.get("/api/quote/{ticker}")
def api_quote(ticker: str):
    try:
        import yfinance as yf

        from cli.prompts import parse_ticker

        symbol = parse_ticker(ticker)
        info = yf.Ticker(symbol).fast_info
        last = getattr(info, "last_price", None)
        prev = getattr(info, "previous_close", None)
        change = None
        if last is not None and prev:
            change = (last - prev) / prev
        return {
            "ticker": symbol,
            "asset_type": detect_ticker_kind(symbol),
            "last": last,
            "previous_close": prev,
            "change": change,
            "currency": getattr(info, "currency", None),
            "exchange": getattr(info, "exchange", None),
        }
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/runs")
def api_runs():
    live = hub.list_jobs()
    saved = list_saved_runs()
    return {"live": live, "saved": saved}


@app.get("/api/runs/{job_id}")
def api_run(job_id: str):
    if job_id.startswith("disk:"):
        _, ticker, date = job_id.split(":", 2)
        data = load_saved_run(ticker, date)
        if not data:
            raise HTTPException(status_code=404, detail="saved run not found")
        return {"id": job_id, "kind": "analysis", "status": "completed", "result": data, "snapshot": data}
    if job_id not in hub.jobs:
        raise HTTPException(status_code=404, detail="run not found")
    return hub.public(job_id)


@app.get("/api/history/{ticker}/{date}")
def api_history(ticker: str, date: str):
    data = load_saved_run(ticker, date)
    if not data:
        raise HTTPException(status_code=404, detail="saved run not found")
    return data


@app.get("/api/reports/file")
def api_report_file(path: str):
    target = Path(path).resolve()
    root = results_root().resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=403, detail="path outside results directory")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    media = "text/html" if target.suffix == ".html" else "text/markdown"
    return FileResponse(target, media_type=media)


@app.post("/api/runs")
def api_start_run(body: AnalysisRequest):
    payload = body.model_dump()
    job_id = hub.create("analysis", payload)
    hub.start(job_id, run_analysis, payload)
    return hub.public(job_id)


@app.post("/api/backtests")
def api_start_backtest(body: BacktestRequest):
    payload = body.model_dump()
    job_id = hub.create("backtest", payload)
    hub.start(job_id, run_backtest_job, payload)
    return hub.public(job_id)


@app.websocket("/api/ws/runs/{job_id}")
async def ws_run(websocket: WebSocket, job_id: str):
    if job_id not in hub.jobs:
        await websocket.close(code=4404)
        return
    await websocket.accept()
    q, replay = hub.subscribe(job_id)
    try:
        for event in replay:
            await websocket.send_json(event)
        while True:
            try:
                event = await asyncio.to_thread(q.get, True, 20.0)
            except queue.Empty:
                await websocket.send_json({"type": "ping"})
                continue
            await websocket.send_json(event)
            if event.get("type") in {"run_completed", "run_error"}:
                break
    except WebSocketDisconnect:
        pass
    finally:
        hub.unsubscribe(job_id, q)


@app.get("/api/settings")
def api_settings():
    info = meta()
    keys = {}
    for env_name in info["key_env"].values():
        raw = os.environ.get(env_name, "")
        keys[env_name] = {"present": bool(raw.strip()), "hint": _mask(raw)}
    trading = {
        name: os.environ.get(name, "")
        for name in (
            "TRADINGAGENTS_LLM_PROVIDER",
            "TRADINGAGENTS_QUICK_THINK_LLM",
            "TRADINGAGENTS_DEEP_THINK_LLM",
            "TRADINGAGENTS_OUTPUT_LANGUAGE",
            "OLLAMA_BASE_URL",
        )
    }
    return {"keys": keys, "trading": trading, "env_file": find_dotenv(usecwd=True) or str(Path(".env").resolve())}


@app.post("/api/settings")
def api_save_settings(body: SettingsPatch):
    env_path = find_dotenv(usecwd=True) or str(Path(".env").resolve())
    if not Path(env_path).exists():
        Path(env_path).write_text("", encoding="utf-8")
    allowed_prefix = ("TRADINGAGENTS_", "OLLAMA_", "OPENAI_", "ANTHROPIC_", "GOOGLE_", "XAI_",
                      "DEEPSEEK_", "DASHSCOPE_", "ZHIPU_", "MINIMAX_", "OPENROUTER_",
                      "MISTRAL_", "MOONSHOT_", "GROQ_", "NVIDIA_", "FRED_", "TYPESAFE_",
                      "OPENAI_COMPATIBLE_", "AWS_")
    saved = []
    for name, value in body.values.items():
        if not name.isidentifier() and "_" not in name:
            continue
        if not name.startswith(allowed_prefix) and name not in meta()["key_env"].values():
            continue
        set_key(env_path, name, value or "")
        if value:
            os.environ[name] = value
        elif name in os.environ:
            del os.environ[name]
        saved.append(name)
    return {"saved": saved, "env_file": env_path}


def _mask(value: str) -> str:
    value = value.strip()
    if not value:
        return ""
    if len(value) <= 6:
        return "••••"
    return f"{value[:3]}••••{value[-2:]}"
