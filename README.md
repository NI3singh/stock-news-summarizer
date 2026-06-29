<div align="center">

<img src="frontend/public/logo.svg" alt="StockStalker-AI Logo" width="120"/>

# StockStalker-AI

### Multi-Agent Quantitative News Intelligence

**AI-powered multi-agent stock intelligence platform for financial news analysis, quantitative market insights, and Retrieval-Augmented Generation (RAG).**

</div>


## Overview

StockStalker-AI transforms a simple watchlist into structured, explainable trading intelligence.

For every ticker, the platform concurrently collects financial news from multiple trusted sources, retrieves historical context using persistent vector memory, performs quantitative market analysis, and synthesizes everything through specialized AI agents into a comprehensive trading report.

Unlike traditional stock news summarizers, StockStalker-AI combines **Multi-Agent AI**, **Retrieval-Augmented Generation (RAG)**, **Quantitative Analysis**, and **Persistent Memory** to deliver contextual investment intelligence rather than generic summaries.



## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                                          │
│  Polygon API  ·  Finviz  ·  Yahoo Finance RSS  ·  Google News RSS    │
└───────────────────────────────┬──────────────────────────────────────┘
                                 │  (4 sources, concurrent)
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  ASYNC SCRAPER ORCHESTRATOR                                            │
│  BaseScraper (httpx + rate limiter) · REST APIs + RSS feeds          │
│  asyncio.gather + per-source timeout + URL/title dedup                 │
└───────────────────────────────┬──────────────────────────────────────┘
                                 │  list[Article]
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  AGENT LAYER  (custom BaseAgent framework)                            │
│                                                                        │
│        MemoryAgent ──► MemoryContext ──┐                              │
│                                         ├─► OrchestratorAgent ─► Synthesis
│        NewsAgent  ┐                     │       (fuses all 3)          │
│                   ├─(asyncio.gather)────┘                              │
│        QuantAgent ┘                                                    │
└───────────────────────────────┬──────────────────────────────────────┘
                                 │  TickerAnalysis (typed)
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  SUPPORT LAYER                                                         │
│  GeminiClient (retry/rate-limit) · provider-agnostic LLM factory      │
│  DatabaseManager (aiosqlite) · VectorStore (ChromaDB) · Settings · log │
└───────────────────────────────┬──────────────────────────────────────┘
                                 │  persist + index (closes RAG loop)
                                 ▼
┌──────────────────────────────────────────────────────────────────────┐
│  PIPELINE / CLI                                                        │
│  PipelineRunner (shared resources, semaphore) · DailyScheduler         │
│  CLI: interactive menu (rich + questionary)  +  scriptable commands —  │
│  analyze · add-ticker · remove-ticker · list-tickers · run-scheduler   │
└──────────────────────────────────────────────────────────────────────┘
```

## Tech Stack

| Component | Technology | Why This Choice |
|---|---|---|
| HTTP client | **httpx** | Async-native; replaces blocking `requests` so all four sources fetch concurrently. |
| News sources | **httpx + RSS** | Polygon & Finviz plus Yahoo Finance / Google News RSS feeds — all lightweight HTTP (no headless browser), each isolated with its own timeout. |
| AI validation | **Pydantic v2** | End-to-end typed pipeline — agents pass validated models, never raw dicts; bad LLM output fails loudly at the boundary. |
| Config | **pydantic-settings** | Validates secrets at startup (fail-fast with a clear message) instead of failing silently on the first API call. |
| Logging | **loguru** | Structured, colored, rotating file logs — replaces `print()` and ad-hoc logging config. |
| Vector memory | **ChromaDB** | Local persistent embeddings for RAG; no external server or API to run. |
| Async DB | **aiosqlite** | Non-blocking SQLite using only portable SQL (no SQLite-only functions) so it can migrate to PostgreSQL. |
| Agent framework | **Custom (`BaseAgent`)** | ~100 lines of explicit, inspectable agent internals (timing, logging, error capture) vs. the opaque magic of CrewAI/AutoGen. |
| LLM | **Gemini 2.5 Flash Lite** | Structured output (validated objects, no string parsing), strong quality, generous free tier; pluggable via a provider-agnostic factory (OpenAI/Anthropic/etc.). |
| Concurrency | **asyncio.gather** | 4 sources scraped concurrently (~3-4s) instead of sequentially; multiple tickers analyzed under a semaphore. |
| Interactive CLI | **rich + questionary** | Colored panels/tables/spinners plus an arrow-key menu, so the tool is pleasant to use interactively (`stockstalker`) as well as scriptably. |

## Design Decisions

**1. Custom agent framework over CrewAI / AutoGen.** Agent frameworks hide the control flow that matters most here — when each agent runs, what context it sees, how failures propagate. A ~100-line `BaseAgent` (an `execute()` wrapper that times the run, logs it to the DB, and converts any exception into a typed failure result that never crashes the pipeline) makes all of that explicit and debuggable. The orchestration ("memory first, then news + quant in parallel, then one synthesis call") is plain `asyncio`, not a DSL.

**2. ChromaDB vector memory, not just SQL history.** SQL can tell you *that* a ticker was analyzed before; it can't tell you *which past events resemble today's news*. The Memory Agent embeds prior articles in ChromaDB and retrieves the semantically closest ones, so the synthesis can say "this echoes the supply-chain concern from last week." SQL still stores the structured analyses (for the sentiment-trend and recency signals); the two are complementary.

**3. All scrapers concurrent with `asyncio.gather`.** The four sources are independent I/O-bound calls, so running them sequentially just adds their latencies. `gather` overlaps them, and each is wrapped in an isolated task with its own timeout — one slow or blocked source (e.g. a 403'd Finviz request) can't abort the others or blow the latency budget.

**4. Pydantic for everything.** Every boundary — a scraped `Article`, an agent's `AgentResult`, the final `TickerAnalysis` — is a validated Pydantic model. This means an agent literally cannot pass a malformed object downstream, the LLM's structured output is validated on arrival, and the whole pipeline is autocomplete-friendly and self-documenting. Typing the pipeline end-to-end turns a class of silent runtime bugs into loud, located errors.

**5. `generate_structured()` instead of prompt-parsing hacks.** Rather than asking the model for JSON and then regex-stripping markdown fences and `json.loads`-ing the result (brittle, and a frequent source of production failures), the LLM client uses structured output (`with_structured_output(schema)` over the provider factory, backed by Gemini's response-schema support). The model returns a *validated Pydantic instance directly* — there is no string parsing anywhere in the pipeline.

## Quick Start

```bash
# 1. Clone
git clone <repo-url> && cd stock-news-summarizer

# 2. Install (editable, with dev/test extras) into a Python 3.11+ venv
pip install -e ".[dev]"

# 3. Configure secrets
cp .env.example .env            # then fill in GEMINI_API_KEY and POLYGON_API_KEY

# 4. Launch the interactive menu...
stockstalker

#    ...or run a one-off command directly
stockstalker analyze AAPL
```

## CLI Reference

After `pip install -e .`, the `stockstalker` command is available. Run it **with no arguments to launch the interactive menu**, or pass a subcommand to run it directly (ideal for scripts and cron):

```bash
stockstalker                       # interactive arrow-key menu
stockstalker <command> [args]      # one-off command (= python stockstalker/main.py <command> [args])
```

### Interactive menu

Running `stockstalker` with no arguments opens an arrow-key menu (built with **rich** + **questionary**). Pick an action, answer the prompt, and results render in colored panels — then it loops back to the menu.

```
 StockStalker v2 · Multi-agent quantitative news intelligence

 ? What would you like to do?  (use the up/down arrows, then Enter)
 > Analyze ticker(s)
   Add ticker to watchlist
   List watchlist
   Remove ticker
   Run daily scheduler
   Exit
```

> **Note:** the interactive menu needs a real terminal — **PowerShell, cmd, or Windows Terminal**. It does not run inside Git Bash/MinTTY or through a pipe (a `prompt_toolkit` limitation); use the direct commands below in those environments.

### Commands

**`analyze TICKERS...`** — run the full pipeline for one or more tickers.
```
$ stockstalker analyze AAPL
────────────────────────────────────────────────────────────
TICKER: AAPL  |  2026-06-23 06:01
Sentiment: +0.30  |  Days of History: 1
Themes: Intel-Apple Chip Collaboration, Rising Memory Chip Costs, AI Strategy, ...

WHAT CHANGED:
The primary new development is the reported agreement between Apple and Intel ...

SYNTHESIS:
Apple's stock is currently influenced by a confluence of strategic advancements
and immediate cost pressures ... a bearish MACD crossover ... For a trader
monitoring AAPL, the key takeaway is to watch for confirmation of the Intel
partnership ...

SIGNALS: RSI=49.25  MACD=1.20  Vol Ratio=0.85
────────────────────────────────────────────────────────────
```

**`add-ticker SYMBOL`** — add a ticker to the watchlist.
```
$ stockstalker add-ticker NVDA
Added NVDA to watchlist
```

**`remove-ticker SYMBOL`** — remove (soft-delete) a ticker from the watchlist.
```
$ stockstalker remove-ticker NVDA
Removed NVDA from watchlist
```

**`list-tickers`** — show active tickers and when each was last analyzed.
```
$ stockstalker list-tickers
Active tickers:
  AAPL  (last analyzed: 2026-06-23 06:08)
```

**`run-scheduler`** — analyze the whole watchlist now, then start the daily cron refresh.
```
$ stockstalker run-scheduler
Running initial analysis for 3 tickers before starting scheduler...
Scheduler running. Daily refresh at 08:00 Asia/Kolkata
Press Ctrl+C to stop.
```

**`api`** — start the FastAPI server (port 8000) that powers the web frontend.
```
$ stockstalker api
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**`mcp-server`** — start the MCP server so MCP clients (e.g. Claude Desktop) can call StockStalker as tools.
```
$ stockstalker mcp-server
Starting StockStalker MCP server...
Connect Claude Desktop at: http://127.0.0.1:8765/mcp
```

## Web UI & Integrations

Beyond the CLI, StockStalker ships with:

- **Web frontend** (`frontend/`) — a Next.js + Tailwind dashboard (watchlist, per-ticker analysis, history, alerts, MCP status). Start the backend with `stockstalker api`, then `cd frontend && npm install && npm run dev` (→ http://localhost:3000).
- **Telegram alerts** — rule-based notifications (sentiment thresholds, daily summaries) delivered to Telegram; configured from the dashboard or via `TELEGRAM_BOT_TOKEN` in `.env`.
- **MCP server** (`stockstalker mcp-server`) — exposes the engine to MCP clients (Claude Desktop, IDEs) as five tools: `get_stock_analysis`, `run_stock_analysis`, `get_watchlist`, `compare_tickers`, `get_system_status`.

## Performance

Measured on live runs (free-tier Gemini, single developer machine):

| Operation | Time | Notes |
|---|---|---|
| Scraping (4 sources, concurrent) | **~3-4s** / ticker | Polygon + Finviz + Yahoo & Google News RSS (~90 articles for AAPL); all HTTP, no headless browser. |
| Full single-ticker analysis | **~32s** | Scrape → memory → news + quant → synthesis → persist. |
| 3-ticker concurrent batch | **~58s** | vs. ~96s if run sequentially → **~40% faster**. Not 3× because the shared LLM rate limiter (0.9 calls/s) serializes the model calls; the scrapes overlap fully. |

Cross-run memory is verified end-to-end: a second analysis of the same ticker reports `Days of History: 1` and retrieves the prior run's indexed articles, confirming the RAG loop.

## vs. StockStalker v1

- **Async vs. synchronous** — `asyncio` throughout (httpx, aiosqlite, concurrent scrape + multi-ticker batch) instead of blocking, one-thing-at-a-time `requests`.
- **4 sources vs. 3** — Polygon, Finviz, Yahoo Finance RSS, and Google News RSS, each isolated and individually timed (all lightweight HTTP — no headless browser).
- **Vector memory vs. SQL-only** — ChromaDB RAG so each run is informed by semantically similar past events, not just a flat history table.
- **Typed pipeline vs. dict passing** — validated Pydantic models at every boundary instead of free-form dictionaries.
- **Multi-agent vs. monolithic** — specialized Memory/News/Quant agents coordinated by an orchestrator, replacing one big summarize-everything function.
- **Interactive menu + scriptable CLI** — an arrow-key TUI (rich + questionary) for exploration *and* one-off commands for scripts/cron, vs. a single web view.
- **Resilient LLM client vs. one-shot** — rate-limited, 3-retry-with-backoff structured-output client, plus a provider-agnostic factory (swap Gemini for OpenAI/Anthropic via config) instead of a single direct call.
