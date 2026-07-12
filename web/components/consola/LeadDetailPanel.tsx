import React, { useState, useEffect } from 'react';
import ScorePanel from './ScorePanel';
import BriefPanel from './BriefPanel';
import AuditLog from './AuditLog';
import ApprovalBlock from './ApprovalBlock';
import { User, Mail, FileText, Briefcase } from 'lucide-react';


// Interfaz adaptada a los datos de tu mock
interface LeadDetailProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  lead: any | null; // Tipado genérico temporal hasta que R2 te pase los esquemas exactos
}

export default function LeadDetailPanel({ lead }: LeadDetailProps) {
  // Regla 6: Estado vacío (Empty State) si no hay un lead seleccionado
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const [accionSimulada, setAccionSimulada] = useState<{ tipo: string, data: any } | null>(null);
    useEffect(() => {
    setAccionSimulada(null);
    }, [lead]);

  if (!lead) {
    return (
      <div className="h-full flex flex-col items-center justify-center bg-gray-50/50 text-gray-400 p-8 text-center border-l border-gray-200">
        <Briefcase className="w-12 h-12 mb-4 text-gray-300" strokeWidth={1.5} />
        <h3 className="text-lg font-medium text-gray-500 mb-1">Ningún lead seleccionado</h3>
        <p className="text-sm">Haz clic en un prospecto del pipeline para ver su score, brief y proponer acciones.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full bg-gray-50 border-l border-gray-200 overflow-y-auto font-sans">
      
      {/* 1. Cabecera (Identidad del Lead) */}
      <div className="p-6 bg-white border-b border-gray-200 shadow-sm sticky top-0 z-10">
        <div className="flex justify-between items-start">
          <div>
            <h2 className="text-2xl font-bold text-futuro-base flex items-center gap-3">
              {lead.identidad.nombre}
              <span className="text-[10px] px-2 py-1 bg-gray-100 text-gray-600 rounded uppercase tracking-wider font-bold">
                {lead.tipo}
              </span>
            </h2>
            <div className="flex flex-col gap-1.5 mt-3 text-sm text-gray-500">
              <span className="flex items-center gap-2">
                <Mail className="w-4 h-4 text-gray-400" /> {lead.identidad.email}
              </span>
              {lead.identidad.documento && (
                <span className="flex items-center gap-2">
                  <FileText className="w-4 h-4 text-gray-400" /> CI {lead.identidad.documento}
                </span>
              )}
            </div>
          </div>
          {/* Etapa actual del embudo */}
          <div className="text-right">
            <p className="text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Etapa</p>
            <p className="text-sm font-semibold text-futuro-corp bg-blue-50/50 px-3 py-1 rounded-md border border-blue-100">
              {lead.etapa_embudo || 'En Evaluación'}
            </p>
          </div>
        </div>
      </div>

      {/* 2. Cuerpo Orquestador (Los 3 bloques críticos) */}
      <div className="p-6 space-y-6">
        
        {/* Bloque A: Score Dinámico (El que ya construiste) */}
        <ScorePanel score={lead.score} />

        {/* Bloque B: Brief */}
        <BriefPanel lead={lead} />
        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 opacity-70 border-dashed">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2 flex items-center gap-2">
            <User className="w-4 h-4" /> Brief del Lead
          </h3>
          <p className="text-sm text-gray-400 italic">
            (Aquí inyectaremos el componente BriefPanel con la necesidad, perfil y objeciones).
          </p>
        </div>

        {/* Bloque C: Acción Propuesta */}
        {accionSimulada && accionSimulada.tipo !== 'rechazar' ? (
          <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
             <p className="text-sm font-bold text-green-700">¡Acción registrada exitosamente!</p>
             <p className="text-xs text-green-600 mt-1">La decisión ha sido sellada en la bitácora de auditoría.</p>
          </div>
        ) : (
          <ApprovalBlock 
            lead={lead} 
            onActionComplete={(tipo, data) => setAccionSimulada({ tipo, data })} 
          />
        )}


        {/* Bloque D: Bitácora de Auditoría */}
        <AuditLog lead={lead} accionSimulada={accionSimulada} />

        <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 border-l-4 border-l-futuro-base opacity-70 border-dashed">
          <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-2">Acción Propuesta</h3>
          <p className="text-sm text-gray-400 italic">
            (Aquí inyectaremos el bloque con los botones de Aprobar/Rechazar y la lógica de bloqueo por consentimiento).
          </p>
        </div>

      </div>
    </div>
  );
}
