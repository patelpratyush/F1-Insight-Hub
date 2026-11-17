import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import * as React from "react";
import { cn } from "../lib/cn";

const button = cva(
  "inline-flex items-center justify-center gap-2 rounded-md font-medium transition-transform duration-150 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-team disabled:pointer-events-none disabled:opacity-50 active:scale-[0.97]",
  {
    variants: {
      variant: {
        primary: "bg-team text-white hover:brightness-110",
        secondary: "bg-carbon-800 text-carbon-50 hover:bg-carbon-700",
        ghost: "text-carbon-200 hover:bg-carbon-800",
      },
      size: { sm: "h-8 px-3 text-sm", md: "h-10 px-4 text-sm" },
    },
    defaultVariants: { variant: "primary", size: "md" },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof button> {
  asChild?: boolean;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild, ...props }, ref) => {
    const Comp = asChild ? Slot : "button";
    return <Comp ref={ref} className={cn(button({ variant, size }), className)} {...props} />;
  },
);
Button.displayName = "Button";
