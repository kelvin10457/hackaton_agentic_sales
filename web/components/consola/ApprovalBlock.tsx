'use client';

import React, { useState, useEffect } from 'react';
import { ShieldCheck, AlertTriangle, Phone, BookOpen, X, Edit3 } from 'lucide-react';

interface ApprovalBlockProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  lead: any;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onActionComplete?: (type: 'aprobar' | 'editar_aprobar' | 'rechazar', data: any) => void;
}

export default function ApprovalBlock({ lead, onActionComplete }: ApprovalBlockProps) {
  // Simulación de una acción propuesta vinculada al lead (según Sección 5 del manual)
  const accion = lead?.accion_propuesta || {
    id: "acc_001",
    tipo: "agendar_reunion",
    razonamiento: `Score ${lead?.score?.total || 0} (${lead?.score?.banda || 'frio'}). Requiere contacto para profundizar en su perfil de riesgo y resolver dudas normativas.`,
    fuentes_consultadas: ["FA-063 §2", "FA-009 §1"],
    borrador: {
      asunto: `Asesoría Personalizada - Futuro Academy`,
      cuerpo: `Hola ${lead?.identidad?.nombre || 'Prospecto'},\n\nHe revisado tu interés en nuestros programas de formación financiera. Basado en tu perfil, te sugiero agendar una breve sesión de 15 minutos para estructurar tu ruta de aprendizaje de forma segura.\n\nSaludos cordiales,\nCarlos Peña`
    },
    estado: "pendiente"
  };

  // Estados locales para permitir la edición del borrador
  const [asunto, setAsunto] = useState(accion.borrador.asunto);
  const [cuerpo, setCuerpo] = useState(accion.borrador.cuerpo);
  const [motivoRechazo, setMotivoRechazo] = useState('');
  const [mostrarRechazo, setMostrarRechazo] = useState(false);

  // Sincronizar el borrador cuando cambie el lead en el panel master-detail
  /* eslint-disable react-hooks/exhaustive-deps */
  useEffect(() => {
    setAsunto(accion.borrador.asunto);
    setCuerpo(accion.borrador.cuerpo);
    setMostrarRechazo(false);
    setMotivoRechazo('');
  }, [lead]);
  /* eslint-enable react-hooks/exhaustive-deps */

  if (!lead) return null;

  // Verificación estricta del consentimiento comercial (Sección 6.4)
  const tieneConsentimientoComercial = lead.consentimiento?.comunicaciones_comerciales?.otorgado ?? true;
  
  // Simulación de propuesta obsoleta (Regla 8: si el score es bajo o cambió de estado)
  const esObsoleta = lead.etapa_embudo === 'Terminado'; 

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 font-sans">
      <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">
        Acción Sugerida por el Agente
      </h3>

      {/* Alerta de Propuesta Obsoleta */}
      {esObsoleta && (
        <div className="mb-4 p-3 bg-amber-50 border border-amber-200 text-amber-800 text-xs rounded-lg flex items-center gap-2">
          <AlertTriangle className="w-4 h-4 flex-shrink-0" />
          <span><strong>Propuesta obsoleta:</strong> Los datos del lead cambiaron desde que se generó este borrador.</span>
        </div>
      )}

      {/* Razonamiento y Fuentes Consultadas (Sección 6.4) */}
      <div className="mb-4 text-sm text-gray-600 bg-gray-50 p-4 rounded-lg border border-gray-100">
        <p className="font-semibold text-gray-700 text-xs uppercase tracking-wider mb-1">Razonamiento de IA</p>
        <p className="italic mb-3">&quot;{accion.razonamiento}&quot;</p>
        <div className="flex flex-wrap gap-2 items-center text-xs text-gray-500">
          <span className="font-medium">Fuentes auditadas:</span>
          {accion.fuentes_consultadas.map((fuente: string, idx: number) => (
            <span key={idx} className="bg-blue-50 text-futuro-corp px-2 py-0.5 rounded border border-blue-100 font-mono text-[11px]">
              {fuente}
            </span>
          ))}
        </div>
      </div>

      {/* Formulario Editable del Borrador (Sección 6.4) */}
      <div className="space-y-3 mb-6">
        <div>
          <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Asunto de la Comunicación</label>
          <input 
            type="text" 
            value={asunto} 
            onChange={(e) => setAsunto(e.target.value)}
            disabled={!tieneConsentimientoComercial || esObsoleta}
            className="w-full text-sm border-gray-200 rounded-lg focus:ring-futuro-corp focus:border-futuro-corp disabled:bg-gray-50 disabled:text-gray-400"
          />
        </div>
        <div>
          <label className="block text-xs font-bold text-gray-400 uppercase mb-1">Cuerpo del Mensaje (Email)</label>
          <textarea 
            rows={5}
            value={cuerpo} 
            onChange={(e) => setCuerpo(e.target.value)}
            disabled={!tieneConsentimientoComercial || esObsoleta}
            className="w-full text-sm border-gray-200 rounded-lg font-mono text-xs focus:ring-futuro-corp focus:border-futuro-corp disabled:bg-gray-50 disabled:text-gray-400 resize-none"
          />
        </div>
      </div>

      {/* --- PLANO ESTRELLA: CONTROL DE CONSENTIMIENTO BLOQUEADO (Sección 6.4) --- */}
      {!tieneConsentimientoComercial ? (
        <div className="space-y-4">
          <div className="p-4 bg-red-50 border border-red-200 rounded-xl flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h4 className="text-sm font-bold text-red-800">⚠️ APROBACIÓN BLOQUEADA</h4>
              <p className="text-xs text-red-700 mt-1 leading-relaxed">
                Este lead no ha otorgado su consentimiento para comunicaciones comerciales. No se puede enviar ninguna comunicación directa por este canal.
              </p>
            </div>
          </div>
          
          {/* Alternativas habilitadas ante el bloqueo */}
          <div className="grid grid-cols-2 gap-2 pt-1">
            <button type="button" className="flex items-center justify-center gap-2 px-3 py-2 border border-gray-200 text-xs font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors">
              <Phone className="w-3.5 h-3.5 text-gray-500" /> Contactar por Teléfono
            </button>
            <button type="button" className="flex items-center justify-center gap-2 px-3 py-2 border border-gray-200 text-xs font-medium rounded-lg text-gray-700 bg-white hover:bg-gray-50 transition-colors">
              <BookOpen className="w-3.5 h-3.5 text-gray-500" /> Solo Material Educativo
            </button>
          </div>
          
          {/* Botón principal deshabilitado */}
          <button disabled className="w-full py-2.5 bg-gray-200 text-gray-400 text-sm font-medium rounded-lg cursor-not-allowed">
            Aprobación Inhabilitada
          </button>
        </div>
      ) : (
        /* --- FLUJO NORMAL DE ACCIONES --- */
        <div className="space-y-3">
          {mostrarRechazo ? (
            <div className="p-3 bg-gray-50 border border-gray-200 rounded-lg space-y-2">
              <label className="block text-xs font-bold text-gray-500 uppercase">Motivo del Rechazo (Vuelve a Nutrición)</label>
              <input 
                type="text" 
                placeholder="Ej. El cliente prefiere esperar al próximo trimestre" 
                value={motivoRechazo}
                onChange={(e) => setMotivoRechazo(e.target.value)}
                className="w-full text-xs border-gray-200 rounded p-1.5"
              />
              <div className="flex justify-end gap-2 text-xs pt-1">
                <button onClick={() => setMostrarRechazo(false)} className="px-2 py-1 text-gray-500 hover:text-gray-700">Cancelar</button>
                <button 
                  onClick={() => onActionComplete?.('rechazar', { motivo: motivoRechazo })}
                  disabled={!motivoRechazo.trim()}
                  className="px-2 py-1 bg-red-600 text-white rounded disabled:opacity-50"
                >
                  Confirmar Rechazo
                </button>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-2 justify-end">
              <button 
                onClick={() => setMostrarRechazo(true)}
                disabled={esObsoleta}
                className="px-3 py-2 border border-gray-200 rounded-lg text-xs font-medium text-red-600 hover:bg-red-50 transition-colors disabled:opacity-50"
              >
                <X className="w-3.5 h-3.5 inline mr-1" /> Rechazar
              </button>
              
              <button 
                onClick={() => onActionComplete?.('editar_aprobar', { asunto, cuerpo })}
                disabled={esObsoleta || asunto === accion.borrador.asunto && cuerpo === accion.borrador.cuerpo}
                className="px-3 py-2 border border-gray-200 rounded-lg text-xs font-medium text-gray-700 hover:bg-gray-50 transition-colors disabled:opacity-50"
              >
                <Edit3 className="w-3.5 h-3.5 inline mr-1" /> Editar y Aprobar
              </button>

              <button 
                onClick={() => onActionComplete?.('aprobar', { asunto, cuerpo })}
                disabled={esObsoleta}
                className="px-4 py-2 bg-futuro-corp hover:bg-futuro-base text-white text-xs font-medium rounded-lg shadow-sm transition-colors flex items-center gap-1.5 disabled:opacity-50"
              >
                <ShieldCheck className="w-4 h-4" /> Aprobar Envío
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
