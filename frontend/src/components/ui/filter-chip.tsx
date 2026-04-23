import * as React from "react";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";

const filterChipVariants = cva(
  "inline-flex items-center justify-center rounded-full border font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:pointer-events-none disabled:opacity-50",
  {
    variants: {
      selected: {
        true: "border-primary bg-primary text-primary-foreground",
        false:
          "border-border text-muted-foreground hover:border-foreground hover:bg-accent hover:text-foreground",
      },
      size: {
        sm: "h-8 px-3 text-xs",
        md: "h-9 px-3.5 text-sm",
      },
    },
    defaultVariants: {
      selected: false,
      size: "sm",
    },
  },
);

type FilterChipProps = React.ButtonHTMLAttributes<HTMLButtonElement> &
  Omit<VariantProps<typeof filterChipVariants>, "selected"> & {
    selected?: boolean;
  };

export function FilterChip({ className, selected = false, size, ...props }: FilterChipProps) {
  return (
    <button
      type="button"
      aria-pressed={selected}
      className={cn(filterChipVariants({ selected, size }), className)}
      {...props}
    />
  );
}
