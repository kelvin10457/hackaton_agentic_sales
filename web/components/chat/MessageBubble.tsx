import { ShieldCheck } from "lucide-react";

import { CitationChip } from "@/components/shared/citation-chip";
import { LogoMark } from "@/components/shared/logo";
import { formatHora } from "@/lib/format";
import { cn } from "@/lib/utils";
import type { MensajeChat } from "@/lib/types";

export function MessageBubble({ mensaje }: { mensaje: MensajeChat }) {
  const esAgente = mensaje.rol === "agente";
  const esGuardrail = Boolean(mensaje.guardrail);

  return (
    <div
      className={cn(
        "flex w-full animate-fade-up gap-2.5 py-1.5",
        esAgente ? "justify-start" : "justify-end"
      )}
    >
      {esAgente && (
        <LogoMark className="mt-1 size-7 rounded-full text-[11px]" />
      )}
      <div
        className={cn(
          "flex max-w-[82%] flex-col gap-1 sm:max-w-[75%]",
          esAgente ? "items-start" : "items-end"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-3.5 py-2.5 text-sm leading-relaxed shadow-sm",
            esAgente
              ? esGuardrail
                ? "rounded-tl-md border border-amber-200 bg-amber-50 text-amber-950"
                : "rounded-tl-md border border-border bg-card text-foreground"
              : "rounded-br-md bg-futuro-corp text-white"
          )}
        >
          <span className="sr-only">{esAgente ? "Asistente:" : "Tú:"}</span>
          {/* Negativa honesta: decir "no sé" es una feature, y se etiqueta */}
          {esGuardrail && (
            <p className="mb-1 flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-amber-700">
              <ShieldCheck className="size-3" aria-hidden="true" />
              Negativa honesta — sin fuente, no hay afirmación
            </p>
          )}
          <p className="whitespace-pre-line">{mensaje.texto}</p>
          {mensaje.fuentes && mensaje.fuentes.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {mensaje.fuentes.map((f, i) => (
                <CitationChip key={i} cita={f.cita_visible} />
              ))}
            </div>
          )}
        </div>
        <span className="px-1 text-[10px] tabular-nums text-muted-foreground">
          {formatHora(mensaje.ts)}
        </span>
      </div>
    </div>
  );
}
