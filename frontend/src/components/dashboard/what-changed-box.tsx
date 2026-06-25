export function WhatChangedBox({ text }: { text: string }) {
  return (
    <div className="rounded-lg border-l-4 border-qm-amber bg-qm-amber-bg p-4">
      <div className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-qm-amber">
        <span aria-hidden>⚡</span> What Changed Today
      </div>
      <p className="text-sm leading-relaxed text-qm-text2">{text}</p>
    </div>
  );
}
