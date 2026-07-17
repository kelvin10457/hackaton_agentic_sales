'use client';

import React, { useEffect, useMemo, useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table';
import { ArrowUpDown, ChevronDown, Filter, Search, SearchX, X } from 'lucide-react';

import { Input } from '@/components/shared/input';
import { Checkbox } from '@/components/shared/checkbox';
import { etiqueta } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Banda, Lead } from '@/lib/types';

interface PipelineTableProps {
  leads: Lead[];
  selectedLeadId: string | null;
  onSelectLead: (lead: Lead) => void;
}

// Una fila puede traer cualquier banda del enum del backend, así que DOT las
// cubre todas. El motor solo emite 3 (Biblia §5.5); "critico" se pinta como
// caliente para que nunca quede una fila sin color.
const DOT: Record<Banda, string> = {
  caliente: 'bg-banda-caliente',
  critico: 'bg-banda-caliente',
  tibio: 'bg-banda-tibio',
  frio: 'bg-banda-frio',
};

// Los chips de filtro solo ofrecen las 3 bandas reales.
type FiltroBanda = 'todas' | 'caliente' | 'tibio' | 'frio';

const FILTROS: { valor: FiltroBanda; texto: string }[] = [
  { valor: 'todas', texto: 'Todas' },
  { valor: 'caliente', texto: 'Caliente' },
  { valor: 'tibio', texto: 'Tibio' },
  { valor: 'frio', texto: 'Frío' },
];

// Atributos del filtro avanzado (icono junto a la búsqueda).
// Las 8 etapas cerradas de la Biblia (schemas.EtapaEmbudo) y los 2 tipos.
const ETAPAS: string[] = [
  'nuevo',
  'en_calificacion',
  'calificado',
  'educando',
  'listo_para_asesor',
  'derivado',
  'nutricion',
  'descartado',
];
const TIPOS: string[] = ['B2C', 'B2B'];

const columnHelper = createColumnHelper<Lead>();

export default function PipelineTable({
  leads,
  selectedLeadId,
  onSelectLead,
}: PipelineTableProps) {
  const [banda, setBanda] = useState<FiltroBanda>('todas');
  const [busqueda, setBusqueda] = useState('');
  const [sorting, setSorting] = useState<SortingState>([{ id: 'score', desc: true }]);

  // Filtro avanzado por atributos (etapa / tipo).
  const [filtroAbierto, setFiltroAbierto] = useState(false);
  const [secEtapa, setSecEtapa] = useState(true);
  const [secTipo, setSecTipo] = useState(false);
  const [etapasSel, setEtapasSel] = useState<Set<string>>(new Set());
  const [tiposSel, setTiposSel] = useState<Set<string>>(new Set());
  const atributosActivos = etapasSel.size + tiposSel.size;

  const toggleEn = (setter: React.Dispatch<React.SetStateAction<Set<string>>>) => (v: string) =>
    setter((prev) => {
      const n = new Set(prev);
      if (n.has(v)) n.delete(v);
      else n.add(v);
      return n;
    });
  const toggleEtapa = toggleEn(setEtapasSel);
  const toggleTipo = toggleEn(setTiposSel);
  const limpiarAtributos = () => {
    setEtapasSel(new Set());
    setTiposSel(new Set());
  };

  // Cerrar el popover con Escape.
  useEffect(() => {
    if (!filtroAbierto) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setFiltroAbierto(false);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [filtroAbierto]);

  // "critico" cuenta como caliente: son la misma acción para Carlos (llamar hoy).
  const esBanda = (l: Lead, b: Exclude<FiltroBanda, 'todas'>) =>
    b === 'caliente'
      ? l.score?.banda === 'caliente' || l.score?.banda === 'critico'
      : l.score?.banda === b;

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return leads.filter(
      (l) =>
        (banda === 'todas' || esBanda(l, banda)) &&
        (q === '' || l.identidad.nombre.toLowerCase().includes(q)) &&
        (etapasSel.size === 0 || etapasSel.has(l.etapa_embudo)) &&
        (tiposSel.size === 0 || tiposSel.has(l.tipo))
    );
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [leads, banda, busqueda, etapasSel, tiposSel]);

  const conteos: Record<FiltroBanda, number> = useMemo(
    () => ({
      todas: leads.length,
      caliente: leads.filter((l) => esBanda(l, 'caliente')).length,
      tibio: leads.filter((l) => esBanda(l, 'tibio')).length,
      frio: leads.filter((l) => esBanda(l, 'frio')).length,
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [leads]
  );

  const columns = useMemo(
    () => [
      columnHelper.accessor((l) => l.identidad.nombre, {
        id: 'prospecto',
        header: 'Prospecto',
        enableSorting: false,
        cell: (info) => (
          <span className="block max-w-[150px] truncate font-medium text-foreground">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor('tipo', {
        id: 'tipo',
        header: 'Tipo',
        enableSorting: false,
        cell: (info) => (
          <span className="rounded border border-border bg-muted px-1.5 py-0.5 text-[10px] font-bold uppercase tracking-wider text-muted-foreground">
            {info.getValue()}
          </span>
        ),
      }),
      columnHelper.accessor((l) => l.score?.total ?? 0, {
        id: 'score',
        header: 'Score',
        cell: (info) => {
          const bandaLead = info.row.original.score?.banda ?? 'frio';
          return (
            <span className="flex items-center justify-end gap-2">
              <span className="text-sm font-bold tabular-nums text-foreground">
                {info.getValue()}
              </span>
              <span
                className={cn('size-2 shrink-0 rounded-full', DOT[bandaLead])}
                aria-hidden="true"
              />
              <span className="sr-only">banda {etiqueta(bandaLead)}</span>
            </span>
          );
        },
      }),
      columnHelper.accessor('etapa_embudo', {
        id: 'etapa',
        header: 'Etapa',
        enableSorting: false,
        cell: (info) => (
          <span className="text-xs text-muted-foreground">{etiqueta(info.getValue())}</span>
        ),
      }),
    ],
    []
  );

  const table = useReactTable({
    data: filtrados,
    columns,
    state: { sorting },
    onSortingChange: setSorting,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
  });

  const filas = table.getRowModel().rows;

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-card">
      {/* Controles: título, búsqueda y filtro por banda */}
      <div className="flex shrink-0 flex-col gap-2.5 border-b border-border p-3.5">
        <div className="flex items-center justify-between gap-2">
          <h2 className="flex items-center gap-2 text-sm font-bold text-foreground">
            Pipeline de leads
            <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-semibold tabular-nums text-muted-foreground">
              {filtrados.length}
            </span>
          </h2>
          <div className="flex items-center gap-2">
            <div className="relative w-32 sm:w-40">
              <Search
                className="pointer-events-none absolute left-2.5 top-1/2 size-3.5 -translate-y-1/2 text-muted-foreground"
                aria-hidden="true"
              />
              <Input
                value={busqueda}
                onChange={(e) => setBusqueda(e.target.value)}
                placeholder="Buscar…"
                aria-label="Buscar prospecto por nombre"
                className="h-8 pl-8 text-[13px]"
              />
            </div>

            {/* Filtro avanzado por atributos (etapa / tipo) */}
            <div className="relative">
              <button
                type="button"
                onClick={() => setFiltroAbierto((v) => !v)}
                aria-label="Filtrar por etapa o tipo"
                aria-expanded={filtroAbierto}
                title="Filtrar por etapa o tipo"
                className={cn(
                  'relative flex size-8 shrink-0 items-center justify-center rounded-lg border transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
                  filtroAbierto || atributosActivos > 0
                    ? 'border-futuro-base bg-futuro-base text-white'
                    : 'border-border bg-card text-muted-foreground hover:border-futuro-base/40 hover:text-foreground'
                )}
              >
                <Filter className="size-4" aria-hidden="true" />
                {atributosActivos > 0 && (
                  <span className="absolute -right-1 -top-1 flex size-4 items-center justify-center rounded-full bg-futuro-accent text-[9px] font-bold tabular-nums text-white ring-2 ring-card">
                    {atributosActivos}
                  </span>
                )}
              </button>

              {filtroAbierto && (
                <>
                  {/* Cierre al hacer clic fuera */}
                  <div
                    className="fixed inset-0 z-20"
                    aria-hidden="true"
                    onClick={() => setFiltroAbierto(false)}
                  />
                  <div
                    role="dialog"
                    aria-label="Filtrar pipeline por etapa o tipo"
                    className="absolute right-0 top-full z-30 mt-2 w-64 overflow-hidden rounded-xl border border-border bg-card shadow-xl"
                  >
                    {/* Cabecera con botón de cierre */}
                    <div className="flex items-center justify-between border-b border-border px-3 py-2">
                      <span className="text-[11px] font-bold uppercase tracking-wider text-muted-foreground">
                        Filtrar por
                      </span>
                      <button
                        type="button"
                        onClick={() => setFiltroAbierto(false)}
                        aria-label="Cerrar filtros"
                        className="flex size-6 items-center justify-center rounded-full text-muted-foreground transition-colors duration-150 hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <X className="size-4" aria-hidden="true" />
                      </button>
                    </div>

                    {/* Atributo: Etapa */}
                    <div className="border-b border-border">
                      <button
                        type="button"
                        onClick={() => setSecEtapa((v) => !v)}
                        aria-expanded={secEtapa}
                        className="flex w-full items-center justify-between px-3 py-2 text-left text-[13px] font-semibold text-foreground transition-colors duration-150 hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <span className="flex items-center gap-1.5">
                          Etapa
                          {etapasSel.size > 0 && (
                            <span className="rounded-full bg-futuro-accent/15 px-1.5 text-[10px] font-bold tabular-nums text-futuro-corp dark:text-futuro-sky">
                              {etapasSel.size}
                            </span>
                          )}
                        </span>
                        <ChevronDown
                          className={cn(
                            'size-4 text-muted-foreground transition-transform duration-150',
                            secEtapa && 'rotate-180'
                          )}
                          aria-hidden="true"
                        />
                      </button>
                      {secEtapa && (
                        <div className="max-h-52 space-y-0.5 overflow-y-auto px-2 pb-2">
                          {ETAPAS.map((v) => (
                            <label
                              key={v}
                              className="flex cursor-pointer items-center gap-2 rounded-md px-1.5 py-1 text-[13px] text-foreground transition-colors duration-150 hover:bg-accent/60"
                            >
                              <Checkbox
                                checked={etapasSel.has(v)}
                                onCheckedChange={() => toggleEtapa(v)}
                              />
                              {etiqueta(v)}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Atributo: Tipo */}
                    <div className="border-b border-border">
                      <button
                        type="button"
                        onClick={() => setSecTipo((v) => !v)}
                        aria-expanded={secTipo}
                        className="flex w-full items-center justify-between px-3 py-2 text-left text-[13px] font-semibold text-foreground transition-colors duration-150 hover:bg-accent/50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        <span className="flex items-center gap-1.5">
                          Tipo
                          {tiposSel.size > 0 && (
                            <span className="rounded-full bg-futuro-accent/15 px-1.5 text-[10px] font-bold tabular-nums text-futuro-corp dark:text-futuro-sky">
                              {tiposSel.size}
                            </span>
                          )}
                        </span>
                        <ChevronDown
                          className={cn(
                            'size-4 text-muted-foreground transition-transform duration-150',
                            secTipo && 'rotate-180'
                          )}
                          aria-hidden="true"
                        />
                      </button>
                      {secTipo && (
                        <div className="space-y-0.5 px-2 pb-2">
                          {TIPOS.map((v) => (
                            <label
                              key={v}
                              className="flex cursor-pointer items-center gap-2 rounded-md px-1.5 py-1 text-[13px] text-foreground transition-colors duration-150 hover:bg-accent/60"
                            >
                              <Checkbox
                                checked={tiposSel.has(v)}
                                onCheckedChange={() => toggleTipo(v)}
                              />
                              {v}
                            </label>
                          ))}
                        </div>
                      )}
                    </div>

                    {/* Pie: resultados + limpiar */}
                    <div className="flex items-center justify-between px-3 py-2">
                      <span className="text-[11px] tabular-nums text-muted-foreground">
                        {filtrados.length} resultado{filtrados.length === 1 ? '' : 's'}
                      </span>
                      <button
                        type="button"
                        onClick={limpiarAtributos}
                        disabled={atributosActivos === 0}
                        className="text-[11px] font-semibold text-futuro-corp dark:text-futuro-sky underline-offset-2 transition-opacity hover:underline disabled:opacity-40 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      >
                        Limpiar
                      </button>
                    </div>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>

        <div
          role="group"
          aria-label="Filtrar pipeline por banda"
          className="flex flex-wrap items-center gap-1.5"
        >
          {FILTROS.map((f) => (
            <button
              key={f.valor}
              type="button"
              onClick={() => setBanda(f.valor)}
              aria-pressed={banda === f.valor}
              className={cn(
                'flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[11px] font-semibold transition-colors duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1',
                banda === f.valor
                  ? 'border-futuro-base bg-futuro-base text-white'
                  : 'border-border bg-card text-muted-foreground hover:border-futuro-base/40 hover:text-foreground'
              )}
            >
              {f.valor !== 'todas' && (
                <span
                  className={cn('size-1.5 rounded-full', DOT[f.valor as Banda])}
                  aria-hidden="true"
                />
              )}
              {f.texto}
              <span className="tabular-nums opacity-70">{conteos[f.valor]}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Tabla de alta densidad: filas de 44 px, números tabulares */}
      <div className="scrollbar-thin min-h-0 flex-1 overflow-auto">
        <table className="w-full border-collapse text-left">
          <thead className="sticky top-0 z-10 bg-card">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-border">
                {headerGroup.headers.map((header) => {
                  const orden = header.column.getIsSorted();
                  return (
                    <th
                      key={header.id}
                      scope="col"
                      aria-sort={
                        orden === 'asc'
                          ? 'ascending'
                          : orden === 'desc'
                            ? 'descending'
                            : undefined
                      }
                      className={cn(
                        'bg-card px-3 py-2 text-[10px] font-bold uppercase tracking-wider text-muted-foreground',
                        header.column.id === 'score' && 'text-right'
                      )}
                    >
                      {header.column.getCanSort() ? (
                        <button
                          type="button"
                          onClick={header.column.getToggleSortingHandler()}
                          className="ml-auto flex items-center gap-1 uppercase tracking-wider transition-colors duration-150 hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                          title="Ordenar por score"
                        >
                          {flexRender(header.column.columnDef.header, header.getContext())}
                          <ArrowUpDown className="size-3" aria-hidden="true" />
                        </button>
                      ) : (
                        flexRender(header.column.columnDef.header, header.getContext())
                      )}
                    </th>
                  );
                })}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-border/60">
            {filas.map((row) => {
              const seleccionado = selectedLeadId === row.original.id;
              return (
                <tr
                  key={row.id}
                  tabIndex={0}
                  aria-selected={seleccionado}
                  onClick={() => onSelectLead(row.original)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onSelectLead(row.original);
                    }
                  }}
                  className={cn(
                    'h-11 cursor-pointer border-l-2 transition-colors duration-150 focus-visible:bg-accent/70 focus-visible:outline-none',
                    seleccionado
                      ? 'border-l-futuro-accent bg-accent/70'
                      : 'border-l-transparent hover:bg-accent/40'
                  )}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td
                      key={cell.id}
                      className={cn(
                        'whitespace-nowrap px-3 text-sm',
                        cell.column.id === 'score' && 'text-right'
                      )}
                    >
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
          </tbody>
        </table>

        {filas.length === 0 && (
          <div className="flex flex-col items-center gap-2 p-10 text-center">
            <SearchX className="size-8 text-muted-foreground/50" aria-hidden="true" />
            <p className="text-sm font-semibold text-foreground">Sin resultados</p>
            <p className="text-xs text-muted-foreground">
              Ningún lead coincide con el filtro actual.
            </p>
            <button
              type="button"
              onClick={() => {
                setBanda('todas');
                setBusqueda('');
                limpiarAtributos();
              }}
              className="mt-1 text-xs font-semibold text-futuro-corp dark:text-futuro-sky underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Limpiar filtros
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
