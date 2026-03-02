import React from 'react';
import clsx from 'clsx';

export interface CardProps {
  children: React.ReactNode;
  title?: string;
  subtitle?: string;
  headerAction?: React.ReactNode;
  footer?: React.ReactNode;
  variant?: 'default' | 'bordered' | 'elevated';
  padding?: 'none' | 'sm' | 'md' | 'lg';
  hoverable?: boolean;
  clickable?: boolean;
  onClick?: () => void;
  className?: string;
}

const Card: React.FC<CardProps> = ({
  children,
  title,
  subtitle,
  headerAction,
  footer,
  variant = 'default',
  padding = 'md',
  hoverable = false,
  clickable = false,
  onClick,
  className = '',
}) => {
  const baseClasses = 'bg-white rounded-lg transition-all duration-200';

  const variantClasses = {
    default: 'border border-gray-200',
    bordered: 'border-2 border-gray-300',
    elevated: 'shadow-lg border border-gray-100',
  };

  const paddingClasses = {
    none: '',
    sm: 'p-3',
    md: 'p-4',
    lg: 'p-6',
  };

  const interactiveClasses = clsx(
    hoverable && 'hover:shadow-md hover:border-gray-300',
    clickable && 'cursor-pointer active:scale-[0.99]'
  );

  const hasHeader = title || subtitle || headerAction;

  return (
    <div
      className={clsx(
        baseClasses,
        variantClasses[variant],
        paddingClasses[padding],
        interactiveClasses,
        className
      )}
      onClick={clickable ? onClick : undefined}
    >
      {hasHeader && (
        <div className={clsx(
          'flex items-start justify-between gap-4',
          padding !== 'none' && 'mb-4'
        )}>
          <div className="flex-1">
            {title && (
              <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
            )}
            {subtitle && (
              <p className="text-sm text-gray-500 mt-1">{subtitle}</p>
            )}
          </div>
          {headerAction && (
            <div className="flex-shrink-0">{headerAction}</div>
          )}
        </div>
      )}

      <div>{children}</div>

      {footer && (
        <div className={clsx(
          'border-t border-gray-200',
          padding !== 'none' && 'mt-4 pt-4'
        )}>
          {footer}
        </div>
      )}
    </div>
  );
};

export default Card;
