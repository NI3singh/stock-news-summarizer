"""QuantMind v2 — command-line interface (primary entry point).

Five subcommands: analyze, add-ticker, remove-ticker, list-tickers, run-scheduler.
Run as ``python quantmind/main.py <command> ...`` or, since the package is
installed editable, as ``quantmind <command> ...``.
"""
import argparse
import asyncio
import sys

from quantmind.config import settings
from quantmind.memory import DatabaseManager
from quantmind.pipeline import DailyScheduler, PipelineRunner

# The analyze output uses Unicode box-drawing / em-dash; make sure a non-UTF-8
# console (e.g. a Windows pipe defaulting to cp1252) doesn't raise on encode.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # pragma: no cover — non-reconfigurable stream
    pass

_RULE = "─" * 60


# --- Command handlers --------------------------------------------------------

async def cmd_analyze(args: argparse.Namespace) -> None:
    runner = PipelineRunner()
    results = await runner.analyze_all([t.upper() for t in args.tickers])

    if not results:
        print("No analyses produced (all tickers failed — see logs).")
        return

    for ta in results:
        # quant is Optional — the orchestrator stores None when the quant agent
        # fails, so the signals line must not assume it exists.
        if ta.quant is not None:
            s = ta.quant.signals
            signals_line = (
                f"SIGNALS: RSI={s.rsi or 'N/A'}  MACD={s.macd or 'N/A'}  "
                f"Vol Ratio={s.volume_ratio or 'N/A'}"
            )
        else:
            signals_line = "SIGNALS: N/A (quant analysis unavailable)"

        print(_RULE)
        print(f"TICKER: {ta.ticker}  |  {ta.analyzed_at.strftime('%Y-%m-%d %H:%M')}")
        print(
            f"Sentiment: {ta.news.sentiment_score:+.2f}  |  "
            f"Days of History: {ta.memory.days_of_history}"
        )
        print(f"Themes: {', '.join(ta.news.key_themes[:4])}")
        print()
        print("WHAT CHANGED:")
        print(ta.news.what_changed)
        print()
        print("SYNTHESIS:")
        print(ta.final_synthesis)
        print()
        print(signals_line)
        print(_RULE)


async def cmd_add_ticker(args: argparse.Namespace) -> None:
    db = DatabaseManager()
    await db.init_db()
    symbol = args.symbol.upper()
    success = await db.add_ticker(symbol)
    if success:
        print(f"Added {symbol} to watchlist")
    else:
        print(f"{symbol} is already in the watchlist")


async def cmd_remove_ticker(args: argparse.Namespace) -> None:
    db = DatabaseManager()
    await db.init_db()
    symbol = args.symbol.upper()
    await db.deactivate_ticker(symbol)
    print(f"Removed {symbol} from watchlist")


async def cmd_list_tickers(args: argparse.Namespace) -> None:
    db = DatabaseManager()
    await db.init_db()
    tickers = await db.get_active_tickers()
    if not tickers:
        print("No active tickers in watchlist")
        return

    print("Active tickers:")
    for ticker in tickers:
        recent = await db.get_recent_analyses(ticker, days=1)
        if recent:
            # analyzed_at is a naive-UTC ISO string; show date + minute (UTC).
            last = recent[0]["analyzed_at"].replace("T", " ")[:16]
        else:
            last = "never"
        print(f"  {ticker}  (last analyzed: {last})")


async def cmd_run_scheduler(args: argparse.Namespace) -> None:
    runner = PipelineRunner()
    await runner.initialize()

    # Run an immediate analysis for all tickers on startup.
    tickers = await runner.db.get_active_tickers()
    if tickers:
        print(
            f"Running initial analysis for {len(tickers)} tickers "
            f"before starting scheduler..."
        )
        await runner.analyze_all(tickers)
    else:
        print("No active tickers. Add some with: quantmind add-ticker AAPL")

    sched = DailyScheduler(runner)
    sched.start()

    print(f"Scheduler running. Daily refresh at {settings.refresh_time} {settings.timezone}")
    print("Press Ctrl+C to stop.")

    try:
        import time

        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        sched.stop()
        print("Scheduler stopped gracefully.")


# --- Parser ------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="quantmind",
        description="QuantMind v2 — Multi-agent quantitative news intelligence",
    )
    # Not required: running with NO subcommand launches the interactive menu.
    subparsers = parser.add_subparsers(
        dest="command", help="run with no command to launch the interactive menu"
    )

    analyze_parser = subparsers.add_parser("analyze", help="Analyze one or more tickers")
    analyze_parser.add_argument(
        "tickers", nargs="+", help="Ticker symbols e.g. AAPL MSFT GOOGL"
    )

    add_parser = subparsers.add_parser("add-ticker", help="Add a ticker to the watchlist")
    add_parser.add_argument("symbol", help="Ticker symbol e.g. NVDA")

    remove_parser = subparsers.add_parser(
        "remove-ticker", help="Remove a ticker from the watchlist"
    )
    remove_parser.add_argument("symbol", help="Ticker symbol e.g. NVDA")

    subparsers.add_parser("list-tickers", help="List active watchlist tickers")

    subparsers.add_parser(
        "run-scheduler",
        help="Run an initial analysis, then start the daily scheduler",
    )

    return parser


parser = build_parser()

HANDLER_MAP = {
    "analyze": cmd_analyze,
    "add-ticker": cmd_add_ticker,
    "remove-ticker": cmd_remove_ticker,
    "list-tickers": cmd_list_tickers,
    "run-scheduler": cmd_run_scheduler,
}


def main() -> None:
    """Console-script entry point (`quantmind`)."""
    args = parser.parse_args()
    if args.command is None:
        # No subcommand → launch the interactive TUI menu. Imported lazily so
        # plain commands and --help don't pay the prompt-toolkit import cost.
        from quantmind.tui import run_menu

        try:
            asyncio.run(run_menu())
        except Exception as exc:  # noqa: BLE001 — friendly hint for the no-console case
            # prompt_toolkit needs a real console; Git Bash/MinTTY/pipes raise
            # NoConsoleScreenBufferError. Re-raise anything unrelated.
            if "console" in f"{type(exc).__name__} {exc}".lower():
                print(
                    "The interactive menu needs a standard terminal "
                    "(PowerShell, cmd, or Windows Terminal) — it does not run inside "
                    "Git Bash/MinTTY or a pipe.\n"
                    "You can still use commands directly, e.g.  quantmind analyze AAPL"
                )
            else:
                raise
    else:
        asyncio.run(HANDLER_MAP[args.command](args))


if __name__ == "__main__":
    main()
