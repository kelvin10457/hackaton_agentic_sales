'use client';

import React from 'react';
import { Skeleton } from '@/components/shared/skeleton';

/** Esqueleto del panel izquierdo: KPIs + filtros + filas del pipeline */
export function PipelineSkeleton() {
  return (
    <div className="flex h-full flex-col" aria-hidden="true">
      <div className="border-b border-border p-3.5">
        <Skeleton className="h-3 w-40" />
        <div className="mt-3 grid grid-cols-3 gap-2.5">
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
          <Skeleton className="h-20 rounded-xl" />
        </div>
        <Skeleton className="mt-3 h-1.5 w-full rounded-full" />
      </div>

      <div className="border-b border-border p-3.5">
        <div className="flex items-center justify-between gap-2">
          <Skeleton className="h-5 w-32" />
          <Skeleton className="h-8 w-40 rounded-lg" />
        </div>
        <div className="mt-2.5 flex gap-1.5">
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-20 rounded-full" />
          <Skeleton className="h-6 w-16 rounded-full" />
          <Skeleton className="h-6 w-14 rounded-full" />
        </div>
      </div>

      <div className="flex-1 space-y-0 overflow-hidden px-3.5 py-2">
        {Array.from({ length: 10 }).map((_, i) => (
          <div key={i} className="flex h-11 items-center gap-4 border-b border-border/50">
            <Skeleton className="h-3.5 w-2/5" />
            <Skeleton className="h-3.5 w-10" />
            <Skeleton className="ml-auto h-3.5 w-12" />
            <Skeleton className="h-3.5 w-16" />
          </div>
        ))}
      </div>
    </div>
  );
}

/** Esqueleto del panel derecho: cabecera + score + brief + acción */
export function DetailPanelSkeleton() {
  return (
    <div className="flex h-full flex-col bg-background" aria-hidden="true">
      <div className="border-b border-border bg-card px-6 py-4">
        <div className="flex items-start gap-3">
          <Skeleton className="size-11 rounded-xl" />
          <div className="flex-1">
            <Skeleton className="h-6 w-1/3" />
            <Skeleton className="mt-2 h-3.5 w-1/2" />
          </div>
          <Skeleton className="h-6 w-28 rounded-full" />
        </div>
      </div>

      <div className="space-y-4 p-6">
        <div className="rounded-xl border border-border bg-card p-5">
          <Skeleton className="h-3 w-28" />
          <Skeleton className="mt-3 h-9 w-24" />
          <div className="mt-5 space-y-4">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i}>
                <div className="mb-1.5 flex justify-between">
                  <Skeleton className="h-3 w-20" />
                  <Skeleton className="h-3 w-10" />
                </div>
                <Skeleton className="h-2 w-full rounded-full" />
              </div>
            ))}
          </div>
          <Skeleton className="mt-5 h-16 w-full rounded-lg" />
        </div>

        <div className="rounded-xl border border-border bg-card p-5">
          <Skeleton className="h-3 w-32" />
          <Skeleton className="mt-3 h-14 w-full rounded-lg" />
          <div className="mt-4 grid grid-cols-3 gap-4">
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
            <Skeleton className="h-10" />
          </div>
        </div>

        <div className="rounded-xl border border-border bg-card p-5">
          <Skeleton className="h-3 w-40" />
          <Skeleton className="mt-3 h-20 w-full rounded-lg" />
          <Skeleton className="mt-3 h-9 w-full rounded-lg" />
          <Skeleton className="mt-3 h-28 w-full rounded-lg" />
        </div>
      </div>
    </div>
  );
}
