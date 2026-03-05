import React from 'react';
import clsx from 'clsx';

interface SkeletonProps {
  className?: string;
  rows?: number;
  cols?: number;
}

/** Bloque de una línea con pulso */
export const SkeletonLine: React.FC<{ className?: string }> = ({ className }) => (
  <div className={clsx('animate-pulse rounded bg-gray-200', className)} />
);

/** Skeleton completo para una tabla (filas × columnas) */
const Skeleton: React.FC<SkeletonProps> = ({ rows = 5, cols = 4, className }) => (
  <div className={clsx('space-y-1', className)}>
    {/* Header */}
    <div className="grid gap-4 rounded-lg bg-gray-50 px-4 py-3" style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}>
      {Array.from({ length: cols }).map((_, i) => (
        <SkeletonLine key={i} className="h-3 w-3/4" />
      ))}
    </div>
    {/* Filas */}
    {Array.from({ length: rows }).map((_, r) => (
      <div
        key={r}
        className="grid gap-4 border-b border-gray-100 px-4 py-4"
        style={{ gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))` }}
      >
        {Array.from({ length: cols }).map((_, c) => (
          <SkeletonLine key={c} className={clsx('h-4', c === 0 ? 'w-full' : 'w-2/3')} />
        ))}
      </div>
    ))}
  </div>
);

/** Skeleton para tarjetas KPI (4 en fila) */
export const SkeletonKPI: React.FC = () => (
  <div className="animate-pulse rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
    <div className="flex items-center justify-between">
      <div className="space-y-3 flex-1">
        <SkeletonLine className="h-3 w-1/2" />
        <SkeletonLine className="h-7 w-3/4" />
        <SkeletonLine className="h-3 w-1/3" />
      </div>
      <div className="h-12 w-12 rounded-full bg-gray-200" />
    </div>
    <div className="mt-4 border-t border-gray-100 pt-3">
      <SkeletonLine className="h-3 w-1/2" />
    </div>
  </div>
);

export default Skeleton;
