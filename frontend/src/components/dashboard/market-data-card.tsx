import type { MarketData } from "@/lib/types";

function fmtCap(n: number | null): string {
  if (n == null) return "—";
  if (n >= 1e12) return `$${(n / 1e12).toFixed(2)}T`;
  if (n >= 1e9) return `$${(n / 1e9).toFixed(2)}B`;
  if (n >= 1e6) return `$${(n / 1e6).toFixed(2)}M`;
  return `$${n.toLocaleString()}`;
}

function fmtNum(n: number | null, digits = 2): string {
  return n == null ? "—" : n.toFixed(digits);
}

function fmtPrice(n: number | null): string {
  return n == null ? "—" : `$${n.toFixed(2)}`;
}

export function MarketDataCard({ data }: { data: MarketData | null | undefined }) {
  if (!data) return null;
  // Hide the card entirely if nothing meaningful came back.
  const hasAny = [
    data.market_cap,
    data.pe_ratio,
    data.current_price,
    data.earnings_date,
    data.sector,
  ].some((v) => v != null);
  if (!hasAny) return null;

  const items: [string, string][] = [
    ["Price", fmtPrice(data.current_price)],
    ["Market Cap", fmtCap(data.market_cap)],
    ["P/E (TTM)", fmtNum(data.pe_ratio, 1)],
    ["Fwd P/E", fmtNum(data.forward_pe, 1)],
    ["Beta", fmtNum(data.beta, 2)],
    ["52W High", fmtPrice(data.fifty_two_week_high)],
    ["52W Low", fmtPrice(data.fifty_two_week_low)],
    ["Short Ratio", fmtNum(data.short_ratio, 2)],
    ["Earnings", data.earnings_date ? data.earnings_date.slice(0, 10) : "—"],
  ];

  const subtitle = [data.sector, data.industry].filter(Boolean).join(" · ");

  return (
    <section className="qm-elevate rounded-xl border border-qm-border bg-qm-card p-5">
      <h2 className="mb-1 text-sm font-semibold text-qm-text">🏦 Market Data</h2>
      {subtitle && <p className="mb-3 text-xs text-qm-text3">{subtitle}</p>}
      <div className="grid grid-cols-2 gap-x-4 gap-y-3 sm:grid-cols-3">
        {items.map(([label, value]) => (
          <div key={label} className="flex flex-col">
            <span className="text-[10px] uppercase tracking-wider text-qm-text3">{label}</span>
            <span className="text-sm font-medium tabular-nums text-qm-text">{value}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
