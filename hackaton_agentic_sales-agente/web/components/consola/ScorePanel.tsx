'use client';

import React, { useEffect, useState } from 'react';
import { Info } from 'lucide-react';

import { etiqueta } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Banda, ScoreLead } from '@/lib/types';

const BADGE_BANDA: Record<Banda, string> = {
  caliente: 'border-red-200 bg-red-50 text-red-700',
  tibio: 'border-amber-200 bg-amber-50 text-amber-700',
  frio: 'border-blue-200 bg-blue-50 text-blue-700',
};

const DOT_BANDA: Record<Banda, string> = {
  caliente: 'bg-banda-caliente',
  tibio: 'bg-banda-tibio',
  frio: 'bg-banda-frio',
};

const BORDE_BANDA: Record<Banda, string> = {
  caliente: 'border-l-banda-caliente',
  tibio: 'border-l-banda-tibio',
  frio: 'border-l-banda-frio',
};

function ScoreBar({
  label,
  value,
  max,
  animar,
}: {
  label: string;
  value: number;
  max: number;
  animar: boolean;
}) {
  const pct = Math.max(0, Math.min(100, ((value ?? 0) / max) * 100));
  return (
    <div>
      <div className="mb-1 flex items-baseline justify-between">
        <span className="text-[13px] font-medium text-foreground">{label}</span>
        <span className="text-xs font-semibold tabular-nums text-muted-foreground">
          {value ?? 0}/{max}
        </span>
      </div>
      <div
        className="h-2 w-full overflow-hidden rounded-full bg-muted"
        role="img"
        aria-label={`${label}: ${value ?? 0} de ${max}`}
      >
        <div
          className="h-full rounded-full bg-futuro-accent transition-[width] duration-500 ease-out"
          style={{ width: animar ? `${pct}%` : '0%' }}
        />
      </div>
    </div>
  );
}

export default function ScorePanel({ score }: { score: ScoreLead }) {
  const banda: Banda = score?.banda ?? 'frio';
  const [animar, setAnimar] = useState(false);

  // Las barras crecen desde 0 al montar o al cambiar de lead (≈500 ms)
  useEffect(() => {
    setAnimar(false);
    const raf = requestAnimationFrame(() => {
      requestAnimationFrame(() => setAnimar(true));
    });
    return () => cancelAnimationFrame(raf);
  }, [score]);

  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="mb-5 flex items-end justify-between gap-3">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
            Score del lead
          </h3>
          <div className="mt-1.5 flex items-center gap-2.5">
            <span className="text-4xl font-bold leading-none tabular-nums text-futuro-base">
              {score?.total ?? 0}
            </span>
            <span
              className={cn(
                'inline-flex items-center gap-1.5 rounded-md border px-2 py-1 text-[11px] font-bold uppercase tracking-wider',
                BADGE_BANDA[banda]
              )}
            >
              <span
                className={cn('size-1.5 rounded-full', DOT_BANDA[banda])}
                aria-hidden="true"
              />
              {etiqueta(banda)}
            </span>
          </div>
        </div>
        <span className="text-[11px] font-medium tabular-nums text-muted-foreground">
          / 100
        </span>
      </div>

      {/* 4 dimensiones de 25 puntos: el desglose es el argumento */}
      <div className="mb-5 space-y-3.5">
        <ScoreBar label="Interés" value={score?.interes} max={25} animar={animar} />
        <ScoreBar label="Presupuesto" value={score?.presupuesto} max={25} animar={animar} />
        <ScoreBar label="Perfil" value={score?.perfil} max={25} animar={animar} />
        <ScoreBar label="Urgencia" value={score?.urgencia} max={25} animar={animar} />
      </div>

      {/* La justificación sostiene la tesis del producto */}
      <div className={cn('rounded-lg border-l-4 bg-muted/60 p-3.5', BORDE_BANDA[banda])}>
        <p className="text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
          Justificación del score
        </p>
        <p className="mt-1 text-[13px] leading-relaxed text-foreground">
          {score?.justificacion || 'Sin justificación disponible para este lead.'}
        </p>
      </div>

      <p className="mt-3 flex items-start gap-1.5 text-[11px] leading-snug text-muted-foreground">
        <Info className="mt-px size-3 shrink-0" aria-hidden="true" />
        Este número lo calcula código determinista, dimensión por dimensión — el LLM
        solo extrae señales.
      </p>
    </section>
  );
}
