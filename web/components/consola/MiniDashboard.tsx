'use client';

import React from 'react';
import { Users, Flame, Target } from 'lucide-react';

interface MiniDashboardProps {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  leads: any[];
}

export default function MiniDashboard({ leads }: MiniDashboardProps) {
  // Cálculos dinámicos basados en tus leads
  const totalLeads = leads?.length || 0;
  const leadsCalientes = leads?.filter(lead => lead.score >= 80).length || 0;
  const porcentajeCalientes = totalLeads > 0 ? Math.round((leadsCalientes / totalLeads) * 100) : 0;
  
  // Métrica simulada de impacto
  const tasaAprobacion = "92%";

  return (
    <div className="bg-white border-b border-gray-200 p-4">
      <h2 className="text-[10px] font-bold text-gray-400 uppercase tracking-widest mb-3">
        Rendimiento de Campaña
      </h2>
      
      <div className="grid grid-cols-3 gap-3">
        {/* Métrica 1: Volumen */}
        <div className="bg-gray-50 border border-gray-100 rounded-lg p-3 flex flex-col justify-center items-center text-center">
          <Users className="w-4 h-4 text-futuro-corp mb-1" />
          <span className="text-lg font-bold text-gray-800 leading-none">{totalLeads}</span>
          <span className="text-[10px] text-gray-500 mt-1 uppercase tracking-tight">Leads</span>
        </div>

        {/* Métrica 2: Calidad */}
        <div className="bg-red-50 border border-red-100 rounded-lg p-3 flex flex-col justify-center items-center text-center">
          <Flame className="w-4 h-4 text-red-500 mb-1" />
          <span className="text-lg font-bold text-red-600 leading-none">{porcentajeCalientes}%</span>
          <span className="text-[10px] text-red-500 mt-1 uppercase tracking-tight">Calientes</span>
        </div>

        {/* Métrica 3: Eficiencia (Aprobación) */}
        <div className="bg-green-50 border border-green-100 rounded-lg p-3 flex flex-col justify-center items-center text-center">
          <Target className="w-4 h-4 text-green-600 mb-1" />
          <span className="text-lg font-bold text-green-700 leading-none">{tasaAprobacion}</span>
          <span className="text-[10px] text-green-600 mt-1 uppercase tracking-tight">Aprobación</span>
        </div>
      </div>
    </div>
  );
}
