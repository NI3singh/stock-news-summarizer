import { cn } from "@/lib/utils";

interface LogoProps {
  size?: "sm" | "md" | "lg";
  className?: string;
}

export function Logo({ size = "md", className }: LogoProps) {
  const sizes = { sm: "gap-2", md: "gap-3", lg: "gap-3" };
  const iconSizes = { sm: "h-8 w-8 text-lg", md: "h-10 w-10 text-xl", lg: "h-12 w-12 text-2xl" };
  const nameSizes = { sm: "text-base", md: "text-xl", lg: "text-2xl" };

  return (
    <div className={cn("flex items-center", sizes[size], className)}>
      <div className={cn(
        "flex items-center justify-center rounded-xl bg-qm-green text-white font-bold flex-shrink-0",
        iconSizes[size]
      )}>
        ◎
      </div>
      <div>
        <div className={cn("font-bold text-qm-text leading-none", nameSizes[size])}>
          StockStalker
        </div>
        <div className="text-xs text-qm-green font-semibold tracking-wider mt-0.5">AI</div>
      </div>
    </div>
  );
}
