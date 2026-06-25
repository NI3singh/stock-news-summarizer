import { cn } from "@/lib/utils";
import LogoMark from "@/components/icons/logo-mark";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Logo({ size = "md", className }: LogoProps) {
  const gap = { sm: "gap-2", md: "gap-2.5", lg: "gap-3" };
  const mark = { sm: "h-8 w-8", md: "h-10 w-10", lg: "h-12 w-12" };
  const name = { sm: "text-base", md: "text-xl", lg: "text-2xl" };

  return (
    <div className={cn("flex items-center", gap[size], className)}>
      <LogoMark className={cn("flex-shrink-0", mark[size])} />
      <div>
        <div className={cn("font-bold text-white leading-none", name[size])}>StockStalker</div>
        <div className="text-xs text-market-green-400 font-semibold tracking-wider mt-0.5 gradient-text">AI</div>
      </div>
    </div>
  );
}
