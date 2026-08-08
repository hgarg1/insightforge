"""Launch the desktop client with a local API."""

from __future__ import annotations

import argparse

from insightforge.api.server import start_local_api


def main() -> None:
    parser = argparse.ArgumentParser(description="Launch InsightForge")
    parser.add_argument("--api-only", action="store_true", help="Run only the local API")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()

    if args.api_only:
        from insightforge.api.server import run

        run(host="127.0.0.1", port=args.port)
        return

    start_local_api(port=args.port)
    from insightforge.ui.app import run_app

    run_app()


if __name__ == "__main__":
    main()
