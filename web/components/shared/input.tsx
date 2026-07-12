import * as React from "react"
import { Input as InputPrimitive } from "@base-ui/react/input"

import { cn } from "@/lib/utils"

function Input({ className, type, ...props }: React.ComponentProps<"input">) {
  return (
    <InputPrimitive
      type={type}
      data-slot="input"
      className={cn(
        "h-9 w-full min-w-0 rounded-lg border border-input bg-card px-3 py-1 text-sm text-foreground transition-colors duration-150 outline-none placeholder:text-muted-foreground focus-visible:border-futuro-accent focus-visible:ring-2 focus-visible:ring-ring/30 disabled:pointer-events-none disabled:cursor-not-allowed disabled:bg-muted disabled:opacity-60",
        className
      )}
      {...props}
    />
  )
}

export { Input }
