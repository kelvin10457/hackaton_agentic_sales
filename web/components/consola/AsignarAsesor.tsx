'use client';

import { useEffect, useState } from 'react';
import { CalendarClock, Check, UserCheck, UserPlus, X } from 'lucide-react';

import { Button } from '@/components/shared/button';
import { Input } from '@/components/shared/input';
import { useToast } from '@/components/shared/toast';

interface Asignacion {
  asesor: string;
  fecha: string;
  hora: string;
  medio: string;
}

/**
 * Asignar asesor + agenda a un lead que autorizó ser contactado por un asesor.
 *
 * DEMO: la asignación se registra en la interfaz (no se persiste en el backend).
 * Es coherente con el resto de acciones simuladas de la consola; enchufar un
 * endpoint real sería añadir una tabla, sin cambiar esta UI.
 */
export default function AsignarAsesor({
  leadId,
  nombreLead,
}: {
  leadId: string;
  nombreLead: string;
}) {
  const [abierto, setAbierto] = useState(false);
  const [asignacion, setAsignacion] = useState<Asignacion | null>(null);
  const [asesor, setAsesor] = useState('');
  const [fecha, setFecha] = useState('');
  const [hora, setHora] = useState('');
  const [medio, setMedio] = useState('');
  const { toast } = useToast();

  // Al cambiar de lead, se limpia todo (master–detail comparte el componente).
  useEffect(() => {
    setAbierto(false);
    setAsignacion(null);
    setAsesor('');
    setFecha('');
    setHora('');
    setMedio('');
  }, [leadId]);

  const completo = asesor.trim() && fecha && hora && medio.trim();

  function confirmar() {
    if (!completo) return;
    setAsignacion({ asesor: asesor.trim(), fecha, hora, medio: medio.trim() });
    setAbierto(false);
    toast({
      tipo: 'success',
      titulo: 'Asesor asignado',
      descripcion: `${asesor.trim()} contactará a ${nombreLead.split(' ')[0]} el ${fecha} a las ${hora} vía ${medio.trim()}.`,
    });
  }

  // ── Ya asignado: se muestra la ficha y se permite reasignar ────────────────
  if (asignacion) {
    return (
      <section className="rounded-xl border border-emerald-200 bg-emerald-50 p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex items-start gap-3">
            <UserCheck className="mt-0.5 size-5 shrink-0 text-emerald-600" aria-hidden="true" />
            <div>
              <p className="text-sm font-bold text-emerald-900">Asesor asignado</p>
              <p className="mt-1 text-[13px] leading-relaxed text-emerald-800">
                <strong className="font-semibold">{asignacion.asesor}</strong> contactará a{' '}
                {nombreLead.split(' ')[0]} el <strong className="font-semibold">{asignacion.fecha}</strong> a
                las <strong className="font-semibold">{asignacion.hora}</strong> vía{' '}
                <strong className="font-semibold">{asignacion.medio}</strong>.
              </p>
            </div>
          </div>
          <Button
            variant="ghost"
            size="sm"
            onClick={() => setAbierto(true)}
            className="shrink-0 text-emerald-800 hover:bg-emerald-100"
          >
            Reasignar
          </Button>
        </div>
      </section>
    );
  }

  return (
    <section className="rounded-xl border border-border bg-card p-5 shadow-sm">
      <h3 className="mb-1 flex items-center gap-2 text-xs font-bold uppercase tracking-widest text-muted-foreground">
        <CalendarClock className="size-4" aria-hidden="true" />
        Asignación de asesor
      </h3>

      {!abierto ? (
        <>
          <p className="mb-3 text-[13px] leading-relaxed text-muted-foreground">
            {nombreLead.split(' ')[0]} autorizó el contacto de un asesor. Asigna quién,
            cuándo y por qué medio le dará seguimiento.
          </p>
          <Button onClick={() => setAbierto(true)}>
            <UserPlus aria-hidden="true" /> Asignar asesor
          </Button>
        </>
      ) : (
        <div className="mt-2 space-y-3">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <label htmlFor={`asesor-${leadId}`} className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Nombre del asesor
              </label>
              <Input
                id={`asesor-${leadId}`}
                autoFocus
                placeholder="Ej. Carlos Peña"
                value={asesor}
                onChange={(e) => setAsesor(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor={`medio-${leadId}`} className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Medio de contacto
              </label>
              <Input
                id={`medio-${leadId}`}
                placeholder="Ej. Llamada, WhatsApp, Correo…"
                value={medio}
                onChange={(e) => setMedio(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor={`fecha-${leadId}`} className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Fecha
              </label>
              <Input
                id={`fecha-${leadId}`}
                type="date"
                value={fecha}
                onChange={(e) => setFecha(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor={`hora-${leadId}`} className="mb-1 block text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                Hora
              </label>
              <Input
                id={`hora-${leadId}`}
                type="time"
                value={hora}
                onChange={(e) => setHora(e.target.value)}
              />
            </div>
          </div>
          <div className="flex justify-end gap-2 pt-1">
            <Button variant="ghost" size="sm" onClick={() => setAbierto(false)}>
              <X aria-hidden="true" /> Cancelar
            </Button>
            <Button size="sm" disabled={!completo} onClick={confirmar}>
              <Check aria-hidden="true" /> Confirmar asignación
            </Button>
          </div>
        </div>
      )}
    </section>
  );
}
