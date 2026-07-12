import { cn } from "@/lib/utils"

/**
 * Isotipo de marca: cuadrado con el degradado oficial del logo
 * (celeste #4BA3E3 → azul oscuro #031B4E). Es el ÚNICO degradado
 * permitido en la UI — pertenece a la marca, no a la decoración.
 */
export function LogoMark({
  className,
  claro = false,
}: {
  className?: string
  /** true cuando el fondo es oscuro (borde sutil para separarlo) */
  claro?: boolean
}) {
  return (
    <span
      aria-hidden="true"
      className={cn(
        "flex size-8 shrink-0 select-none items-center justify-center rounded-lg bg-gradient-to-b from-futuro-sky to-futuro-base text-sm font-bold text-white shadow-sm",
        claro && "ring-1 ring-white/25",
        className
      )}
    >
      F
    </span>
  )
}

/** Wordmark tipográfico: FUTURO Academy */
export function LogoWordmark({
  className,
  invertido = false,
}: {
  className?: string
  /** true sobre fondos oscuros */
  invertido?: boolean
}) {
  return (
    <span className={cn("flex items-baseline gap-1.5 leading-none", className)}>
      <span
        className={cn(
          "text-base font-extrabold tracking-tight",
          invertido ? "text-white" : "text-futuro-base"
        )}
      >
        FUTURO
      </span>
      <span
        className={cn(
          "text-[11px] font-semibold uppercase tracking-[0.18em]",
          invertido ? "text-futuro-sky" : "text-futuro-corp/70"
        )}
      >
        Academy
      </span>
    </span>
  )
}
