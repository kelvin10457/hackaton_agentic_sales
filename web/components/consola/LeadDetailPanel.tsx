'use client';

import React, { useEffect, useState } from 'react';
import {
  Briefcase,
  Building2,
  CheckCircle2,
  FileText,
  Mail,
  RotateCcw,
  ShieldCheck,
  ShieldX,
  Trash2,
} from 'lucide-react';

import { eliminarLead } from '@/lib/consola-api';

import ScorePanel from './ScorePanel';
import BriefPanel from './BriefPanel';
import AuditLog from './AuditLog';
import ApprovalBlock from './ApprovalBlock';
import AsignarAsesor from './AsignarAsesor';
import { Badge } from '@/components/shared/badge';
import { etiqueta, formatFechaLarga, formatRelativo } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Lead } from '@/lib/types';

export interface AccionRealizada {
  tipo: 'aprobar' | 'editar_aprobar' | 'rechazar';
  data: { motivo?: string; asunto?: string; cuerpo?: string };
}

function ChipConsentimiento({
  otorgado,
  texto,
  timestamp,
}: {
  otorgado: boolean;
  texto: string;
  timestamp?: string;
}) {
  const detalle = otorgado
    ? `Otorgado${timestamp ? ` el ${formatFechaLarga(timestamp)}` : ''}`
    : 'No otorgado';
  return (
    <span
      title={`${texto}: ${detalle}`}
      className={cn(
        'inline-flex items-center gap-1 rounded-md border px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wide [&_svg]:size-3',
        otorgado
          ? 'border-emerald-200 bg-emerald-50 text-emerald-700'
          : 'border-red-200 bg-red-50 text-red-700'
      )}
    >
      {otorgado ? (
        <ShieldCheck aria-hidden="true" />
      ) : (
        <ShieldX aria-hidden="true" />
      )}
      {texto}
      <span className="sr-only">: {detalle}</span>
    </span>
  );
}

function ResolucionCard({ accion, lead }: { accion: AccionRealizada; lead: Lead }) {
  if (accion.tipo === 'rechazar') {
    return (
      <section className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-5">
        <RotateCcw className="mt-0.5 size-5 shrink-0 text-amber-600" aria-hidden="true" />
        <div>
          <p className="text-sm font-bold text-amber-900">Propuesta rechazada</p>
          <p className="mt-1 text-[13px] leading-relaxed text-amber-800">
            {lead.identidad.nombre.split(' ')[0]} vuelve a nutrición — el lead no se
            descarta.
            {accion.data.motivo ? ` Motivo: “${accion.data.motivo}”.` : ''} La decisión
            quedó registrada en la bitácora.
          </p>
        </div>
      </section>
    );
  }
  const editada = accion.tipo === 'editar_aprobar';
  return (
    <section className="flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-5">
      <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" aria-hidden="true" />
      <div>
        <p className="text-sm font-bold text-emerald-900">
          {editada ? 'Borrador editado y aprobado' : 'Comunicación aprobada'}
        </p>
        <p className="mt-1 text-[13px] leading-relaxed text-emerald-800">
          Envío simulado a {lead.identidad.email ?? 'su correo'}. La decisión quedó
          sellada en la bitácora con la autoría de Carlos Peña
          {editada ? ' y la marca de edición humana' : ''}.
        </p>
      </div>
    </section>
  );
}

export default function LeadDetailPanel({
  lead,
  onDelete,
}: {
  lead: Lead | null;
  onDelete?: () => void;
}) {
  const [accionRealizada, setAccionRealizada] = useState<AccionRealizada | null>(null);
  const [eliminando, setEliminando] = useState(false);

  useEffect(() => {
    setAccionRealizada(null);
  }, [lead?.id]);

  const handleEliminar = async () => {
    if (!lead) return;
    if (
      window.confirm(
        `¿Estás seguro de que deseas eliminar permanentemente a ${lead.identidad.nombre}? Esta acción no se puede deshacer y limpiará todo su historial.`
      )
    ) {
      setEliminando(true);
      try {
        await eliminarLead(lead.id);
        if (onDelete) onDelete();
      } catch (err) {
        console.error('Fallo al eliminar:', err);
        alert('Error al eliminar el lead');
        setEliminando(false);
      }
    }
  };

  // Regla 6: estado vacío cuidado si no hay lead seleccionado
  if (!lead) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-3 bg-background p-8 text-center">
        <span className="flex size-14 items-center justify-center rounded-2xl border border-border bg-card shadow-sm">
          <Briefcase className="size-6 text-muted-foreground/60" strokeWidth={1.5} aria-hidden="true" />
        </span>
        <div>
          <h3 className="text-sm font-semibold text-foreground">
            Ningún lead seleccionado
          </h3>
          <p className="mx-auto mt-1 max-w-xs text-[13px] leading-relaxed text-muted-foreground">
            Elige un prospecto del pipeline para ver su score explicado, el brief y la
            acción que propone el agente.
          </p>
        </div>
      </div>
    );
  }

  const iniciales = lead.identidad.nombre
    .split(' ')
    .map((p) => p[0])
    .slice(0, 2)
    .join('')
    .toUpperCase();

  return (
    <div className="scrollbar-thin flex h-full flex-col overflow-y-auto bg-background">
      {/* Cabecera de identidad (sticky para no perder contexto) */}
      <div className="sticky top-0 z-10 border-b border-border bg-card px-4 py-4 shadow-sm sm:px-6">
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="flex min-w-0 items-start gap-3">
            <span
              aria-hidden="true"
              className="flex size-11 shrink-0 items-center justify-center rounded-xl bg-futuro-base text-sm font-bold text-white"
            >
              {iniciales}
            </span>
            <div className="min-w-0">
              <h2 className="flex flex-wrap items-center gap-2 text-lg font-bold leading-tight text-foreground sm:text-xl">
                {lead.identidad.nombre}
                <Badge variant="outline" className="uppercase tracking-wider">
                  {lead.tipo}
                </Badge>
              </h2>
              <div className="mt-1.5 flex flex-wrap items-center gap-x-4 gap-y-1 text-[13px] text-muted-foreground">
                {lead.identidad.email && (
                  <span className="flex items-center gap-1.5">
                    <Mail className="size-3.5 shrink-0" aria-hidden="true" />
                    <span className="truncate">{lead.identidad.email}</span>
                  </span>
                )}
                {lead.identidad.documento && (
                  <span className="flex items-center gap-1.5">
                    <FileText className="size-3.5 shrink-0" aria-hidden="true" />
                    CI {lead.identidad.documento}
                  </span>
                )}
                {lead.identidad.empresa && (
                  <span className="flex items-center gap-1.5">
                    <Building2 className="size-3.5 shrink-0" aria-hidden="true" />
                    {lead.identidad.empresa}
                  </span>
                )}
                {lead.ultima_actividad && (
                  <span
                    title={formatFechaLarga(lead.ultima_actividad)}
                    className="tabular-nums"
                  >
                    Actividad {formatRelativo(lead.ultima_actividad)}
                  </span>
                )}
              </div>
            </div>
          </div>

          <div className="mt-2 flex w-full shrink-0 items-center justify-between gap-4 sm:mt-0 sm:w-auto sm:justify-end">
            <div className="flex flex-col items-start gap-1.5 sm:items-end">
              <Badge variant="secondary">{etiqueta(lead.etapa_embudo)}</Badge>
              <div className="flex gap-1.5">
                <ChipConsentimiento
                  otorgado={lead.consentimiento?.tratamiento_datos?.otorgado ?? false}
                  texto="Datos"
                  timestamp={lead.consentimiento?.tratamiento_datos?.timestamp}
                />
                <ChipConsentimiento
                  otorgado={
                    lead.consentimiento?.comunicaciones_comerciales?.otorgado ?? false
                  }
                  texto="Comercial"
                  timestamp={lead.consentimiento?.comunicaciones_comerciales?.timestamp}
                />
              </div>
            </div>

            <button
              type="button"
              onClick={handleEliminar}
              disabled={eliminando}
              className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-1.5 text-sm font-semibold text-red-600 transition-colors hover:bg-red-100 hover:text-red-700 disabled:opacity-50"
              title="Eliminar permanentemente"
            >
              <Trash2 className="size-4" aria-hidden="true" />
              Eliminar
            </button>
          </div>
        </div>
      </div>

      {/* Cuerpo: score → brief → acción → bitácora */}
      <div key={lead.id} className="animate-fade-up space-y-4 p-4 sm:p-6">
        <ScorePanel score={lead.score} />
        <BriefPanel lead={lead} />

        {accionRealizada ? (
          <ResolucionCard accion={accionRealizada} lead={lead} />
        ) : (
          <ApprovalBlock
            lead={lead}
            onActionComplete={(tipo, data) => setAccionRealizada({ tipo, data })}
          />
        )}

        {/* Asignar asesor: solo si el prospecto autorizó ser contactado. */}
        {lead.consentimiento?.comunicaciones_comerciales?.otorgado && (
          <AsignarAsesor leadId={lead.id} nombreLead={lead.identidad.nombre} />
        )}

        <AuditLog lead={lead} accionSimulada={accionRealizada} />
      </div>
    </div>
  );
}
