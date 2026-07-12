'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import {
    ArrowLeft,
    GraduationCap,
    LayoutDashboard,
    LogOut,
    Settings,
} from 'lucide-react';

import { mockLeads } from '@/lib/mocks-consola';
import type { Lead } from '@/lib/types';
import PipelineTable from '@/components/consola/PipelineTable';
import LeadDetailPanel from '@/components/consola/LeadDetailPanel';
import MiniDashboard from '@/components/consola/MiniDashboard';
import { PipelineSkeleton, DetailPanelSkeleton } from '@/components/consola/Skeletons';
import { ToastProvider } from '@/components/shared/toast';
import { LogoMark } from '@/components/shared/logo';
import { cn } from '@/lib/utils';

function NavIcon({
    activo,
    etiqueta,
    children,
}: {
    activo?: boolean;
    etiqueta: string;
    children: React.ReactNode;
}) {
    return (
        <button
            type="button"
            aria-label={etiqueta}
            title={etiqueta}
            aria-current={activo ? 'page' : undefined}
            className={cn(
                'relative flex size-9 items-center justify-center rounded-lg transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60 [&_svg]:size-[18px]',
                activo
                    ? 'bg-white/15 text-white'
                    : 'text-white/50 hover:bg-white/10 hover:text-white'
            )}
        >
            {activo && (
                <span
                    aria-hidden="true"
                    className="absolute -left-2.5 h-5 w-0.5 rounded-full bg-futuro-accent"
                />
            )}
            {children}
        </button>
    );
}

export default function ConsolaPage() {
    const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
    const [estaCargando, setEstaCargando] = useState(true);

    // Simula la latencia del servidor para exhibir los skeletons (regla 6)
    useEffect(() => {
        const timer = setTimeout(() => setEstaCargando(false), 800);
        return () => clearTimeout(timer);
    }, []);

    return (
        <ToastProvider>
            <div className="flex h-dvh overflow-hidden bg-background">
                {/* Rail de navegación (superficie interna con marca) */}
                <aside className="hidden w-14 shrink-0 flex-col items-center gap-1.5 bg-futuro-base py-4 md:flex">
                    <Link
                        href="/"
                        aria-label="Ir a la página principal"
                        className="mb-4 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                    >
                        <LogoMark claro />
                    </Link>
                    <nav aria-label="Secciones de la consola" className="flex flex-col gap-1.5">
                        <NavIcon activo etiqueta="Pipeline de leads">
                            <LayoutDashboard aria-hidden="true" />
                        </NavIcon>
                        <NavIcon etiqueta="Academia (próximamente)">
                            <GraduationCap aria-hidden="true" />
                        </NavIcon>
                        <NavIcon etiqueta="Configuración (próximamente)">
                            <Settings aria-hidden="true" />
                        </NavIcon>
                    </nav>
                    <Link
                        href="/"
                        aria-label="Salir de la consola"
                        title="Salir de la consola"
                        className="mt-auto flex size-9 items-center justify-center rounded-lg text-white/50 transition-colors duration-150 hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                    >
                        <LogOut className="size-[18px]" aria-hidden="true" />
                    </Link>
                </aside>

                <div className="flex min-w-0 flex-1 flex-col">
                    {/* Cabecera: identidad del ejecutivo (login stub) */}
                    <header className="flex h-14 shrink-0 items-center justify-between gap-3 border-b border-border bg-card px-4">
                        <div className="flex items-center gap-3">
                            <LogoMark className="md:hidden" />
                            <div>
                                <h1 className="text-sm font-bold leading-tight text-futuro-base">
                                    Consola del Ejecutivo
                                </h1>
                                <p className="hidden text-[11px] leading-tight text-muted-foreground sm:block">
                                    Ninguna comunicación sale sin aprobación humana
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-2.5">
                            <span className="hidden rounded-full border border-border bg-muted px-2.5 py-1 text-[11px] font-medium text-muted-foreground sm:inline-block">
                                Entorno demo
                            </span>
                            <div className="flex items-center gap-2.5 rounded-full border border-border py-1 pl-1 pr-3">
                                <span
                                    aria-hidden="true"
                                    className="flex size-7 items-center justify-center rounded-full bg-futuro-base text-[11px] font-bold text-white"
                                >
                                    CP
                                </span>
                                <div className="leading-tight">
                                    <p className="text-xs font-semibold text-foreground">Carlos Peña</p>
                                    <p className="text-[10px] text-muted-foreground">
                                        Ejecutivo comercial
                                    </p>
                                </div>
                            </div>
                        </div>
                    </header>

                    {/* Master–detail: el pipeline nunca pierde el contexto */}
                    <main className="flex min-h-0 flex-1">
                        <section
                            aria-label="Pipeline de leads"
                            className="flex w-full min-w-0 flex-col border-r border-border bg-card lg:w-[420px] lg:shrink-0 xl:w-[460px]"
                        >
                            {estaCargando ? (
                                <PipelineSkeleton />
                            ) : (
                                <>
                                    <MiniDashboard leads={mockLeads} />
                                    <PipelineTable
                                        leads={mockLeads}
                                        selectedLeadId={selectedLead?.id ?? null}
                                        onSelectLead={setSelectedLead}
                                    />
                                </>
                            )}
                        </section>

                        {/* Ficha (solo escritorio; en móvil se superpone) */}
                        <section
                            aria-label="Ficha del lead seleccionado"
                            className="hidden min-w-0 flex-1 lg:block"
                        >
                            {estaCargando ? (
                                <DetailPanelSkeleton />
                            ) : (
                                <LeadDetailPanel lead={selectedLead} />
                            )}
                        </section>
                    </main>
                </div>

                {/* Ficha en móvil/tablet: panel superpuesto con botón de volver */}
                {selectedLead && !estaCargando && (
                    <div className="fixed inset-0 z-40 flex animate-slide-in-right flex-col bg-background lg:hidden">
                        <div className="flex h-12 shrink-0 items-center gap-2 border-b border-border bg-card px-2">
                            <button
                                type="button"
                                onClick={() => setSelectedLead(null)}
                                className="flex items-center gap-1.5 rounded-lg px-2.5 py-1.5 text-sm font-medium text-muted-foreground transition-colors duration-150 hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                            >
                                <ArrowLeft className="size-4" aria-hidden="true" />
                                Pipeline
                            </button>
                            <span className="truncate text-sm font-semibold text-foreground">
                                {selectedLead.identidad.nombre}
                            </span>
                        </div>
                        <div className="min-h-0 flex-1">
                            <LeadDetailPanel lead={selectedLead} />
                        </div>
                    </div>
                )}
            </div>
        </ToastProvider>
    );
}
