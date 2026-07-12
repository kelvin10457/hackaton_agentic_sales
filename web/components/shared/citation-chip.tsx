import { BookOpen } from "lucide-react"

import { cn } from "@/lib/utils"

/**
 * Chip de cita del corpus aprobado.
 * MISMO componente en el chat (fuentes del tutor) y en la consola
 * (fuentes_consultadas de la acción propuesta) — regla de consistencia #5.
 * Debe ser legible en el vídeo: es la prueba visual del criterio antialucinación.
 */
export function CitationChip({
  cita,
  className,
}: {
  cita: string
  className?: string
}) {
  return (
    <span
      className={cn(
        "inline-flex max-w-full items-center gap-1.5 rounded-md border border-futuro-accent/25 bg-futuro-accent/5 px-2 py-1 text-[11px] font-medium leading-tight text-futuro-corp",
        className
      )}
    >
      <BookOpen className="size-3 shrink-0 text-futuro-accent" aria-hidden="true" />
      <span className="truncate" title={cita}>
        {cita}
      </span>
    </span>
  )
}
