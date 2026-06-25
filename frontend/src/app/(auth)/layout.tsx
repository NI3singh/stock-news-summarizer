export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen bg-qm-bg overflow-hidden">
      {/* Background glow effects — matches reference screenshots */}
      <div
        className="pointer-events-none absolute inset-0"
        style={{
          background: `
            radial-gradient(ellipse 70% 60% at 0% 100%, rgba(34,197,94,0.14) 0%, transparent 65%),
            radial-gradient(ellipse 60% 55% at 100% 0%, rgba(220,38,38,0.12) 0%, transparent 65%)
          `,
        }}
      />

      {/* Floating market change badges — top left, matches screenshot */}
      <div className="absolute top-4 left-4 flex gap-2 z-10">
        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">
          -2%
        </span>
        <span className="px-2 py-0.5 rounded text-xs font-semibold bg-red-500/20 text-red-400 border border-red-500/30">
          -1%
        </span>
      </div>

      {/* Content */}
      <div className="relative z-10">{children}</div>
    </div>
  );
}
