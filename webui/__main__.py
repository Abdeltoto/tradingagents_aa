"""Launch the visual desk: python -m webui"""

from __future__ import annotations

import argparse
import webbrowser


def main() -> None:
    parser = argparse.ArgumentParser(description="TradingDesk — visual TradingAgents platform")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8787)
    parser.add_argument("--no-browser", action="store_true")
    args = parser.parse_args()

    import uvicorn

    url = f"http://{args.host}:{args.port}"
    if not args.no_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass
    print(f"TradingDesk → {url}")
    uvicorn.run("webui.app:app", host=args.host, port=args.port, log_level="info")


if __name__ == "__main__":
    main()
