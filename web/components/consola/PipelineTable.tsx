'use client';

import React, { useState } from 'react';
import {
  createColumnHelper,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { Filter } from 'lucide-react';

interface Lead {
  id: string;
  tipo: string;
  identidad: { nombre: string };
  score: { total: number; banda: string };
  etapa_embudo: string;
}

interface PipelineTableProps {
  leads: Lead[];
  selectedLeadId: string | null;
  onSelectLead: (lead: Lead) => void;
}

const columnHelper = createColumnHelper<Lead>();

export default function PipelineTable({ leads, selectedLeadId, onSelectLead }: PipelineTableProps) {
  const [bandaFilter, setBandaFilter] = useState<string>('todas');

  const columns = [
    columnHelper.accessor('identidad.nombre', {
      header: 'Prospecto',
      cell: (info) => <span className="font-medium text-gray-900">{info.getValue()}</span>,
    }),
    columnHelper.accessor('tipo', {
      header: 'Tipo',
      cell: (info) => (
        <span className="text-[10px] px-1.5 py-0.5 bg-gray-100 text-gray-600 rounded uppercase tracking-wider font-bold">
          {info.getValue()}
        </span>
      ),
    }),
    columnHelper.accessor('score.total', {
      header: 'Score',
      cell: (info) => {
        const score = info.getValue();
        const banda = info.row.original.score.banda;
        const dotColor = 
          banda === 'caliente' ? 'bg-red-500' : 
          banda === 'tibio' ? 'bg-amber-400' : 'bg-blue-500';

        return (
          <div className="flex items-center gap-2">
            <span className="text-sm font-bold tabular-nums text-gray-700">{score}</span>
            <span className={`w-2 h-2 rounded-full ${dotColor}`}></span>
          </div>
        );
      },
      // Ordenamiento por defecto
      sortingFn: 'basic',
    }),
    columnHelper.accessor('etapa_embudo', {
      header: 'Etapa',
      cell: (info) => <span className="text-xs text-gray-500 truncate">{info.getValue() || 'Nutrición'}</span>,
    }),
  ];

  const table = useReactTable({
    data: leads,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    initialState: {
      sorting: [{ id: 'score_total', desc: true }], // Ordenar por score descendente por defecto
    },
    state: {
      globalFilter: bandaFilter !== 'todas' ? bandaFilter : undefined,
    },
    onGlobalFilterChange: setBandaFilter,
    globalFilterFn: (row, columnId, filterValue) => {
      if (filterValue === 'todas') return true;
      return row.original.score.banda === filterValue;
    },
  });

  return (
    <div className="flex flex-col h-full bg-white font-sans border-r border-gray-200">
      {/* Controles de la Tabla */}
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50/50">
        <h2 className="text-sm font-bold text-futuro-base flex items-center gap-2">
          Pipeline de Leads <span className="bg-gray-200 text-gray-600 px-2 py-0.5 rounded-full text-xs">{leads.length}</span>
        </h2>
        
        {/* Filtro por Banda */}
        <div className="flex items-center gap-2 text-xs">
          <Filter className="w-3.5 h-3.5 text-gray-400" />
          <select 
            className="border-gray-200 rounded-md text-xs py-1 pl-2 pr-6 bg-white focus:ring-futuro-corp focus:border-futuro-corp"
            value={bandaFilter}
            onChange={(e) => setBandaFilter(e.target.value)}
          >
            <option value="todas">Todas las bandas</option>
            <option value="caliente"> Caliente (70-100)</option>
            <option value="tibio"> Tibio (40-69)</option>
            <option value="frio"> Frío (0-39)</option>
          </select>
        </div>
      </div>

      {/* Tabla (Alta Densidad - Filas de 44px) */}
      <div className="overflow-auto flex-1">
        <table className="w-full text-left border-collapse">
          <thead className="bg-gray-50 sticky top-0 z-10 border-b border-gray-200">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th key={header.id} className="px-4 py-2 text-xs font-bold text-gray-500 uppercase tracking-wider">
                    {flexRender(header.column.columnDef.header, header.getContext())}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody className="divide-y divide-gray-100">
            {table.getRowModel().rows.map((row) => (
              <tr 
                key={row.id}
                onClick={() => onSelectLead(row.original)}
                className={`h-[44px] cursor-pointer transition-colors duration-150 ease-in-out hover:bg-blue-50/50 ${
                  selectedLeadId === row.original.id ? 'bg-blue-50 border-l-2 border-l-futuro-accent' : 'border-l-2 border-l-transparent'
                }`}
              >
                {row.getVisibleCells().map((cell) => (
                  <td key={cell.id} className="px-4 whitespace-nowrap text-sm">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
        
        {table.getRowModel().rows.length === 0 && (
          <div className="p-8 text-center text-sm text-gray-500 italic">
            No hay leads que coincidan con el filtro.
          </div>
        )}
      </div>
    </div>
  );
}
