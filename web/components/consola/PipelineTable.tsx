'use client';

import React, { useMemo, useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  type SortingState,
} from '@tanstack/react-table';
import { ArrowUpDown, Search, SearchX } from 'lucide-react';

import { Input } from '@/components/shared/input';
import { etiqueta } from '@/lib/format';
import { cn } from '@/lib/utils';
import type { Banda, Lead } from '@/lib/types';

interface PipelineTableProps {
  leads: Lead[];
  selectedLeadId: string | null;
  onSelectLead: (lead: Lead) => void;
}

const DOT: Record<Banda, string> = {
  caliente: 'bg-banda-caliente',
  tibio: 'bg-banda-tibio',
  frio: 'bg-banda-frio',
};

const FILTROS: { valor: Banda | 'todas'; texto: string }[] = [
  { valor: 'todas', texto: 'Todas' },
  { valor: 'caliente', texto: 'Caliente' },
  { valor: 'tibio', texto: 'Tibio' },
  { valor: 'frio', texto: 'Frío' },
];

const columnHelper = createColumnHelper<Lead>();

export default function PipelineTable({
  leads,
  selectedLeadId,
  onSelectLead,
}: PipelineTableProps) {
  const [banda, setBanda] = useState<Banda | 'todas'>('todas');
  const [busqueda, setBusqueda] = useState('');
  const [sorting, setSorting] = useState<SortingState>([{ id: 'score', desc: true }]);

  const filtrados = useMemo(() => {
    const q = busqueda.trim().toLowerCase();
    return leads.filter(
      (l) =>
        (banda === 'todas' || l.score?.banda === banda) &&
        (q === '' || l.identidad.nombre.toLowerCase().includes(q))
    );
  }, [leads, banda, busqueda]);

  const conteos = useMemo(
    () => ({
      todas: leads.length,
      caliente: leads.filter((l) => l.score?.banda === 'caliente').length,
      tibio: leads.filter((l) => l.score?.banda === 'tibio').length,
      frio: leads.filter((l) => l.score?.banda === 'frio').length,
    }),
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
          <h2 className="flex items-center gap-2 text-sm font-bold text-futuro-base">
            Pipeline de leads
            <span className="rounded-full bg-muted px-2 py-0.5 text-[11px] font-semibold tabular-nums text-muted-foreground">
              {filtrados.length}
            </span>
          </h2>
          <div className="relative w-36 sm:w-44">
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
              }}
              className="mt-1 text-xs font-semibold text-futuro-corp underline-offset-2 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            >
              Limpiar filtros
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
