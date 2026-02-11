import React from 'react';
import { cn } from '../../lib/utils';

// BUTTON
export const Button = React.forwardRef<HTMLButtonElement, React.ButtonHTMLAttributes<HTMLButtonElement> & { variant?: 'primary' | 'destructive' | 'outline' | 'ghost' }>(
  ({ className, variant = 'primary', ...props }, ref) => {
    const variants = {
      primary: "bg-slate-900 text-white hover:bg-slate-800",
      destructive: "bg-red-500 text-white hover:bg-red-600",
      outline: "border border-slate-200 bg-white hover:bg-slate-100 text-slate-900",
      ghost: "hover:bg-slate-100 text-slate-700",
    };
    return (
      <button
        ref={ref}
        className={cn("inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors h-10 px-4 py-2 disabled:opacity-50 disabled:pointer-events-none", variants[variant], className)}
        {...props}
      />
    );
  }
);

// INPUT
export const Input = React.forwardRef<HTMLInputElement, React.InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => {
    return (
      <input
        ref={ref}
        className={cn("flex h-10 w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-slate-400 disabled:cursor-not-allowed disabled:opacity-50", className)}
        {...props}
      />
    );
  }
);

// BADGE
export const Badge = ({ children, className, variant = "default" }: { children: React.ReactNode, className?: string, variant?: string }) => {
    const variants: Record<string, string> = {
        default: "bg-slate-900 text-white",
        success: "bg-green-500 text-white",
        warning: "bg-yellow-500 text-white",
        destructive: "bg-red-500 text-white",
        outline: "text-slate-950 border border-slate-200",
    };
    return (
        <div className={cn("inline-flex items-center rounded-full border px-2.5 py-0.5 text-xs font-semibold transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2", variants[variant] || variants.default, className)}>
            {children}
        </div>
    )
}

// CARD
export const Card = ({ className, children }: { className?: string, children: React.ReactNode }) => (
  <div className={cn("rounded-lg border border-slate-200 bg-white text-slate-950 shadow-sm", className)}>
    {children}
  </div>
);
