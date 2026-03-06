/**
 * EmptyState - Componente reutilizable para estados vacíos
 * Diseño consistente en todo el sistema
 */

import React from 'react';
import { LucideIcon } from 'lucide-react';

export interface EmptyStateProps {
  icon?: LucideIcon;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
  };
  size?: 'sm' | 'md' | 'lg';
}

const EmptyState: React.FC<EmptyStateProps> = ({
  icon: Icon,
  title,
  description,
  action,
  size = 'md',
}) => {
  const sizes = {
    sm: { container: 'py-8', icon: 'h-10 w-10', title: 'text-base', desc: 'text-xs' },
    md: { container: 'py-12', icon: 'h-12 w-12', title: 'text-lg', desc: 'text-sm' },
    lg: { container: 'py-16', icon: 'h-16 w-16', title: 'text-xl', desc: 'text-base' },
  };

  const s = sizes[size];

  return (
    <div className={`flex flex-col items-center justify-center ${s.container} text-center`}>
      {Icon && (
        <div className="rounded-full bg-gray-100 p-4 mb-4">
          <Icon className={`${s.icon} text-gray-400`} />
        </div>
      )}
      <h3 className={`font-semibold text-gray-900 ${s.title}`}>{title}</h3>
      {description && (
        <p className={`mt-2 text-gray-500 max-w-sm ${s.desc}`}>{description}</p>
      )}
      {action && (
        <button
          onClick={action.onClick}
          className="mt-4 inline-flex items-center gap-2 rounded-lg bg-amber-500 px-4 py-2 text-sm font-medium text-white hover:bg-amber-600 transition-colors"
        >
          {action.label}
        </button>
      )}
    </div>
  );
};

export default EmptyState;
