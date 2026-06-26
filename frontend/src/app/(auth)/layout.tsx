import { AnimatedAuthBg } from "@/components/auth/animated-bg";

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="relative min-h-screen stock-grid-bg overflow-hidden">
      <AnimatedAuthBg />
      <div className="relative z-10">{children}</div>
    </div>
  );
}
