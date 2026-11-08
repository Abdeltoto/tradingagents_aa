"""Run a TradingAgents analysis the same way the CLI does, emitting UI events."""

from __future__ import annotations

import threading
import time
import traceback
import uuid
from datetime import datetime
from functools import wraps
from pathlib import Path
from typing import Any, Callable

from cli.display import (
    ANALYST_AGENT_NAMES,
    ANALYST_ORDER,
    ANALYST_REPORT_MAP,
    AnalystWallTimeTracker,
    MessageBuffer,
    classify_message_type,
)
from cli.prompts import detect_asset_type, filter_analysts_for_asset_type, parse_analysts, parse_analysis_date, parse_ticker
from cli.models import AnalystType, AssetType
from cli.stats_handler import StatsCallbackHandler
from tradingagents.agents.rating import is_review, run_rating
from tradingagents.backtest import iter_grid, run_backtest, summarize
from tradingagents.dataflows.symbols import safe_ticker_component
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.graph.analyst_execution import build_analyst_execution_plan
from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.portfolio import PortfolioContext


Emit = Callable[[dict[str, Any]], None]


def _text(value) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        return "\n".join(str(item) for item in value)
    return str(value)


def _snapshot(buffer: MessageBuffer, stats: StatsCallbackHandler, start: float) -> dict:
    return {
        "agent_status": dict(buffer.agent_status),
        "reports": {k: _text(v) for k, v in buffer.report_sections.items() if v},
        "stats": stats.get_stats(),
        "elapsed_s": round(time.time() - start, 1),
        "completed_reports": buffer.get_completed_reports_count(),
    }


def _hook(buffer: MessageBuffer, emit: Emit, stats: StatsCallbackHandler, start: float):
    """Wrap buffer mutations so the desk sees every CLI update."""

    def after(fn_name):
        original = getattr(buffer, fn_name)

        @wraps(original)
        def wrapper(*args, **kwargs):
            original(*args, **kwargs)
            emit({"type": "snapshot", **_snapshot(buffer, stats, start)})
            return None
        return wrapper

    buffer.update_agent_status = after("update_agent_status")  # type: ignore[method-assign]
    orig_message = buffer.add_message
    orig_tool = buffer.add_tool_call
    orig_report = buffer.update_report_section

    def add_message(message_type, content):
        orig_message(message_type, content)
        timestamp, kind, text = buffer.messages[-1]
        emit({
            "type": "message",
            "timestamp": timestamp,
            "message_type": kind,
            "content": _text(text)[:8000],
            **_snapshot(buffer, stats, start),
        })

    def add_tool_call(tool_name, args):
        orig_tool(tool_name, args)
        timestamp, name, payload = buffer.tool_calls[-1]
        emit({
            "type": "tool",
            "timestamp": timestamp,
            "name": name,
            "args": payload if isinstance(payload, dict) else {"value": str(payload)},
            **_snapshot(buffer, stats, start),
        })

    def update_report_section(section_name, content):
        orig_report(section_name, content)
        emit({
            "type": "report",
            "section": section_name,
            "content": _text(buffer.report_sections.get(section_name)),
            **_snapshot(buffer, stats, start),
        })

    buffer.add_message = add_message  # type: ignore[method-assign]
    buffer.add_tool_call = add_tool_call  # type: ignore[method-assign]
    buffer.update_report_section = update_report_section  # type: ignore[method-assign]


def _update_research_team(buffer: MessageBuffer, status: str) -> None:
    for agent in ("Bull Researcher", "Bear Researcher", "Research Manager"):
        buffer.update_agent_status(agent, status)


def _update_analyst_statuses(buffer: MessageBuffer, chunk: dict, tracker: AnalystWallTimeTracker) -> None:
    from cli.display import sync_analyst_tracker_from_chunk

    sync_analyst_tracker_from_chunk(tracker, chunk)
    selected = buffer.selected_analysts
    all_filed = True
    for analyst_key in ANALYST_ORDER:
        if analyst_key not in selected:
            continue
        agent_name = ANALYST_AGENT_NAMES[analyst_key]
        report_key = ANALYST_REPORT_MAP[analyst_key]
        if chunk.get(report_key):
            buffer.update_report_section(report_key, chunk[report_key])
        if buffer.report_sections.get(report_key):
            buffer.update_agent_status(agent_name, "completed")
        else:
            buffer.update_agent_status(agent_name, "in_progress")
            all_filed = False
    if all_filed and selected and buffer.agent_status.get("Bull Researcher") == "pending":
        buffer.update_agent_status("Bull Researcher", "in_progress")


def build_run_config(body: dict) -> tuple[dict, dict]:
    """Validate a desk request the same way CLI flags are validated."""
    ticker = parse_ticker(str(body.get("ticker") or "SPY"))
    trade_date = parse_analysis_date(str(body.get("date") or datetime.now().date().isoformat()))
    asset_type = detect_asset_type(ticker)
    raw_analysts = body.get("analysts") or ["market", "social", "news", "fundamentals"]
    if isinstance(raw_analysts, list):
        raw_analysts = ",".join(raw_analysts)
    analysts = parse_analysts(raw_analysts, asset_type)
    depth = int(body.get("research_depth") or 1)
    if depth not in (1, 3, 5):
        raise ValueError("research_depth must be 1, 3 or 5")

    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = depth
    config["max_risk_discuss_rounds"] = depth
    config["quick_think_llm"] = body.get("quick_think_llm") or config["quick_think_llm"]
    config["deep_think_llm"] = body.get("deep_think_llm") or config["deep_think_llm"]
    config["llm_provider"] = (body.get("llm_provider") or config["llm_provider"]).lower()
    if body.get("backend_url"):
        config["backend_url"] = body["backend_url"]
    config["output_language"] = body.get("output_language") or config["output_language"]
    if "checkpoint_enabled" in body:
        config["checkpoint_enabled"] = bool(body["checkpoint_enabled"])

    portfolio = None
    if body.get("portfolio"):
        portfolio = PortfolioContext.model_validate(body["portfolio"])

    selections = {
        "ticker": ticker,
        "analysis_date": trade_date,
        "asset_type": asset_type.value,
        "analysts": analysts,
        "research_depth": depth,
        "llm_provider": config["llm_provider"],
        "quick_think_llm": config["quick_think_llm"],
        "deep_think_llm": config["deep_think_llm"],
        "output_language": config["output_language"],
        "portfolio": portfolio,
    }
    return config, selections


def run_analysis(body: dict, emit: Emit) -> dict:
    config, selections = build_run_config(body)
    selected_set = {analyst.value for analyst in selections["analysts"]}
    selected_analyst_keys = [a for a in ANALYST_ORDER if a in selected_set]
    plan = build_analyst_execution_plan(selected_analyst_keys)
    tracker = AnalystWallTimeTracker(plan)
    stats = StatsCallbackHandler()
    start = time.time()

    buffer = MessageBuffer()
    buffer.init_for_analysis(selected_analyst_keys)
    _hook(buffer, emit, stats, start)

    emit({
        "type": "run_started",
        "ticker": selections["ticker"],
        "date": selections["analysis_date"],
        "asset_type": selections["asset_type"],
        "analysts": selected_analyst_keys,
        "provider": config["llm_provider"],
        "quick_think_llm": config["quick_think_llm"],
        "deep_think_llm": config["deep_think_llm"],
        **_snapshot(buffer, stats, start),
    })

    graph = TradingAgentsGraph(
        selected_analyst_keys,
        config=config,
        debug=True,
        callbacks=[stats],
    )

    results_dir = Path(config["results_dir"]) / safe_ticker_component(selections["ticker"]) / selections["analysis_date"]
    results_dir.mkdir(parents=True, exist_ok=True)
    report_dir = results_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)

    buffer.add_message("System", f"Selected ticker: {selections['ticker']}")
    if selections["asset_type"] != "stock":
        buffer.add_message("System", f"Detected asset type: {selections['asset_type']}")
    buffer.add_message("System", f"Analysis date: {selections['analysis_date']}")
    buffer.add_message(
        "System",
        f"Selected analysts: {', '.join(a.value for a in selections['analysts'])}",
    )
    for spec in plan.specs:
        buffer.update_agent_status(spec.agent_node, "in_progress")
        tracker.mark_started(spec.key)

    init_state = graph.create_run_state(
        selections["ticker"],
        selections["analysis_date"],
        selections["asset_type"],
        selections["portfolio"],
    )
    args = graph.propagator.get_graph_args(callbacks=[stats])
    checkpoint_tid = graph.begin_checkpoint(
        selections["ticker"],
        selections["analysis_date"],
        selections["asset_type"],
        selections["portfolio"],
    )
    if checkpoint_tid is not None:
        args.setdefault("config", {}).setdefault("configurable", {})["thread_id"] = checkpoint_tid
        buffer.add_message(
            "System",
            f"{'Resuming' if graph._resuming else 'Starting fresh'} for {selections['ticker']} on {selections['analysis_date']}",
        )

    trace = []
    try:
        for messages, chunk in graph.stream_run(graph.checkpoint_input(init_state), **args):
            for message in messages:
                msg_id = getattr(message, "id", None)
                if msg_id is not None:
                    if msg_id in buffer._processed_message_ids:
                        continue
                    buffer._processed_message_ids.add(msg_id)
                msg_type, content = classify_message_type(message)
                if content and content.strip():
                    buffer.add_message(msg_type, content)
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        if isinstance(tool_call, dict):
                            buffer.add_tool_call(tool_call["name"], tool_call["args"])
                        else:
                            buffer.add_tool_call(tool_call.name, tool_call.args)

            if chunk is None:
                continue

            _update_analyst_statuses(buffer, chunk, tracker)

            if chunk.get("investment_debate_state"):
                debate_state = chunk["investment_debate_state"]
                bull_hist = (debate_state.get("bull_history") or "").strip()
                bear_hist = (debate_state.get("bear_history") or "").strip()
                judge = (chunk.get("investment_plan") or "").strip()
                if bull_hist or bear_hist:
                    _update_research_team(buffer, "in_progress")
                if bull_hist:
                    buffer.update_report_section("investment_plan", f"### Bull Researcher Analysis\n{bull_hist}")
                if bear_hist:
                    buffer.update_report_section("investment_plan", f"### Bear Researcher Analysis\n{bear_hist}")
                if judge:
                    buffer.update_report_section("investment_plan", f"### Research Manager Decision\n{judge}")
                    _update_research_team(buffer, "completed")
                    buffer.update_agent_status("Trader", "in_progress")

            if chunk.get("trader_investment_plan"):
                buffer.update_report_section("trader_investment_plan", chunk["trader_investment_plan"])
                if buffer.agent_status.get("Trader") != "completed":
                    buffer.update_agent_status("Trader", "completed")
                    buffer.update_agent_status("Aggressive Analyst", "in_progress")

            if chunk.get("risk_debate_state"):
                risk_state = chunk["risk_debate_state"]
                agg_hist = (risk_state.get("aggressive_history") or "").strip()
                con_hist = (risk_state.get("conservative_history") or "").strip()
                neu_hist = (risk_state.get("neutral_history") or "").strip()
                judge = (chunk.get("final_trade_decision") or "").strip()
                if agg_hist:
                    buffer.update_agent_status("Aggressive Analyst", "in_progress")
                    buffer.update_report_section("final_trade_decision", f"### Aggressive Analyst Analysis\n{agg_hist}")
                if con_hist:
                    buffer.update_agent_status("Conservative Analyst", "in_progress")
                    buffer.update_report_section("final_trade_decision", f"### Conservative Analyst Analysis\n{con_hist}")
                if neu_hist:
                    buffer.update_agent_status("Neutral Analyst", "in_progress")
                    buffer.update_report_section("final_trade_decision", f"### Neutral Analyst Analysis\n{neu_hist}")
                if judge and buffer.agent_status.get("Portfolio Manager") != "completed":
                    buffer.update_agent_status("Portfolio Manager", "in_progress")
                    buffer.update_report_section("final_trade_decision", f"### Portfolio Manager Decision\n{judge}")
                    buffer.update_agent_status("Aggressive Analyst", "completed")
                    buffer.update_agent_status("Conservative Analyst", "completed")
                    buffer.update_agent_status("Neutral Analyst", "completed")
                    buffer.update_agent_status("Portfolio Manager", "completed")

            trace.append(chunk)

        final_state = {}
        for chunk in trace:
            final_state.update(chunk)
        graph.record_decision(selections["ticker"], selections["analysis_date"], final_state)
        graph.clear_checkpoint_on_success(
            selections["ticker"], selections["analysis_date"], selections["asset_type"], selections["portfolio"]
        )
    finally:
        graph.end_checkpoint()

    for agent in buffer.agent_status:
        buffer.update_agent_status(agent, "completed")
    buffer.add_message("System", f"Completed analysis for {selections['analysis_date']}")
    buffer.add_message("System", tracker.format_summary())
    for section in buffer.report_sections:
        if section in final_state:
            buffer.update_report_section(section, final_state[section])

    report_path = graph.save_reports(final_state, selections["ticker"], html=True)
    rating = run_rating(final_state)
    result = {
        "ticker": selections["ticker"],
        "date": selections["analysis_date"],
        "rating": rating,
        "review": is_review(rating),
        "decision": _text(final_state.get("final_trade_decision")),
        "report_path": str(report_path),
        "html_report": str(Path(report_path).parent / "complete_report.html")
        if (Path(report_path).parent / "complete_report.html").exists()
        else None,
        "timings": tracker.format_summary(),
        "stats": stats.get_stats(),
        "reports": {k: _text(v) for k, v in buffer.report_sections.items() if v},
        "settings": graph.run_settings(),
    }
    emit({"type": "run_completed", **result, **_snapshot(buffer, stats, start)})
    return result


def run_backtest_job(body: dict, emit: Emit) -> dict:
    tickers = [parse_ticker(t) for t in str(body.get("tickers") or "").split(",") if t.strip()]
    if not tickers:
        raise ValueError("name at least one ticker")
    start = parse_analysis_date(str(body.get("start")))
    end = parse_analysis_date(str(body.get("end")))
    every = int(body.get("every") or 7)
    asset_type = AssetType((body.get("asset_type") or "stock").strip().lower())
    raw_analysts = body.get("analysts")
    if raw_analysts:
        if isinstance(raw_analysts, list):
            raw_analysts = ",".join(raw_analysts)
        chosen = parse_analysts(raw_analysts, asset_type)
    else:
        chosen = filter_analysts_for_asset_type(list(AnalystType), asset_type)

    config = DEFAULT_CONFIG.copy()
    if body.get("llm_provider"):
        config["llm_provider"] = body["llm_provider"]
    if body.get("quick_think_llm"):
        config["quick_think_llm"] = body["quick_think_llm"]
    if body.get("deep_think_llm"):
        config["deep_think_llm"] = body["deep_think_llm"]

    dates = iter_grid(start, end, every)
    emit({
        "type": "run_started",
        "tickers": tickers,
        "dates": dates,
        "cells": len(tickers) * len(dates),
    })

    def progress(done, total, ticker, date):
        emit({"type": "progress", "done": done, "total": total, "ticker": ticker, "date": date})

    result = run_backtest(
        tickers,
        dates,
        config,
        asset_type=asset_type.value,
        selected_analysts=[a.value for a in chosen],
        progress=progress,
        run_id=body.get("run_id"),
    )
    summary = summarize(result)
    payload = {
        "run_id": result.run_id,
        "log_path": str(result.log_path),
        "cells_run": result.cells_run,
        "skipped": result.skipped,
        "failures": result.failures,
        "settlement_failures": result.settlement_failures,
        "summary": {
            "resolved": summary.resolved,
            "pending": summary.pending,
            "unscored": summary.unscored,
            "holding": summary.holding,
            "text": summary.render(),
            "by_rating": {
                rating: {
                    "count": score.count,
                    "hit_rate": score.hit_rate,
                    "mean_alpha": score.mean_alpha,
                }
                for rating, score in summary.by_rating.items()
            },
        },
    }
    emit({"type": "run_completed", **payload})
    return payload


class JobHub:
    """In-memory live jobs plus a thin event fan-out for websockets."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self.jobs: dict[str, dict[str, Any]] = {}

    def create(self, kind: str, request: dict) -> str:
        job_id = uuid.uuid4().hex[:12]
        now = datetime.now().isoformat(timespec="seconds")
        with self._lock:
            self.jobs[job_id] = {
                "id": job_id,
                "kind": kind,
                "status": "queued",
                "request": request,
                "events": [],
                "snapshot": {},
                "result": None,
                "error": None,
                "created_at": now,
                "updated_at": now,
                "queues": [],
            }
        return job_id

    def emit(self, job_id: str, event: dict) -> None:
        event = {"ts": datetime.now().strftime("%H:%M:%S"), **event}
        with self._lock:
            job = self.jobs[job_id]
            job["events"].append(event)
            job["updated_at"] = datetime.now().isoformat(timespec="seconds")
            if event.get("type") == "run_started":
                job["status"] = "running"
            if event.get("type") == "run_completed":
                job["status"] = "completed"
                job["result"] = {k: v for k, v in event.items() if k not in {"type", "ts", "agent_status", "reports", "stats"}}
            if event.get("type") == "run_error":
                job["status"] = "error"
                job["error"] = event.get("error")
            snap_keys = ("agent_status", "reports", "stats", "elapsed_s", "completed_reports", "rating")
            job["snapshot"].update({k: event[k] for k in snap_keys if k in event})
            queues = list(job["queues"])
        for q in queues:
            q.put(event)

    def subscribe(self, job_id: str):
        import queue
        q: queue.Queue = queue.Queue()
        with self._lock:
            job = self.jobs[job_id]
            replay = list(job["events"])
            job["queues"].append(q)
        return q, replay

    def unsubscribe(self, job_id: str, q) -> None:
        with self._lock:
            job = self.jobs.get(job_id)
            if job and q in job["queues"]:
                job["queues"].remove(q)

    def public(self, job_id: str) -> dict:
        with self._lock:
            job = self.jobs[job_id]
            return {
                "id": job["id"],
                "kind": job["kind"],
                "status": job["status"],
                "request": job["request"],
                "snapshot": job["snapshot"],
                "result": job["result"],
                "error": job["error"],
                "created_at": job["created_at"],
                "updated_at": job["updated_at"],
                "event_count": len(job["events"]),
            }

    def list_jobs(self) -> list[dict]:
        with self._lock:
            ids = list(self.jobs)
        return [self.public(i) for i in reversed(ids)]

    def start(self, job_id: str, worker: Callable[[dict, Emit], dict], request: dict) -> None:
        def run():
            emit = lambda event: self.emit(job_id, event)
            try:
                worker(request, emit)
            except Exception as exc:
                emit({
                    "type": "run_error",
                    "error": str(exc),
                    "trace": traceback.format_exc()[-4000:],
                })
        threading.Thread(target=run, daemon=True, name=f"desk-{job_id}").start()


hub = JobHub()
