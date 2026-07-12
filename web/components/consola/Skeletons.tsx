'use client';

import React from 'react';

// Esqueleto para el panel izquierdo (Pipeline de Leads)
export function PipelineSkeleton() {
  return (
    <div className="w-full animate-pulse p-4">
      {/* Cabecera simulada */}
      <div className="flex justify-between items-center mb-6">
        <div className="h-6 bg-gray-200 rounded w-1/3"></div>
        <div className="h-8 bg-gray-100 rounded w-24"></div>
      </div>
      
      {/* Cabecera de la tabla */}
      <div className="h-4 bg-gray-100 rounded w-full mb-4"></div>
      
      {/* Filas de la tabla simuladas */}
      <div className="space-y-4">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="flex gap-4 items-center p-3 border-b border-gray-50">
            <div className="h-4 bg-gray-200 rounded w-1/3"></div>
            <div className="h-4 bg-gray-100 rounded w-1/6"></div>
            <div className="h-4 bg-gray-200 rounded w-1/6"></div>
            <div className="h-4 bg-gray-100 rounded w-1/4"></div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Esqueleto para el panel derecho (Ficha del Lead)
export function DetailPanelSkeleton() {
  return (
    <div className="w-full animate-pulse p-6 space-y-6">
      {/* Título y estado simulados */}
      <div className="flex justify-between items-center mb-8 border-b border-gray-100 pb-4">
        <div className="h-8 bg-gray-200 rounded w-1/2"></div>
        <div className="h-6 bg-gray-100 rounded w-24"></div>
      </div>
      
      {/* Bloque A: Score simulado */}
      <div className="h-48 bg-gray-50 rounded-xl border border-gray-100 p-6 flex flex-col justify-between">
        <div className="h-5 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          <div className="h-2 bg-gray-200 rounded w-full"></div>
          <div className="h-2 bg-gray-200 rounded w-4/5"></div>
          <div className="h-2 bg-gray-200 rounded w-full"></div>
        </div>
      </div>

      {/* Bloque B: Brief simulado */}
      <div className="h-32 bg-gray-50 rounded-xl border border-gray-100 p-6">
         <div className="h-5 bg-gray-200 rounded w-1/3 mb-4"></div>
         <div className="h-3 bg-gray-200 rounded w-full mb-2"></div>
         <div className="h-3 bg-gray-200 rounded w-5/6"></div>
      </div>

      {/* Bloque C: Aprobación simulada */}
      <div className="h-40 bg-gray-50 rounded-xl border border-gray-100 p-6">
         <div className="h-5 bg-gray-200 rounded w-1/4 mb-4"></div>
         <div className="h-10 bg-gray-200 rounded w-full mb-2"></div>
         <div className="h-10 bg-gray-200 rounded w-full"></div>
      </div>
    </div>
  );
}
