"use client";
import { GraduationCap } from "lucide-react";

/**
 * Estado vacío del chat: bienvenida + accesos rápidos.
 * Identificación progresiva (nunca un formulario de registro al entrar).
 */
export function Bienvenida({
  onSelect,
  deshabilitado,
}: {
  onSelect: (texto: string) => void;
  deshabilitado?: boolean;
}) {
  const sugerencias = [
    "¿Qué es un ETF?",
    "Quiero empezar a invertir",
    "Hacer el quiz de perfil de riesgo",
  ];

  return (
    <div className="flex animate-fade-up flex-col items-center gap-4 px-4 py-8 text-center">
      <span
        className="flex size-14 items-center justify-center rounded-2xl bg-gradient-to-b from-futuro-sky to-futuro-base shadow-md"
        aria-hidden="true"
      >
        <GraduationCap className="size-7 text-white" />
      </span>
      <div>
        <h2 className="text-base font-semibold text-futuro-base">
          Hola, soy el asistente de Futuro Academy
        </h2>
        <p className="mx-auto mt-1 max-w-sm text-sm leading-relaxed text-muted-foreground">
          Aprende finanzas con contenido verificado y descubre tu perfil de
          inversionista. Sin registros, a tu ritmo.
        </p>
      </div>
      <div className="flex flex-wrap justify-center gap-2">
        {sugerencias.map((s) => (
          <button
            key={s}
            type="button"
            onClick={() => onSelect(s)}
            disabled={deshabilitado}
            className="rounded-full border border-border bg-card px-3.5 py-1.5 text-[13px] font-medium text-futuro-corp shadow-sm transition-all duration-150 hover:border-futuro-accent hover:bg-accent focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 active:translate-y-px disabled:pointer-events-none disabled:opacity-50"
          >
            {s}
          </button>
        ))}
      </div>
    </div>
  );
}
