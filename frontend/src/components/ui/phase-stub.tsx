import Link from "next/link";

export function PhaseStub({
  phase,
  title,
  description,
  color,
}: {
  phase: string;
  title: string;
  description: string;
  color: string;
}) {
  return (
    <div className="flex h-full flex-col items-center justify-center p-8 text-center">
      <span
        className="rounded-full px-3 py-1 text-xs font-bold text-white"
        style={{ backgroundColor: color }}
      >
        {phase}
      </span>
      <h1 className="mt-4 text-2xl font-bold text-qm-text">{title}</h1>
      <p className="mt-2 max-w-md text-sm text-qm-text2">{description}</p>
      <Link href="/dashboard" className="mt-6 text-sm text-qm-green hover:underline">
        ← Back to Dashboard
      </Link>
    </div>
  );
}
