/**
 * Componente Button reutilizable
 */

import React from "react";

type ButtonVariant = "default" | "outline" | "ghost";
type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  children: React.ReactNode;
}

const buttonVariants = {
  default:
    "bg-blue-600 hover:bg-blue-700 text-white border border-blue-600 hover:border-blue-700",
  outline:
    "border border-slate-600 hover:border-slate-500 text-slate-100 hover:bg-slate-800",
  ghost:
    "text-slate-300 hover:text-white hover:bg-slate-800 border-0",
};

const buttonSizes = {
  sm: "px-3 py-2 text-sm",
  md: "px-4 py-2 text-base",
  lg: "px-6 py-3 text-lg",
};

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant = "default", size = "md", ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={`
          inline-flex items-center justify-center rounded-lg font-semibold
          transition-colors duration-200 disabled:opacity-50 disabled:cursor-not-allowed
          ${buttonVariants[variant]} ${buttonSizes[size]} ${className}
        `}
        {...props}
      />
    );
  }
);

Button.displayName = "Button";
