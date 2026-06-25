"use client";
import { cn } from "@/lib/utils";
import { InputHTMLAttributes, forwardRef, ReactNode, useState } from "react";
import { Eye, EyeOff } from "lucide-react";

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: ReactNode;
  rightIcon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ className, label, error, leftIcon, rightIcon, type, ...props }, ref) => {
    const [showPassword, setShowPassword] = useState(false);
    const isPassword = type === "password";
    const inputType = isPassword ? (showPassword ? "text" : "password") : type;

    return (
      <div className="space-y-1.5">
        {label && (
          <label className="block text-sm font-medium text-qm-text2">{label}</label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-qm-text3">{leftIcon}</div>
          )}
          <input
            ref={ref}
            type={inputType}
            className={cn(
              "w-full rounded-lg border border-qm-border bg-qm-card text-qm-text placeholder:text-qm-text3",
              "py-2.5 text-sm transition-all duration-200",
              "focus:outline-none focus:border-qm-green focus:ring-1 focus:ring-qm-green focus:bg-qm-card2",
              leftIcon ? "pl-10" : "pl-3.5",
              (rightIcon || isPassword) ? "pr-10" : "pr-3.5",
              error && "border-red-500 focus:border-red-500 focus:ring-red-500",
              className
            )}
            {...props}
          />
          {isPassword && (
            <button
              type="button"
              onClick={() => setShowPassword(!showPassword)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-qm-text3 hover:text-qm-text2 transition-colors"
            >
              {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </button>
          )}
          {rightIcon && !isPassword && (
            <div className="absolute right-3 top-1/2 -translate-y-1/2 text-qm-text3">{rightIcon}</div>
          )}
        </div>
        {error && <p className="text-xs text-red-400">{error}</p>}
      </div>
    );
  }
);
Input.displayName = "Input";
