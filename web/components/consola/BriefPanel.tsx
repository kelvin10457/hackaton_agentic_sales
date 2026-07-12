import React from 'react';
import { Target, AlertTriangle, Shield, MessageSquare, DollarSign } from 'lucide-react';

interface BriefProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  lead: any; // Mantenemos el tipado genérico hasta que R2 provea los esquemas
}

export default function BriefPanel({ lead }: BriefProps) {
  if (!lead) return null;

  return (
    <div className="bg-white border border-gray-200 rounded-xl shadow-sm p-6 font-sans">
      <h2 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4 flex items-center gap-2">
        <Target className="w-4 h-4" /> Resumen del Lead (Brief)
      </h2>

      <div className="space-y-4">
        
        {/* 1. Necesidad Extraída */}
        <div>
          <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1.5">
            <MessageSquare className="w-3.5 h-3.5" /> Necesidad
          </p>
          <p className="text-sm text-gray-700 bg-gray-50 p-3 rounded-md border border-gray-100 leading-relaxed">
            {lead.necesidad || 'No especificada por el modelo.'}
          </p>
        </div>

        {/* 2. Grid de Datos Duros (Perfil y Ruta) */}
        <div className="grid grid-cols-2 gap-4 py-2">
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1.5">
              <Shield className="w-3.5 h-3.5" /> Perfil de Riesgo
            </p>
            <p className="text-sm font-bold text-futuro-corp uppercase tracking-wide">
              {lead.senales?.perfil_riesgo || 'Desconocido'}
            </p>
          </div>
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1.5">
              <Target className="w-3.5 h-3.5" /> Ruta Sugerida
            </p>
            <p className="text-sm font-bold text-futuro-accent capitalize">
              {lead.ruta_sugerida ? lead.ruta_sugerida.replace('_', ' ') : 'Por definir'}
            </p>
          </div>
        </div>

        {/* 3. Monto (Aplicando Regla 1: Números tabulares) */}
        {lead.senales?.monto_declarado_usd && (
          <div>
            <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1.5">
              <DollarSign className="w-3.5 h-3.5" /> Monto Declarado
            </p>
            <p className="text-sm font-medium text-gray-800 tabular-nums">
              USD {lead.senales.monto_declarado_usd.toLocaleString('en-US')}
            </p>
          </div>
        )}

        {/* 4. Objeciones (Destacadas sutilmente) */}
        {lead.objeciones && (
          <div className="pt-2">
            <p className="text-xs font-semibold text-gray-500 mb-1 flex items-center gap-1.5">
              <AlertTriangle className="w-3.5 h-3.5 text-amber-500" /> Objeciones Identificadas
            </p>
            <p className="text-sm text-gray-700 bg-amber-50/30 p-3 rounded-md border border-amber-100/50 italic">
              &quot;{lead.objeciones}&quot;
            </p>
          </div>
        )}

      </div>
    </div>
  );
}
