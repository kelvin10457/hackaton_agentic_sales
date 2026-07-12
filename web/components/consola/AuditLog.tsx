'use client';

import React from 'react';
import { Clock, Bot, User, ShieldAlert, CheckCircle2 } from 'lucide-react';

interface AuditLogProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  lead: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  accionSimulada?: { tipo: string, data: any } | null; // Nueva prop
}

interface LogEntry {
  hora: string;
  fechaAbsoluta: string;
  tiempoRelativo: string;
  actor: 'agente' | 'guardrail' | 'usuario' | 'ejecutivo';
  nombreActor: string;
  evento: string;
  metadato?: string;
  esHumano?: boolean;
}

export default function AuditLog({ lead, accionSimulada }: AuditLogProps) {
  if (!lead) return null;

  // Datos simulados de la bitácora según el caso específico (Sección 6.5)
  // Si es María Villacis (lead_001 o similar), cargamos la traza exacta exigida por el manual.
  const esMaria = lead.identidad.nombre.includes('María') || lead.id === 'lead_001';
  
  const bitacoraMock: LogEntry[] = esMaria ? [
    {
      hora: "22:58",
      fechaAbsoluta: "11 jul 2026, 22:58",
      tiempoRelativo: "hace 14 min",
      actor: "agente",
      nombreActor: "Agente IA",
      evento: "Propuso acción: agendar reunión",
      metadato: "Fuentes: FA-003 §2, FA-009 §1"
    },
    {
      hora: "22:54",
      fechaAbsoluta: "11 jul 2026, 22:54",
      tiempoRelativo: "hace 18 min",
      actor: "usuario",
      nombreActor: "María Villacis",
      evento: "Otorgó consentimiento (Tratamiento de datos y Comunicaciones comerciales)"
    },
    {
      hora: "22:53",
      fechaAbsoluta: "11 jul 2026, 22:53",
      tiempoRelativo: "hace 19 min",
      actor: "agente",
      nombreActor: "Agente IA",
      evento: "Score recalculado automáticamente: 88",
      metadato: "Banda: CALIENTE"
    },
    {
      hora: "22:51",
      fechaAbsoluta: "11 jul 2026, 22:51",
      tiempoRelativo: "hace 21 min",
      actor: "guardrail",
      nombreActor: "Guardrail Financiero",
      evento: "Activación de Negativa Honesta",
      metadato: "Consulta bloqueada: 'bitcoin'"
    },
    {
      hora: "22:49",
      fechaAbsoluta: "11 jul 2026, 22:49",
      tiempoRelativo: "hace 23 min",
      actor: "guardrail",
      nombreActor: "Guardrail de Asesoría",
      evento: "Bloqueo de recomendación directa (No-asesoramiento)",
      metadato: "Consulta mitigada: 'en qué invierto'"
    }
  ] : [
    // Caso de Sofía u otros leads
    {
      hora: "17:15",
      fechaAbsoluta: "11 jul 2026, 17:15",
      tiempoRelativo: "hace 1 h",
      actor: "usuario",
      nombreActor: lead.identidad.nombre,
      evento: "Negó consentimiento para comunicaciones comerciales (Solo canales informativos/quiz)"
    },
    {
      hora: "17:12",
      fechaAbsoluta: "11 jul 2026, 17:12",
      tiempoRelativo: "hace 1 h",
      actor: "agente",
      nombreActor: "Agente IA",
      evento: "Score recalculado automáticamente: 72",
      metadato: "Banda: CALIENTE"
    }
  ];
  const timelineActual = [...bitacoraMock];
  if (accionSimulada) {
    const esEdicion = accionSimulada.tipo === 'editar_aprobar';
    const esRechazo = accionSimulada.tipo === 'rechazar';
    
    // Obtenemos la hora actual del navegador (Ecuador)
    const horaActual = new Date().toLocaleTimeString('es-EC', { hour: '2-digit', minute: '2-digit' });

    timelineActual.unshift({
      hora: horaActual,
      fechaAbsoluta: `Hoy, ${horaActual}`,
      tiempoRelativo: "hace un momento",
      actor: "ejecutivo",
      nombreActor: "Carlos Peña", // El usuario logueado en consola
      evento: esRechazo 
        ? "Rechazó la propuesta y devolvió el lead a nutrición"
        : esEdicion 
          ? "EDITÓ el borrador y APROBÓ el envío" 
          : "APROBÓ la comunicación propuesta sin cambios",
      metadato: accionSimulada.data?.motivo ? `Motivo: ${accionSimulada.data.motivo}` : undefined,
      esHumano: true // Flag clave de la Sección 6.5
    });
  }

return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 font-sans">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-6 flex items-center gap-2">
        <Clock className="w-4 h-4 text-gray-400" /> Bitácora de Auditoría Completa
      </h3>

      <div className="relative border-l border-gray-200 ml-3 pl-6 space-y-6">
        
        {timelineActual.map((log, index) => {
          let Icon = Bot;
          let iconBg = 'bg-blue-50 text-blue-600 border-blue-100';

          if (log.actor === 'guardrail') {
            Icon = ShieldAlert;
            iconBg = 'bg-red-50 text-red-600 border-red-100';
          } else if (log.actor === 'usuario') {
            Icon = User;
            iconBg = 'bg-gray-100 text-gray-600 border-gray-200';
          } else if (log.actor === 'ejecutivo') {
            // Estilo destacado para la acción humana final
            Icon = CheckCircle2;
            iconBg = 'bg-green-500 text-white border-green-600 shadow-md transform scale-110';
          }

          return (
            <div key={index} className="relative group">
              <span className={`absolute -left-[37px] top-0.5 w-6 h-6 rounded-full border flex items-center justify-center shadow-sm z-10 transition-all ${iconBg}`}>
                <Icon className="w-3 h-3" />
              </span>

              {/* Si es una acción del ejecutivo, le damos un fondo especial sutil */}
              <div className={`flex flex-col sm:flex-row sm:items-start justify-between gap-1 p-2 -mt-2 rounded-lg ${log.esHumano ? 'bg-green-50/50 border border-green-100' : 'bg-transparent'}`}>
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-gray-800">{log.nombreActor}</span>
                    <span className={`text-[11px] px-1.5 py-0.2 rounded font-mono uppercase tracking-tight ${log.esHumano ? 'bg-green-100 text-green-700 font-bold' : 'bg-gray-50 text-gray-400'}`}>
                      {log.actor}
                    </span>
                  </div>
                  <p className={`text-sm mt-0.5 leading-relaxed ${log.esHumano ? 'text-green-800 font-medium' : 'text-gray-600'}`}>
                    {log.evento}
                  </p>
                  
                  {log.metadato && (
                    <p className="text-xs font-mono text-futuro-corp mt-1 bg-white px-2 py-1 rounded inline-block border border-gray-200">
                      {log.metadato}
                    </p>
                  )}
                </div>

                <div className="text-right flex-shrink-0" title={log.fechaAbsoluta}>
                  <span className="text-xs font-mono text-gray-400 block sm:inline">{log.hora}</span>
                  <span className="text-[10px] text-gray-400 block sm:mt-0.5 italic">({log.tiempoRelativo})</span>
                </div>
              </div>
            </div>
          );
        })}
        
        {/* 
          Línea Base Inicial: Origen de la sesión 
        */}
        <div className="relative">
          <span className="absolute -left-[33px] top-1 w-4 h-4 rounded-full border border-gray-200 bg-gray-50 z-10"></span>
          <p className="text-xs font-medium text-gray-400 italic pl-1">Sesión iniciada en canal público</p>
        </div>

      </div>
    </div>
  );
}
