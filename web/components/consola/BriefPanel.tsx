import React from 'react';
import {
  AlertTriangle,
  DollarSign,
  MessageSquare,
  Route,
  Shield,
  Target,
} from 'lucide-react';

import { etiqueta, formatUSD } from '@/lib/format';
import type { Lead } from '@/lib/types';

function Campo({
  icono: Icono,
  titulo,
  children,
}: {
  icono: React.ElementType;
  titulo: string;
  children: React.ReactNode;
}) {
  return (
    <div>
      <p className="mb-1 flex items-center gap-1.5 text-[11px] font-semibold uppercase tracking-wider text-muted-foreground">
        <Icono className="size-3.5" aria-hidden="true" />
        {titulo}
      </p>
      {children}
    </div>
  );
}

export default function BriefPanel({ lead }: { lead: Lead }) {
  if (!lead) return null;

  const objeciones = Array.isArray(lead.objeciones)
    ? lead.objeciones
    : lead.objeciones
      ? [lead.objeciones as unknown as string]
      : [];

  return (
    <section className="borde-degradado-suave rounded-xl p-5 shadow-sm">
      <h3 className="mb-4 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
        <Target className="size-4" aria-hidden="true" />
        Brief del lead
      </h3>

      <div className="space-y-4">
        <Campo icono={MessageSquare} titulo="Necesidad">
          <p className="rounded-lg border border-border bg-muted/60 p-3 text-[13px] leading-relaxed text-foreground">
            {lead.necesidad || 'No especificada todavía por el agente.'}
          </p>
        </Campo>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
          <Campo icono={Shield} titulo="Perfil de riesgo">
            <p className="text-sm font-bold uppercase tracking-wide text-futuro-corp dark:text-futuro-sky">
              {etiqueta(lead.senales?.perfil_riesgo as string) }
            </p>
          </Campo>
          <Campo icono={Route} titulo="Ruta sugerida">
            <p className="text-sm font-semibold text-futuro-corp dark:text-futuro-sky">
              {etiqueta(lead.ruta_sugerida)}
            </p>
          </Campo>
          {typeof lead.senales?.monto_declarado_usd === 'number' && (
            <Campo icono={DollarSign} titulo="Monto declarado">
              <p className="text-sm font-semibold tabular-nums text-foreground">
                {formatUSD(lead.senales.monto_declarado_usd)}
              </p>
            </Campo>
          )}
        </div>

        {objeciones.length > 0 && (
          <Campo icono={AlertTriangle} titulo="Objeciones identificadas">
            <ul className="space-y-1.5">
              {objeciones.map((obj) => (
                <li
                  key={obj}
                  className="flex items-start gap-2 rounded-lg border border-amber-200/60 bg-amber-50/60 px-3 py-2 text-[13px] leading-snug text-amber-900"
                >
                  <AlertTriangle
                    className="mt-0.5 size-3.5 shrink-0 text-amber-500"
                    aria-hidden="true"
                  />
                  {obj}
                </li>
              ))}
            </ul>
          </Campo>
        )}
      </div>
    </section>
  );
}
