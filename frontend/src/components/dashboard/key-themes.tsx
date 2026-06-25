export function KeyThemes({ themes }: { themes: string[] }) {
  if (!themes?.length) return null;
  const shown = themes.slice(0, 6);
  const extra = themes.length - shown.length;

  return (
    <div className="flex flex-wrap gap-2">
      {shown.map((t) => (
        <span
          key={t}
          className="rounded-full border border-qm-border bg-qm-card px-3 py-1 text-xs text-qm-text2"
        >
          {t}
        </span>
      ))}
      {extra > 0 && (
        <span className="rounded-full border border-qm-border bg-qm-card px-3 py-1 text-xs text-qm-text3">
          +{extra} more
        </span>
      )}
    </div>
  );
}
