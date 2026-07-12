'use client';

import React, { useState, useEffect } from 'react';
import { mockLeads } from '@/lib/mocks-consola';
import PipelineTable from '@/components/consola/PipelineTable';
import LeadDetailPanel from '@/components/consola/LeadDetailPanel';
import { PipelineSkeleton, DetailPanelSkeleton } from '@/components/consola/Skeletons';
import MiniDashboard from '@/components/consola/MiniDashboard';



export default function ConsolaPage() {
    // Estado para controlar qué lead está seleccionado actualmente
    const [selectedLead, setSelectedLead] = useState<any | null>(null);

    const [estaCargando, setEstaCargando] = useState(true);

    // 2. Simula el tiempo de respuesta del servidor (1.5 segundos)
    useEffect(() => {
        const timer = setTimeout(() => {
            setEstaCargando(false);
        }, 1000);
        return () => clearTimeout(timer);
    }, []);


    return (
        <div className="flex h-screen bg-gray-50">

            {/* 
        Menú Lateral (Placeholder súper básico para dar contexto visual) 
        R3 (Chat/Shared) probablemente te pasará el layout final después.
      */}
            <aside className="w-16 bg-futuro-base flex flex-col items-center py-6 border-r border-futuro-corp shadow-lg z-20">
                <div className="w-8 h-8 bg-futuro-accent rounded-lg flex items-center justify-center text-white font-bold mb-8 shadow-sm">
                    F
                </div>
                <div className="w-8 h-8 bg-white/10 rounded-lg border border-white/20 mb-4 cursor-pointer hover:bg-white/20 transition-colors"></div>

                <div className="w-8 h-8 bg-white/5 rounded-lg border border-white/10 cursor-pointer hover:bg-white/20 transition-colors"></div>
            </aside>
            {/* Contenedor Principal (Master-Detail) */}
            <main className="flex-1 flex overflow-hidden">

                {/* Panel Izquierdo: El Pipeline (Master) - 35% del ancho */}
                <div className="w-1/3 min-w-[380px] max-w-[450px] flex-shrink-0 bg-white z-10 shadow-[4px_0_12px_rgba(0,0,0,0.03)] flex flex-col">
                    {estaCargando ? (
                        <PipelineSkeleton />
                    ) : (
                        <>
                            {/* Aquí inyectamos el Mini Dashboard */}
                            <MiniDashboard leads={mockLeads as any} />

                            {/* Contenedor con scroll solo para la tabla */}
                            <div className="flex-1 overflow-y-auto">
                                <PipelineTable
                                    leads={mockLeads as any}
                                    selectedLeadId={selectedLead?.id || null}
                                    onSelectLead={(lead) => setSelectedLead(lead)}
                                />
                            </div>
                        </>
                    )}
                </div>

                {/* Panel Derecho: Ficha del Lead (Detail) - 65% del ancho */}
                <div className="flex-1 bg-gray-50 overflow-hidden relative">
                    {estaCargando ? (
                        <DetailPanelSkeleton />
                    ) : (
                        <LeadDetailPanel lead={selectedLead} />
                    )}
                </div>

            </main>
        </div>
    );
}