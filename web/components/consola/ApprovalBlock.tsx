'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  aprobarAccion as apiAprobar,
  rechazarAccion as apiRechazar,
} from '@/lib/consola-api';
import {
  AlertTriangle,
  BookOpen,
  Bot,
  CheckCircle2,
  Edit3,
  Loader2,
  Lock,
  Mail,
  MessageSquare,
  Phone,
  RotateCcw,
  ShieldAlert,
  ShieldCheck,
  X,
} from 'lucide-react';

import { Badge } from '@/components/shared/badge';
import { Button } from '@/components/shared/button';
import { Input } from '@/components/shared/input';
import { Textarea } from '@/components/shared/textarea';
import { CitationChip } from '@/components/shared/citation-chip';
import { useToast } from '@/components/shared/toast';
import { etiqueta } from '@/lib/format';
import type { AccionPropuesta, Lead } from '@/lib/types';

interface ApprovalBlockProps {
  lead: Lead;
  onActionComplete?: (
    tipo: 'aprobar' | 'editar_aprobar' | 'rechazar',
    data: { motivo?: string; asunto?: string; cuerpo?: string }
  ) => void;
}

/** Propuesta de respaldo mientras R1 no entregue la real (H14) */
function accionPorDefecto(lead: Lead): AccionPropuesta {
  return {
    id: `acc_${lead.id}`,
    lead_id: lead.id,
    tipo: 'agendar_reunion',
    destinatario: { email: lead.identidad.email, nombre: lead.identidad.nombre },
    borrador: {
      canal: 'email',
      asunto: 'Asesoría personalizada — Futuro Academy',
      cuerpo: `Hola ${lead.identidad.nombre},\n\nHe revisado tu interés en nuestros programas de formación financiera. Te sugiero agendar una breve sesión de 15 minutos para estructurar tu ruta de aprendizaje de forma segura.\n\nSaludos cordiales,\nCarlos Peña · Futuro Academy`,
    },
    razonamiento: `Score ${lead.score?.total ?? 0} (${etiqueta(lead.score?.banda)}). Propuesta generada con la información disponible del lead.`,
    fuentes_consultadas: [],
    estado: 'pendiente',
    revisado_por: null,
    editado_por_humano: false,
  };
}

export default function ApprovalBlock({ lead, onActionComplete }: ApprovalBlockProps) {
  const accion = useMemo(
    () => lead.accion_propuesta ?? accionPorDefecto(lead),
    [lead]
  );

  const [asunto, setAsunto] = useState(accion.borrador.asunto);
  const [cuerpo, setCuerpo] = useState(accion.borrador.cuerpo);
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [mostrarRechazo, setMostrarRechazo] = useState(false);
  const [enviando, setEnviando] = useState(false);
  const { toast } = useToast();

  // Resincroniza el borrador al cambiar de lead en el master–detail
  useEffect(() => {
    setAsunto(accion.borrador.asunto);
    setCuerpo(accion.borrador.cuerpo);
    setMostrarRechazo(false);
    setMotivoRechazo('');
    setEnviando(false);
  }, [accion]);

  // Verificación estricta: sin dato explícito, se asume NO consentido
  const consentimientoComercial =
    lead.consentimiento?.comunicaciones_comerciales?.otorgado ?? false;
  const bloqueado = !consentimientoComercial;
  const esObsoleta = accion.estado === 'obsoleta';
  // Una acción que ya pasó por manos humanas NO se vuelve a decidir: se muestra
  // su resolución. Sin esto, aprobar dos veces devolvía 409 en la consola.
  const yaResuelta =
    accion.estado === 'aprobada' ||
    accion.estado === 'editada_y_aprobada' ||
    accion.estado === 'rechazada' ||
    accion.estado === 'ejecutada';
  const editado =
    asunto !== accion.borrador.asunto || cuerpo !== accion.borrador.cuerpo;
  const camposDeshabilitados = bloqueado || esObsoleta || yaResuelta;

  async function aprobar() {
    if (enviando) return;              // guarda anti doble-clic
    const tipo = editado ? 'editar_aprobar' : 'aprobar';
    setEnviando(true);
    try {
      // Se envía SIEMPRE el borrador en pantalla. El backend compara con el que
      // redactó el agente: si cambió, queda como 'editada_y_aprobada' y marca
      // editado_por_humano. La edición ya no se pierde (criterio 3.3).
      await apiAprobar(Number(accion.id), { asunto, cuerpo });
      onActionComplete?.(tipo, { asunto, cuerpo });
      toast({
        tipo: 'success',
        titulo: editado ? 'Borrador editado y aprobado' : 'Comunicación aprobada',
        descripcion: editado
          ? 'Queda registrado en la bitácora que la última palabra fue tuya.'
          : 'Registrado en la bitácora del backend con tu autoría.',
      });
    } catch (err) {
      setEnviando(false);
      toast({
        tipo: 'error',
        titulo: 'Error al aprobar',
        descripcion: err instanceof Error ? err.message : String(err),
      });
    }
  }

  async function rechazar() {
    if (enviando) return;
    setEnviando(true);
    try {
      await apiRechazar(Number(accion.id), motivoRechazo.trim());
      onActionComplete?.('rechazar', { motivo: motivoRechazo.trim() });
      toast({
        tipo: 'info',
        titulo: 'Propuesta rechazada',
        descripcion: 'El lead vuelve a nutrición — no se descarta.',
      });
    } catch (err) {
      setEnviando(false);
      toast({
        tipo: 'error',
        titulo: 'Error al rechazar',
        descripcion: err instanceof Error ? err.message : String(err),
      });
    }
  }

  function canalAlternativo(nombre: string) {
    toast({
      tipo: 'info',
      titulo: `Canal alternativo: ${nombre}`,
      descripcion: 'Disponible porque no requiere consentimiento comercial (demo).',
    });
  }

  const idBloqueo = `bloqueo-${lead.id}`;

  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h3 className="text-xs font-bold uppercase tracking-widest text-muted-foreground">
          Acción propuesta por el agente
        </h3>
        <Badge
          variant={
            accion.estado === 'rechazada'
              ? 'warning'
              : yaResuelta
                ? 'success'
                : esObsoleta
                  ? 'warning'
                  : 'accent'
          }
        >
          {etiqueta(accion.estado)}
        </Badge>
      </div>

      <div className="mt-3 flex flex-wrap items-center gap-x-3 gap-y-1.5 text-[13px]">
        <Badge variant="secondary">{etiqueta(accion.tipo)}</Badge>
        {accion.destinatario?.email && (
          <span className="flex min-w-0 items-center gap-1.5 text-muted-foreground">
            <Mail className="size-3.5 shrink-0" aria-hidden="true" />
            <span className="truncate">
              {accion.destinatario.nombre} · {accion.destinatario.email}
            </span>
          </span>
        )}
      </div>

      {/* Aviso de propuesta obsoleta (coherencia de datos) */}
      {esObsoleta && (
        <div
          role="alert"
          className="mt-3 flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50 p-3"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-600" aria-hidden="true" />
          <p className="text-[13px] leading-relaxed text-amber-900">
            <strong className="font-bold">Propuesta obsoleta:</strong> los datos del
            lead cambiaron después de generar este borrador. El agente debe
            regenerarla antes de cualquier decisión.
          </p>
        </div>
      )}

      {/* Razonamiento del agente + fuentes (violeta = voz de la IA) */}
      <div className="mt-3 rounded-lg border border-futuro-ia/15 bg-futuro-ia/5 p-3.5">
        <p className="flex items-center gap-1.5 text-[10px] font-bold uppercase tracking-wider text-futuro-ia">
          <Bot className="size-3.5" aria-hidden="true" />
          Razonamiento del agente
        </p>
        <p className="mt-1.5 text-[13px] leading-relaxed text-foreground">
          {accion.razonamiento}
        </p>
        {accion.fuentes_consultadas.length > 0 && (
          <div className="mt-2.5 flex flex-wrap items-center gap-1.5">
            <span className="text-[11px] font-medium text-muted-foreground">
              Fuentes consultadas:
            </span>
            {accion.fuentes_consultadas.map((fuente) => (
              <CitationChip key={fuente} cita={fuente} />
            ))}
          </div>
        )}
      </div>

      {/* Borrador editable: el humano puede corregir antes de aprobar */}
      <div className="mt-4 space-y-3">
        <div>
          <label
            htmlFor={`asunto-${accion.id}`}
            className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-muted-foreground"
          >
            Asunto
          </label>
          <Input
            id={`asunto-${accion.id}`}
            value={asunto}
            onChange={(e) => setAsunto(e.target.value)}
            disabled={camposDeshabilitados}
          />
        </div>
        <div>
          <label
            htmlFor={`cuerpo-${accion.id}`}
            className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-muted-foreground"
          >
            Cuerpo del mensaje · {accion.borrador.canal}
          </label>
          <Textarea
            id={`cuerpo-${accion.id}`}
            rows={7}
            value={cuerpo}
            onChange={(e) => setCuerpo(e.target.value)}
            disabled={camposDeshabilitados}
            className="resize-none text-[13px] leading-relaxed"
          />
        </div>
        {editado && !camposDeshabilitados && (
          <p className="flex items-center gap-1.5 text-[11px] font-medium text-futuro-corp dark:text-futuro-sky">
            <Edit3 className="size-3" aria-hidden="true" />
            Borrador modificado — quedará registrado como “editado por humano”.
          </p>
        )}
      </div>

      {yaResuelta ? (
        /* ---- Acción ya decidida: se muestra la resolución, sin re-decidir ---- */
        accion.estado === 'rechazada' ? (
          <div className="mt-4 flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50 p-4">
            <RotateCcw className="mt-0.5 size-5 shrink-0 text-amber-600" aria-hidden="true" />
            <div>
              <p className="text-sm font-bold text-amber-900">Propuesta rechazada</p>
              <p className="mt-1 text-[13px] leading-relaxed text-amber-800">
                El lead volvió a nutrición — no se descarta.
                {accion.motivo_rechazo ? ` Motivo: “${accion.motivo_rechazo}”.` : ''} La
                decisión quedó registrada en la bitácora.
              </p>
            </div>
          </div>
        ) : (
          <div className="mt-4 flex items-start gap-3 rounded-xl border border-emerald-200 bg-emerald-50 p-4">
            <CheckCircle2 className="mt-0.5 size-5 shrink-0 text-emerald-600" aria-hidden="true" />
            <div>
              <p className="text-sm font-bold text-emerald-900">
                {accion.editado_por_humano
                  ? 'Borrador editado y aprobado'
                  : 'Comunicación aprobada'}
              </p>
              <p className="mt-1 text-[13px] leading-relaxed text-emerald-800">
                Envío simulado{accion.destinatario?.email ? ` a ${accion.destinatario.email}` : ''}.
                {accion.revisado_por ? ` Aprobada por ${accion.revisado_por}.` : ''} La
                decisión quedó sellada en la bitácora
                {accion.editado_por_humano ? ' con la marca de edición humana.' : '.'}
              </p>
            </div>
          </div>
        )
      ) : bloqueado ? (
        /* ---- PLANO ESTRELLA: consentimiento por finalidad ---- */
        <div className="mt-4 space-y-3">
          <div
            role="alert"
            id={idBloqueo}
            className="flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-4"
          >
            <ShieldAlert className="mt-0.5 size-5 shrink-0 text-red-600" aria-hidden="true" />
            <div>
              <h4 className="text-sm font-bold uppercase tracking-wide text-red-800">
                Aprobación bloqueada
              </h4>
              <p className="mt-1 text-[13px] leading-relaxed text-red-700">
                {lead.identidad.nombre.split(' ')[0]} no ha consentido comunicaciones
                comerciales. No se puede enviar ninguna comunicación por este canal.
              </p>
            </div>
          </div>

          <p className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
            Alternativas disponibles
          </p>
          <div className="grid gap-2 sm:grid-cols-3">
            <Button variant="outline" size="sm" onClick={() => canalAlternativo('Teléfono')}>
              <Phone aria-hidden="true" /> Contactar por teléfono
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => canalAlternativo('Material educativo')}
            >
              <BookOpen aria-hidden="true" /> Solo material educativo
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => canalAlternativo('Consentimiento vía chat')}
            >
              <MessageSquare aria-hidden="true" /> Pedir consentimiento
            </Button>
          </div>

          <Button
            disabled
            aria-describedby={idBloqueo}
            title="El backend también rechaza este envío (403): ocultar un botón no es seguridad"
            className="w-full"
          >
            <Lock aria-hidden="true" /> Aprobar envío — bloqueado
          </Button>
          <p className="text-center text-[11px] leading-snug text-muted-foreground">
            Un lead sin consentimiento comercial no es basura: es un prospecto válido
            con restricción de canal.
          </p>
        </div>
      ) : (
        /* ---- Flujo normal: aprobar / editar y aprobar / rechazar ---- */
        <div className="mt-4">
          {mostrarRechazo ? (
            <div className="space-y-2 rounded-lg border border-border bg-muted/50 p-3">
              <label
                htmlFor={`motivo-${accion.id}`}
                className="block text-[11px] font-bold uppercase tracking-wider text-muted-foreground"
              >
                Motivo del rechazo — el lead vuelve a nutrición
              </label>
              <Input
                id={`motivo-${accion.id}`}
                autoFocus
                placeholder="Ej. El cliente prefiere esperar al próximo trimestre"
                value={motivoRechazo}
                onChange={(e) => setMotivoRechazo(e.target.value)}
              />
              <div className="flex justify-end gap-2 pt-1">
                <Button variant="ghost" size="sm" onClick={() => setMostrarRechazo(false)}>
                  Cancelar
                </Button>
                <Button
                  size="sm"
                  disabled={!motivoRechazo.trim()}
                  onClick={rechazar}
                  className="bg-red-600 text-white hover:bg-red-700"
                >
                  Confirmar rechazo
                </Button>
              </div>
            </div>
          ) : (
            <div className="flex flex-col-reverse gap-2 sm:flex-row sm:items-center sm:justify-end">
              <Button
                variant="ghost"
                onClick={() => setMostrarRechazo(true)}
                disabled={esObsoleta || enviando}
                className="text-destructive hover:bg-destructive/10 hover:text-destructive"
              >
                <X aria-hidden="true" /> Rechazar
              </Button>
              {/* Un solo botón primario que se adapta: si el borrador cambió,
                  es "Editar y aprobar"; si no, "Aprobar envío". Se acabó la
                  confusión de dos botones que se activaban/desactivaban. */}
              <Button
                onClick={aprobar}
                disabled={esObsoleta || enviando}
                className="min-w-[9.5rem]"
              >
                {enviando ? (
                  <Loader2 className="animate-spin" aria-hidden="true" />
                ) : editado ? (
                  <Edit3 aria-hidden="true" />
                ) : (
                  <ShieldCheck aria-hidden="true" />
                )}
                {enviando
                  ? 'Enviando…'
                  : editado
                    ? 'Editar y aprobar'
                    : 'Aprobar envío'}
              </Button>
            </div>
          )}
        </div>
      )}
    </section>
  );
}
