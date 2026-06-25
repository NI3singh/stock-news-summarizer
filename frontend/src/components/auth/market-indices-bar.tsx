interface IndexData { name: string; change: string; positive: boolean; }

const INDICES: IndexData[] = [
  { name: "S&P 500", change: "+1.24%", positive: true },
  { name: "NASDAQ",  change: "+0.87%", positive: true },
  { name: "DOW",     change: "-0.32%", positive: false },
];

export function MarketIndicesBar() {
  return (
    <div className="flex gap-3 mt-4">
      {INDICES.map(idx => (
        <div
          key={idx.name}
          className="flex-1 rounded-lg border border-qm-border bg-qm-bg/60 px-3 py-2 text-center"
        >
          <div className="text-[10px] text-qm-text3 uppercase tracking-wider">{idx.name}</div>
          <div className={`text-sm font-semibold mt-0.5 ${idx.positive ? "text-qm-green" : "text-red-400"}`}>
            {idx.change}
          </div>
        </div>
      ))}
    </div>
  );
}
