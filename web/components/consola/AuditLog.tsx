'use client';

import React, { useEffect, useState } from 'react';
import { Bot, CheckCircle2, Clock, RotateCcw, ShieldAlert, User } from 'lucide-react';

import { fetchAuditoria, type EventoAuditoriaRaw } from '@/lib/consola-api';
import { CitationChip } from '@/components/shared/citation-chip';
import { etiqueta, formatFechaLarga, formatHora, formatRelativo } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Lead } from '@/lib/types';
import type { AccionRealizada } from './LeadDetailPanel';

interface LogEntry {
  ts: string;
  actor: 'agente' | 'guardrail' | 'usuario' | 'ejecutivo' | 'sistema';
  nombreActor: string;
  evento: string;
  metadato?: string;
  fuentes?: string[];
  esHumano?: boolean;
  esRechazo?: boolean;
}

/**
 * Convierte un evento de auditoría del backend al formato de la bitácora visual.
 */
function mapearEvento(raw: EventoAuditoriaRaw): LogEntry {
  let actor: LogEntry['actor'] = 'agente';
  let nombreActor = raw.actor_id;
  let esHumano = false;
  let esRechazo = false;

  if (raw.actor === 'humano') {
    actor = 'ejecutivo';
    nombreActor = raw.actor_id || 'Ejecutivo';
    esHumano = true;
  } else if (raw.actor === 'sistema') {
    actor = 'sistema';
    nombreActor = 'Sistema';
  } else {
    actor = 'agente';
    nombreActor = 'Agente IA';
  }

  // Mapear tipo_evento a texto legible
  const textos: Record<string, string> = {
    lead_creado: 'Lead creado en el sistema',
    lead_actualizado: 'Lead actualizado',
    identidad_verificada: 'Identidad verificada (cédula/RUC)',
    consentimiento_otorgado: `Consentimiento otorgado: ${(raw.payload as Record<string, string>)?.finalidad ?? 'datos'}`,
    score_calculado: `Score recalculado: ${(raw.payload as Record<string, number>)?.total ?? '—'}`,
    accion_generada: 'Acción propuesta generada',
    // Aquí se cierra la tesis: el agente nunca tuvo la capacidad de enviarlo.
    accion_aprobada: (raw.payload as Record<string, unknown>)?.editado_por_humano
      ? 'EDITÓ el borrador y APROBÓ el envío'
      : 'APROBÓ la comunicación propuesta sin cambios',
    accion_rechazada: 'Propuesta rechazada — lead a nutrición',
    crm_upsert: 'Lead sincronizado al CRM',
    error: `Error: ${(raw.payload as Record<string, string>)?.mensaje ?? 'desconocido'}`,
  };

  if (raw.tipo_evento === 'accion_rechazada') esRechazo = true;

  const evento = textos[raw.tipo_evento] ?? etiqueta(raw.tipo_evento);

  // Extraer metadato relevante del payload
  let metadato: string | undefined;
  if (raw.payload) {
    const p = raw.payload as Record<string, unknown>;
    if (p.banda) metadato = `Banda: ${String(p.banda).toUpperCase()}`;
    if (p.motivo_rechazo) metadato = `Motivo: ${p.motivo_rechazo}`;
    if (p.accion) metadato = `Acción: ${p.accion}`;
    // La marca de responsabilidad (Biblia §10): no se censura al asesor
    // habilitado, se le hace RESPONSABLE.
    if (p.editado_por_humano === true) metadato = 'editado_por_humano = true';
  }

  return {
    ts: raw.timestamp,
    actor,
    nombreActor,
    evento,
    metadato,
    esHumano,
    esRechazo,
  };
}

/**
 * Construye la bitácora fallback si no hay datos del backend.
 * Replica el comportamiento original para que nunca esté vacía.
 */
function construirBitacoraLocal(lead: Lead): LogEntry[] {
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

  return entradas;
}

const ESTILO_ICONO: Record<string, string> = {
  agente: 'border-futuro-ia/25 bg-futuro-ia/10 text-futuro-ia',
  guardrail: 'border-red-200 bg-red-50 text-red-600',
  usuario: 'border-border bg-muted text-muted-foreground',
  ejecutivo: 'border-emerald-600 bg-emerald-500 text-white shadow-md',
  sistema: 'border-border bg-muted text-muted-foreground',
};

const ETIQUETA_ACTOR: Record<string, string> = {
  agente: 'IA',
  guardrail: 'Guardrail',
  usuario: 'Prospecto',
  ejecutivo: 'Humano',
  sistema: 'Sistema',
};

export default function AuditLog({
  lead,
  accionSimulada,
}: {
  lead: Lead;
  accionSimulada?: AccionRealizada | null;
}) {
  const [timeline, setTimeline] = useState<LogEntry[]>([]);
  const [cargando, setCargando] = useState(false);

  useEffect(() => {
    if (!lead) return;

    let cancelado = false;
    setCargando(true);

    fetchAuditoria(Number(lead.id))
      .then((eventos) => {
        if (cancelado) return;
        if (eventos.length > 0) {
          setTimeline(eventos.map(mapearEvento));
        } else {
          // Fallback: construir bitácora local si la API no devuelve eventos
          setTimeline(construirBitacoraLocal(lead));
        }
      })
      .catch(() => {
        if (cancelado) return;
        // En caso de error, usar bitácora local
        setTimeline(construirBitacoraLocal(lead));
      })
      .finally(() => {
        if (!cancelado) setCargando(false);
      });

    return () => {
      cancelado = true;
    };
  }, [lead?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!lead) return null;

  // Insertar acción del ejecutivo al inicio de la timeline
  const timelineFinal = [...timeline];
  if (accionSimulada) {
    const esRechazo = accionSimulada.tipo === 'rechazar';
    const esEdicion = accionSimulada.tipo === 'editar_aprobar';
    timelineFinal.unshift({
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
        {cargando && (
          <span className="ml-2 inline-block size-3 animate-spin rounded-full border-2 border-muted-foreground border-t-transparent" />
        )}
      </h3>

      <ol className="relative ml-2.5 space-y-5 border-l border-border pl-6">
        {timelineFinal.map((log, index) => {
          let Icono: React.ElementType = Bot;
          if (log.actor === 'guardrail') Icono = ShieldAlert;
          if (log.actor === 'usuario') Icono = User;
          if (log.actor === 'sistema') Icono = User;
          if (log.actor === 'ejecutivo') Icono = log.esRechazo ? RotateCcw : CheckCircle2;

          return (
            <li key={index} className="relative">
              <span
                className={cn(
                  'absolute -left-[35px] top-0 flex size-6 items-center justify-center rounded-full border',
                  ESTILO_ICONO[log.actor] ?? ESTILO_ICONO.sistema
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
                      {ETIQUETA_ACTOR[log.actor] ?? 'Sistema'}
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
                  <p className="mt-1.5 inline-block rounded border border-border bg-muted/60 px-1.5 py-0.5 font-mono text-[11px] text-futuro-corp dark:text-futuro-sky">
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
