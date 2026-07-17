"use client";
import { useState } from "react";
import { ClipboardList } from "lucide-react";

import { cn } from "@/lib/utils";
import type { Quiz } from "@/lib/types";

/**
 * Quiz de perfil de riesgo (HU2). Las 3 preguntas vienen FIJAS del backend
 * y el perfil lo calcula una rúbrica determinista — la IA no improvisa
 * un instrumento diagnóstico (principio de diseño 5).
 */
export function QuizCard({
  quiz,
  onComplete,
}: {
  quiz: Quiz;
  onComplete: (respuestas: number[]) => void;
}) {
  const [idx, setIdx] = useState(0);
  const [respuestas, setRespuestas] = useState<number[]>([]);
  const [seleccion, setSeleccion] = useState<number | null>(null);

  const total = quiz.preguntas.length;
  const pregunta = quiz.preguntas[idx];

  function elegir(opcion: number) {
    if (seleccion !== null) return;
    setSeleccion(opcion);
    const nuevas = [...respuestas, opcion];
    // Pausa breve para que se vea la selección antes de avanzar
    window.setTimeout(() => {
      if (idx + 1 < total) {
        setRespuestas(nuevas);
        setIdx(idx + 1);
        setSeleccion(null);
      } else {
        onComplete(nuevas);
      }
    }, 260);
  }

  return (
    <div className="my-2 w-full animate-fade-up rounded-2xl border border-border bg-card p-3 shadow-sm sm:p-4">
      <div className="mb-2.5 flex items-center justify-between gap-2">
        <p className="flex items-center gap-1.5 text-xs font-bold uppercase tracking-wider text-futuro-corp">
          <ClipboardList className="size-3.5" aria-hidden="true" />
          Quiz de perfil de riesgo
        </p>
        <span className="text-[11px] font-medium tabular-nums text-muted-foreground">
          {idx + 1} de {total}
        </span>
      </div>

      <div
        className="mb-3 h-1 overflow-hidden rounded-full bg-muted"
        role="progressbar"
        aria-valuemin={0}
        aria-valuemax={total}
        aria-valuenow={idx}
        aria-label="Progreso del quiz"
      >
        <div
          className="h-full rounded-full bg-futuro-accent transition-all duration-300"
          style={{ width: `${(idx / total) * 100}%` }}
        />
      </div>

      <p className="mb-3 text-sm font-medium text-foreground">{pregunta.texto}</p>

      <div className="flex flex-col gap-2" key={pregunta.id}>
        {pregunta.opciones.map((opcion, i) => (
          <button
            key={opcion}
            type="button"
            onClick={() => elegir(i)}
            disabled={seleccion !== null}
            aria-pressed={seleccion === i}
            className={cn(
              "w-full rounded-lg border px-3 py-2.5 text-left text-sm leading-snug transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1",
              seleccion === i
                ? "border-futuro-accent bg-futuro-accent text-white shadow-sm"
                : "border-border bg-card text-foreground hover:border-futuro-accent/50 hover:bg-accent"
            )}
          >
            {opcion}
          </button>
        ))}
      </div>

      <p className="mt-3 text-[11px] leading-snug text-muted-foreground">
        Cuestionario fijo aprobado por cumplimiento — el perfil lo calcula una
        rúbrica determinista, no la IA.
      </p>
    </div>
  );
}
