// TypeScript types for the StockStalker AI / StockStalker backend (FastAPI over the engine).
//
// Two groups:
//   1) LIVE API SHAPES — exactly what the REST endpoints return today. Use these in the UI.
//   2) ENGINE REFERENCE — the pydantic schema the agent pipeline produces internally.
//
// IMPORTANT caveats (verified against stockstalker/api/main.py + memory/database.py):
//   • GET /api/summary returns flat DB rows (`SummaryRow`), NOT a `TickerAnalysis`.

// ─────────────────────────── ENGINE REFERENCE SCHEMA ───────────────────────────
export interface Article {
  title: string;
  url: string;
  source: string;
  ticker: string;
  published_at: string | null;
  content: string;
  credibility_score?: number; // source weight 0..1
  sentiment_score?: number; // per-article VADER score -1..1
}

export interface TechnicalSignals {
  rsi: number | null;
  macd: number | null;
  macd_signal: number | null;
  bb_upper: number | null;
  bb_lower: number | null;
  volume_ratio: number | null;
  price_change_pct: number | null;
}

export interface MarketData {
  current_price: number | null;
  market_cap: number | null;
  pe_ratio: number | null;
  forward_pe: number | null;
  beta: number | null;
  fifty_two_week_high: number | null;
  fifty_two_week_low: number | null;
  short_ratio: number | null;
  dividend_yield: number | null;
  sector: string | null;
  industry: string | null;
  earnings_date: string | null;
}

export interface MemoryContext {
  similar_past_events: string[];
  historical_sentiment_trend: string;
  days_of_history: number;
}

export interface NewsAnalysis {
  selected_articles: Article[];
  sentiment_score: number;
  key_themes: string[];
  summary: string;
  what_changed: string;
}

export interface QuantAnalysis {
  signals: TechnicalSignals;
  interpretation: string;
  correlation_note: string;
}

export interface TickerAnalysis {
  ticker: string;
  analyzed_at: string;
  news: NewsAnalysis;
  quant: QuantAnalysis | null;
  memory: MemoryContext;
  final_synthesis: string;
}

// ──────────────────────────── LIVE API SHAPES ────────────────────────────
// One persisted analysis row (a row of the `analyses` table; JSON columns are
// decoded by get_recent_analyses). This is what /api/summary actually returns.
export interface SummaryRow {
  id: number;
  ticker: string;
  analyzed_at: string;
  news_summary: string | null;
  what_changed: string | null;
  quant_interpretation: string | null;
  final_synthesis: string | null;
  sentiment_score: number | null;
  articles_used: Article[];
  memory_context: MemoryContext | null;
  key_themes: string[] | null;
  technical_signals: TechnicalSignals | null;
  composite_sentiment: number | null; // credibility-weighted composite
  market_data: MarketData | null;
}

export interface SummaryResponse {
  success: boolean;
  symbol: string;
  latest_summary: SummaryRow | null;
  historical_summaries: SummaryRow[];
  articles: Article[];
}

export interface TickersResponse {
  success: boolean;
  tickers: string[];
}

export interface JobResponse {
  success: boolean;
  job_id: string;
  status: "pending" | "running" | "done" | "failed";
  symbol: string;
  result: SummaryRow | { error: string } | null;
}

export interface SystemStatus {
  tickers: number;
  vector_store_size: number;
  scheduler_time: string;
  db_path: string;
}

export interface AgentRun {
  id: number;
  ticker: string;
  agent_name: string;
  started_at: string;
  duration_seconds: number | null;
  success: number; // stored as 0/1 in SQLite
  error_message: string | null;
}

// --- Alerts (Phase B) ---
export type AlertConditionType =
  | "sentiment_below"
  | "sentiment_above"
  | "new_sec_filing"
  | "daily_summary";

export interface AlertRule {
  id: number | null;
  ticker: string | null; // null = any ticker
  condition_type: AlertConditionType;
  threshold: number | null;
  is_active: boolean;
  created_at: string;
  last_triggered_at: string | null;
  delivery_channel: string;
}

export interface AlertStatus {
  connected: boolean;
  chat_id: string | null;
  bot_username: string | null;
}

export interface AlertEvent {
  id: number;
  rule_id: number;
  ticker: string;
  triggered_at: string;
  message: string | null;
  delivered: number; // 0/1 in SQLite
}

// --- MCP (Phase C) ---
export interface McpTool {
  name: string;
  description: string;
}

export interface McpStatus {
  running: boolean;
  host: string;
  port: number;
  url: string;
  tools: McpTool[];
}
