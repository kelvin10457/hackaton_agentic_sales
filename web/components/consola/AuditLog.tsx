'use client';

import React from 'react';
import { Bot, CheckCircle2, Clock, RotateCcw, ShieldAlert, User } from 'lucide-react';

import { CitationChip } from '@/components/shared/citation-chip';
import { etiqueta, formatFechaLarga, formatHora, formatRelativo } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Lead } from '@/lib/types';
import type { AccionRealizada } from './LeadDetailPanel';

interface LogEntry {
  ts: string;
  actor: 'agente' | 'guardrail' | 'usuario' | 'ejecutivo';
  nombreActor: string;
  evento: string;
  metadato?: string;
  fuentes?: string[];
  esHumano?: boolean;
  esRechazo?: boolean;
}

/**
 * La bitácora se construye desde los DATOS del lead (no strings sueltos):
 * quién hizo qué, cuándo y con qué fuentes. Aquí se cierra la tesis:
 * el agente propone — la persona decide, y queda registrado.
 */
function construirBitacora(lead: Lead): LogEntry[] {
  const base = lead.ultima_actividad ?? new Date().toISOString();
  const hace = (minutos: number) =>
    new Date(new Date(base).getTime() - minutos * 60_000).toISOString();

  const entradas: LogEntry[] = [];
  const accion = lead.accion_propuesta;
  const consentComercial =
    lead.consentimiento?.comunicaciones_comerciales?.otorgado ?? false;
  const consentDatos = lead.consentimiento?.tratamiento_datos?.otorgado ?? false;

  if (accion) {
    entradas.push({
      ts: hace(0),
      actor: 'agente',
      nombreActor: 'Agente IA',
      evento: `Propuso acción: ${etiqueta(accion.tipo).toLowerCase()}`,
      fuentes: accion.fuentes_consultadas,
    });
  }

  entradas.push({
    ts: hace(4),
    actor: 'usuario',
    nombreActor: lead.identidad.nombre,
    evento: consentComercial
      ? 'Otorgó consentimiento (tratamiento de datos y comunicaciones comerciales)'
      : consentDatos
        ? 'Otorgó tratamiento de datos y negó comunicaciones comerciales'
        : 'No otorgó consentimientos',
  });

  entradas.push({
    ts: hace(5),
    actor: 'agente',
    nombreActor: 'Agente IA',
    evento: `Score recalculado: ${lead.score?.total ?? 0}`,
    metadato: `Banda: ${etiqueta(lead.score?.banda).toUpperCase()}`,
  });

  // Traza de guardrails de la demo de María (escena 1:00–1:20 del vídeo)
  if (lead.id === 'lead_001') {
    entradas.push({
      ts: hace(7),
      actor: 'guardrail',
      nombreActor: 'Guardrail G2 · Negativa honesta',
      evento: 'Consulta fuera del corpus aprobado — el agente respondió que no sabe',
      metadato: 'Consulta: "bitcoin"',
    });
    entradas.push({
      ts: hace(9),
      actor: 'guardrail',
      nombreActor: 'Guardrail G1 · No-asesoramiento',
      evento: 'Bloqueo de recomendación de inversión directa',
      metadato: 'Consulta: "en qué invierto"',
    });
  }

  return entradas;
}

const ESTILO_ICONO: Record<LogEntry['actor'], string> = {
  agente: 'border-futuro-ia/25 bg-futuro-ia/10 text-futuro-ia',
  guardrail: 'border-red-200 bg-red-50 text-red-600',
  usuario: 'border-border bg-muted text-muted-foreground',
  ejecutivo: 'border-emerald-600 bg-emerald-500 text-white shadow-md',
};

const ETIQUETA_ACTOR: Record<LogEntry['actor'], string> = {
  agente: 'IA',
  guardrail: 'Guardrail',
  usuario: 'Prospecto',
  ejecutivo: 'Humano',
};

export default function AuditLog({
  lead,
  accionSimulada,
}: {
  lead: Lead;
  accionSimulada?: AccionRealizada | null;
}) {
  if (!lead) return null;

  const timeline = construirBitacora(lead);

  if (accionSimulada) {
    const esRechazo = accionSimulada.tipo === 'rechazar';
    const esEdicion = accionSimulada.tipo === 'editar_aprobar';
    timeline.unshift({
      ts: new Date().toISOString(),
      actor: 'ejecutivo',
      nombreActor: 'Carlos Peña',
      evento: esRechazo
        ? 'Rechazó la propuesta y devolvió el lead a nutrición'
        : esEdicion
          ? 'Editó el borrador y aprobó el envío'
          : 'Aprobó la comunicación propuesta sin cambios',
      metadato: accionSimulada.data?.motivo
        ? `Motivo: ${accionSimulada.data.motivo}`
        : undefined,
      esHumano: true,
      esRechazo,
    });
  }

  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <h3 className="mb-5 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
        <Clock className="size-4" aria-hidden="true" />
        Bitácora de auditoría
      </h3>

      <ol className="relative ml-2.5 space-y-5 border-l border-border pl-6">
        {timeline.map((log, index) => {
          let Icono: React.ElementType = Bot;
          if (log.actor === 'guardrail') Icono = ShieldAlert;
          if (log.actor === 'usuario') Icono = User;
          if (log.actor === 'ejecutivo') Icono = log.esRechazo ? RotateCcw : CheckCircle2;

          return (
            <li key={index} className="relative">
              <span
                className={cn(
                  'absolute -left-[35px] top-0 flex size-6 items-center justify-center rounded-full border',
                  ESTILO_ICONO[log.actor]
                )}
              >
                <Icono className="size-3" aria-hidden="true" />
              </span>

              <div
                className={cn(
                  log.esHumano &&
                    '-mx-2 -mt-1 rounded-lg bg-emerald-50/80 p-2 ring-1 ring-emerald-100'
                )}
              >
                <div className="flex flex-wrap items-baseline justify-between gap-x-3 gap-y-0.5">
                  <p className="flex items-center gap-2 text-[13px] font-semibold text-foreground">
                    {log.nombreActor}
                    <span
                      className={cn(
                        'rounded px-1.5 py-px text-[9px] font-bold uppercase tracking-wider',
                        log.esHumano
                          ? 'bg-emerald-100 text-emerald-700'
                          : 'bg-muted text-muted-foreground'
                      )}
                    >
                      {ETIQUETA_ACTOR[log.actor]}
                    </span>
                  </p>
                  <time
                    dateTime={log.ts}
                    title={`${formatFechaLarga(log.ts)} · ${formatRelativo(log.ts)}`}
                    className="font-mono text-[11px] tabular-nums text-muted-foreground"
                  >
                    {formatHora(log.ts)}
                  </time>
                </div>

                <p
                  className={cn(
                    'mt-0.5 text-[13px] leading-relaxed',
                    log.esHumano ? 'font-medium text-emerald-900' : 'text-muted-foreground'
                  )}
                >
                  {log.evento}
                </p>

                {log.metadato && (
                  <p className="mt-1.5 inline-block rounded border border-border bg-muted/60 px-1.5 py-0.5 font-mono text-[11px] text-futuro-corp">
                    {log.metadato}
                  </p>
                )}

                {log.fuentes && log.fuentes.length > 0 && (
                  <div className="mt-1.5 flex flex-wrap gap-1.5">
                    {log.fuentes.map((fuente) => (
                      <CitationChip key={fuente} cita={fuente} />
                    ))}
                  </div>
                )}
              </div>
            </li>
          );
        })}

        {/* Origen de la sesión */}
        <li className="relative">
          <span
            className="absolute -left-[33px] top-1 size-[18px] rounded-full border-2 border-border bg-card"
            aria-hidden="true"
          />
          <p className="text-xs font-medium text-muted-foreground/80">
            Sesión iniciada en el canal público (chat sin registro)
          </p>
        </li>
      </ol>
    </section>
  );
}
