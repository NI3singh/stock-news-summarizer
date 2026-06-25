export function OrDivider({ text = "or continue with email" }: { text?: string }) {
  return (
    <div className="flex items-center gap-3 my-5">
      <div className="flex-1 h-px bg-qm-border" />
      <span className="text-xs text-qm-text3 whitespace-nowrap">{text}</span>
      <div className="flex-1 h-px bg-qm-border" />
    </div>
  );
}
