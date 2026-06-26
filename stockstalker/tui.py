"""StockStalker v2 — interactive menu (TUI) built on rich + questionary.

Launched by running ``stockstalker`` (or ``python stockstalker/main.py``) with NO
subcommand. This is a thin presentation layer over the SAME PipelineRunner /
DatabaseManager the argparse CLI uses — no analysis logic is duplicated here.
A single PipelineRunner is created once and reused for the whole session.
"""
import sys

import questionary
from questionary import Choice
from questionary import Style as QStyle
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from stockstalker.config import settings
from stockstalker.memory import DatabaseManager
from stockstalker.pipeline import DailyScheduler, PipelineRunner

console = Console()

# Make the colored output survive a non-UTF-8 console (Windows cp1252 pipe).
try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):  # pragma: no cover
    pass

_BANNER = r"""
 ___ _           _    ___ _        _ _
/ __| |_ ___  __| |__/ __| |_ __ _| | |_____ _ _
\__ \  _/ _ \/ _| / /\__ \  _/ _` | | / / -_) '_|
|___/\__\___/\__|_\_\|___/\__\__,_|_|_\_\___|_|
"""

# questionary colour theme for the arrow-key menu
_QSTYLE = QStyle(
    [
        ("qmark", "fg:#00afff bold"),
        ("question", "bold"),
        ("pointer", "fg:#00afff bold"),
        ("highlighted", "fg:#00afff bold"),
        ("selected", "fg:#00ff5f bold"),
        ("answer", "fg:#00afff bold"),
    ]
)

# menu action keys
_ANALYZE, _ADD, _LIST, _REMOVE, _SCHED, _EXIT = (
    "analyze",
    "add",
    "list",
    "remove",
    "scheduler",
    "exit",
)


def _print_banner() -> None:
    console.print(Text(_BANNER, style="bold cyan"))
    console.print(
        "  [dim]v2 · Multi-agent quantitative news intelligence[/dim]\n"
    )


def _render_analysis(ta) -> None:
    """Render one TickerAnalysis as a colored rich panel."""
    sent = ta.news.sentiment_score
    color = "green" if sent > 0.1 else "red" if sent < -0.1 else "yellow"

    if ta.quant is not None:
        s = ta.quant.signals
        signals = (
            f"RSI={s.rsi if s.rsi is not None else 'N/A'}   "
            f"MACD={s.macd if s.macd is not None else 'N/A'}   "
            f"Vol Ratio={s.volume_ratio if s.volume_ratio is not None else 'N/A'}"
        )
    else:
        signals = "N/A (quant analysis unavailable)"

    body = (
        f"[bold]Sentiment:[/bold] [{color}]{sent:+.2f}[/{color}]    "
        f"[bold]Days of History:[/bold] {ta.memory.days_of_history}\n"
        f"[bold]Themes:[/bold] {', '.join(ta.news.key_themes[:4])}\n\n"
        f"[bold underline]What changed[/bold underline]\n{ta.news.what_changed}\n\n"
        f"[bold underline]Synthesis[/bold underline]\n{ta.final_synthesis}\n\n"
        f"[bold]Signals:[/bold] {signals}"
    )
    console.print(
        Panel(
            body,
            title=f"[bold]{ta.ticker}[/bold]  ·  {ta.analyzed_at.strftime('%Y-%m-%d %H:%M')}",
            border_style=color,
            padding=(1, 2),
        )
    )


async def _do_analyze(runner: PipelineRunner) -> None:
    raw = await questionary.text(
        "Enter ticker(s), space-separated (e.g. AAPL MSFT):", style=_QSTYLE
    ).ask_async()
    if not raw or not raw.strip():
        return
    tickers = [t.upper() for t in raw.split()]
    with console.status(
        f"[cyan]Analyzing {', '.join(tickers)} … (scrape → agents → synthesis)[/cyan]",
        spinner="dots",
    ):
        results = await runner.analyze_all(tickers)
    if not results:
        console.print("[red]No analyses produced (all tickers failed — see logs).[/red]")
        return
    for ta in results:
        _render_analysis(ta)


async def _do_add(db: DatabaseManager) -> None:
    sym = await questionary.text(
        "Ticker symbol to add (e.g. NVDA):", style=_QSTYLE
    ).ask_async()
    if not sym or not sym.strip():
        return
    sym = sym.strip().upper()
    if await db.add_ticker(sym):
        console.print(f"[green]✔ Added {sym} to watchlist[/green]")
    else:
        console.print(f"[yellow]{sym} is already in the watchlist[/yellow]")


async def _do_list(db: DatabaseManager) -> None:
    tickers = await db.get_active_tickers()
    if not tickers:
        console.print("[yellow]No active tickers in watchlist.[/yellow]")
        return
    table = Table(title="Watchlist", border_style="cyan", title_style="bold")
    table.add_column("Ticker", style="bold")
    table.add_column("Last analyzed (UTC)")
    for t in tickers:
        recent = await db.get_recent_analyses(t, days=1)
        last = recent[0]["analyzed_at"].replace("T", " ")[:16] if recent else "never"
        table.add_row(t, last)
    console.print(table)


async def _do_remove(db: DatabaseManager) -> None:
    tickers = await db.get_active_tickers()
    if not tickers:
        console.print("[yellow]No active tickers to remove.[/yellow]")
        return
    sym = await questionary.select(
        "Select a ticker to remove:",
        choices=[*tickers, Choice("(cancel)", "__cancel__")],
        style=_QSTYLE,
    ).ask_async()
    if not sym or sym == "__cancel__":
        return
    await db.deactivate_ticker(sym)
    console.print(f"[green]✔ Removed {sym} from watchlist[/green]")


async def _do_scheduler(runner: PipelineRunner) -> None:
    tickers = await runner.db.get_active_tickers()
    if tickers:
        with console.status(
            f"[cyan]Initial analysis for {len(tickers)} ticker(s) …[/cyan]",
            spinner="dots",
        ):
            await runner.analyze_all(tickers)
        console.print(f"[green]✔ Initial analysis complete ({len(tickers)} ticker(s)).[/green]")
    else:
        console.print("[yellow]No active tickers — add some first.[/yellow]")
        return

    sched = DailyScheduler(runner)
    sched.start()
    console.print(
        f"[green]Scheduler running.[/green] Daily refresh at "
        f"[bold]{settings.refresh_time} {settings.timezone}[/bold].  "
        f"Press [bold]Ctrl+C[/bold] to return to the menu."
    )
    try:
        import time

        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        sched.stop()
        console.print("\n[yellow]Scheduler stopped — returning to menu.[/yellow]")


async def run_menu() -> None:
    """Run the interactive menu loop until the user exits."""
    _print_banner()
    runner = PipelineRunner()
    await runner.initialize()

    choices = [
        Choice("Analyze ticker(s)", _ANALYZE),
        Choice("Add ticker to watchlist", _ADD),
        Choice("List watchlist", _LIST),
        Choice("Remove ticker", _REMOVE),
        Choice("Run daily scheduler", _SCHED),
        Choice("Exit", _EXIT),
    ]

    while True:
        action = await questionary.select(
            "What would you like to do?", choices=choices, style=_QSTYLE
        ).ask_async()

        if action is None or action == _EXIT:  # None = user pressed Ctrl+C / Esc
            console.print("[dim]Goodbye.[/dim]")
            break
        if action == _ANALYZE:
            await _do_analyze(runner)
        elif action == _ADD:
            await _do_add(runner.db)
        elif action == _LIST:
            await _do_list(runner.db)
        elif action == _REMOVE:
            await _do_remove(runner.db)
        elif action == _SCHED:
            await _do_scheduler(runner)

        console.print()  # spacer before the menu redraws
