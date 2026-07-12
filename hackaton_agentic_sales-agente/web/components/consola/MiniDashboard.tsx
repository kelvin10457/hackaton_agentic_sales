'use client';

import React from 'react';
import { Flame, Target, Users } from 'lucide-react';

import type { Banda, Lead } from '@/lib/types';
import { cn } from '@/lib/utils';

const DOT: Record<Banda, string> = {
  caliente: 'bg-banda-caliente',
  tibio: 'bg-banda-tibio',
  frio: 'bg-banda-frio',
};

function Kpi({
  icono: Icono,
  valor,
  etiqueta,
  tono,
  nota,
}: {
  icono: React.ElementType;
  valor: string | number;
  etiqueta: string;
  tono: 'base' | 'caliente' | 'ok';
  nota?: string;
}) {
  const tonos = {
    base: 'bg-accent text-futuro-corp',
    caliente: 'bg-red-50 text-banda-caliente',
    ok: 'bg-emerald-50 text-emerald-600',
  } as const;

  return (
    <div className="flex flex-col rounded-xl border border-border bg-card p-3 shadow-sm">
      <span
        className={cn('mb-2 flex size-7 items-center justify-center rounded-lg', tonos[tono])}
        aria-hidden="true"
      >
        <Icono className="size-3.5" />
      </span>
      <span className="text-xl font-bold leading-none tabular-nums text-foreground">
        {valor}
      </span>
      <span className="mt-1 text-[10px] font-semibold uppercase tracking-wider text-muted-foreground">
        {etiqueta}
        {nota && <span className="ml-1 font-normal normal-case opacity-70">({nota})</span>}
      </span>
    </div>
  );
}

export default function MiniDashboard({ leads }: { leads: Lead[] }) {
  const total = leads?.length ?? 0;
  const porBanda: Record<Banda, number> = {
    caliente: leads?.filter((l) => l.score?.banda === 'caliente').length ?? 0,
    tibio: leads?.filter((l) => l.score?.banda === 'tibio').length ?? 0,
    frio: leads?.filter((l) => l.score?.banda === 'frio').length ?? 0,
  };
  const pctCalientes = total > 0 ? Math.round((porBanda.caliente / total) * 100) : 0;
  // Métrica simulada hasta que R2 exponga /api/consola/metricas
  const tasaAprobacion = 92;

  return (
    <div className="shrink-0 border-b border-border bg-card p-3.5">
      <h2 className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
        Rendimiento de campaña
      </h2>

      <div className="mt-2.5 grid grid-cols-3 gap-2.5">
        <Kpi icono={Users} valor={total} etiqueta="Leads" tono="base" />
        <Kpi icono={Flame} valor={`${pctCalientes}%`} etiqueta="Calientes" tono="caliente" />
        <Kpi icono={Target} valor={`${tasaAprobacion}%`} etiqueta="Aprobación" tono="ok" />
      </div>

      {/* Distribución por banda: el color siempre con significado */}
      <div className="mt-3">
        <div
          className="flex h-1.5 w-full gap-px overflow-hidden rounded-full bg-muted"
          role="img"
          aria-label={`Distribución del pipeline: ${porBanda.caliente} calientes, ${porBanda.tibio} tibios, ${porBanda.frio} fríos`}
        >
          {(Object.keys(porBanda) as Banda[]).map(
            (b) =>
              porBanda[b] > 0 && (
                <div
                  key={b}
                  className={cn('h-full transition-all duration-500', DOT[b])}
                  style={{ width: `${(porBanda[b] / Math.max(total, 1)) * 100}%` }}
                />
              )
          )}
        </div>
        <div className="mt-1.5 flex items-center gap-3 text-[10px] font-medium text-muted-foreground">
          {(Object.keys(porBanda) as Banda[]).map((b) => (
            <span key={b} className="flex items-center gap-1">
              <span className={cn('size-1.5 rounded-full', DOT[b])} aria-hidden="true" />
              {b === 'caliente' ? 'Caliente' : b === 'tibio' ? 'Tibio' : 'Frío'}
              <span className="tabular-nums">{porBanda[b]}</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
