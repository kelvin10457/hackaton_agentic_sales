'use client';

import React, { useCallback, useEffect, useState } from 'react';
import Link from 'next/link';
import {
    ArrowLeft,
    GraduationCap,
    LayoutDashboard,
    LogIn,
    LogOut,
    Settings,
} from 'lucide-react';

import {
    fetchLeadsEnriquecidos,
    registrarYLogin,
    isAuthenticated,
    clearToken,
} from '@/lib/consola-api';
import type { Lead } from '@/lib/types';
import PipelineTable from '@/components/consola/PipelineTable';
import LeadDetailPanel from '@/components/consola/LeadDetailPanel';
import MiniDashboard from '@/components/consola/MiniDashboard';
import { PipelineSkeleton, DetailPanelSkeleton } from '@/components/consola/Skeletons';
import { ToastProvider } from '@/components/shared/toast';
import { LogoMark } from '@/components/shared/logo';
import { cn } from '@/lib/utils';

// ── Login rápido (pantalla inline mientras no hay auth) ─────────────────────

function LoginForm({ onSuccess }: { onSuccess: () => void }) {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [cargando, setCargando] = useState(false);

    async function handleSubmit(e: React.FormEvent) {
        e.preventDefault();
        setError('');
        setCargando(true);
        try {
            await registrarYLogin("Ejecutivo", email, password);
            onSuccess();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Error al iniciar sesión');
        } finally {
            setCargando(false);
        }
    }

    return (
        <div className="flex h-dvh items-center justify-center bg-background p-6">
            <form
                onSubmit={handleSubmit}
                className="w-full max-w-sm space-y-4 rounded-2xl border border-border bg-card p-8 shadow-lg"
            >
                <div className="text-center">
                    <LogoMark className="mx-auto mb-3" />
                    <h1 className="text-lg font-bold text-futuro-base">
                        Consola del Ejecutivo
                    </h1>
                    <p className="mt-1 text-sm text-muted-foreground">
                        Inicia sesión para acceder al pipeline
                    </p>
                </div>

                <div>
                    <label htmlFor="email" className="mb-1 block text-xs font-bold uppercase tracking-wider text-muted-foreground">
                        Email
                    </label>
                    <input
                        id="email"
                        type="email"
                        required
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-futuro-accent"
                        placeholder="ejecutivo@futuro.ec"
                    />
                </div>

                <div>
                    <label htmlFor="password" className="mb-1 block text-xs font-bold uppercase tracking-wider text-muted-foreground">
                        Contraseña
                    </label>
                    <input
                        id="password"
                        type="password"
                        required
                        value={password}
                        onChange={(e) => setPassword(e.target.value)}
                        className="w-full rounded-lg border border-border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-futuro-accent"
                        placeholder="••••••••"
                    />
                </div>

                {error && (
                    <p className="rounded-lg bg-red-50 p-2 text-center text-xs font-semibold text-red-700">
                        {error}
                    </p>
                )}

                <button
                    type="submit"
                    disabled={cargando}
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-futuro-base px-4 py-2.5 text-sm font-bold text-white transition-colors hover:bg-futuro-base/90 disabled:opacity-50"
                >
                    <LogIn className="size-4" />
                    {cargando ? 'Entrando…' : 'Iniciar sesión'}
                </button>
            </form>
        </div>
    );
}

// ── NavIcon ──────────────────────────────────────────────────────────────────

function NavIcon({
    activo,
    etiqueta,
    href,
    children,
}: {
    activo?: boolean;
    etiqueta: string;
    href?: string;
    children: React.ReactNode;
}) {
    const Component = href ? Link : 'button';
    const props = href ? { href } : { type: 'button' as const };

    return (
        <Component
            {...props}
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
        </Component>
    );
}

// ── Página principal ────────────────────────────────────────────────────────

export default function ConsolaPage() {
    const [autenticado, setAutenticado] = useState(false);
    const [leads, setLeads] = useState<Lead[]>([]);
    const [selectedLead, setSelectedLead] = useState<Lead | null>(null);
    const [estaCargando, setEstaCargando] = useState(true);
    const [error, setError] = useState<string | null>(null);

    // Verificar si ya hay token al montar
    useEffect(() => {
        setAutenticado(isAuthenticated());
    }, []);

    // Cargar leads cuando estamos autenticados
    const cargarLeads = useCallback(async () => {
        setEstaCargando(true);
        setError(null);
        try {
            const data = await fetchLeadsEnriquecidos();
            setLeads(data);
        } catch (err) {
            const msg = err instanceof Error ? err.message : 'Error al cargar leads';
            setError(msg);
            // Si la sesión expiró, volver al login
            if (msg.includes('Sesión expirada')) {
                setAutenticado(false);
            }
        } finally {
            setEstaCargando(false);
        }
    }, []);

    useEffect(() => {
        if (autenticado) {
            cargarLeads();
        }
    }, [autenticado, cargarLeads]);

    // Pantalla de login si no hay token
    if (!autenticado) {
        return <LoginForm onSuccess={() => setAutenticado(true)} />;
    }

    return (
        <ToastProvider>
            <div className="flex min-h-screen bg-background">
                {/* Rail de navegación (superficie interna con marca) */}
                <aside className="sticky top-0 hidden h-screen w-14 shrink-0 flex-col items-center gap-1.5 bg-futuro-base py-4 md:flex">
                    <Link
                        href="/"
                        aria-label="Ir a la página principal"
                        className="mb-4 rounded-lg focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                    >
                        <LogoMark claro />
                    </Link>
                    <nav aria-label="Secciones de la consola" className="flex flex-col gap-1.5">
                        <NavIcon activo etiqueta="Pipeline de leads" href="/consola">
                            <LayoutDashboard aria-hidden="true" />
                        </NavIcon>
                        <NavIcon etiqueta="Academia (próximamente)" href="/chat">
                            <GraduationCap aria-hidden="true" />
                        </NavIcon>
                        <NavIcon etiqueta="Configuración (próximamente)" href="/consola">
                            <Settings aria-hidden="true" />
                        </NavIcon>
                    </nav>
                    <button
                        type="button"
                        onClick={() => {
                            clearToken();
                            setAutenticado(false);
                            setLeads([]);
                            setSelectedLead(null);
                        }}
                        aria-label="Cerrar sesión"
                        title="Cerrar sesión"
                        className="mt-auto flex size-9 items-center justify-center rounded-lg text-white/50 transition-colors duration-150 hover:bg-white/10 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-white/60"
                    >
                        <LogOut className="size-[18px]" aria-hidden="true" />
                    </button>
                </aside>

                <div className="flex min-w-0 flex-1 flex-col">
                    {/* Cabecera: identidad del ejecutivo */}
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
                                Conectado exitosamente
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
                            ) : error ? (
                                <div className="flex flex-col items-center justify-center gap-3 p-8 text-center">
                                    <p className="text-sm font-semibold text-red-600">{error}</p>
                                    <button
                                        type="button"
                                        onClick={cargarLeads}
                                        className="rounded-lg bg-futuro-base px-4 py-2 text-sm font-bold text-white hover:bg-futuro-base/90"
                                    >
                                        Reintentar
                                    </button>
                                </div>
                            ) : (
                                <>
                                    <MiniDashboard leads={leads} />
                                    <PipelineTable
                                        leads={leads}
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
