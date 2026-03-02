import React, { forwardRef } from 'react';
import clsx from 'clsx';
import { Check } from 'lucide-react';

export interface CheckboxProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type' | 'size'> {
  label?: string;
  error?: string;
  helperText?: string;
  checkboxSize?: 'sm' | 'md' | 'lg';
}

const Checkbox = forwardRef<HTMLInputElement, CheckboxProps>(({
  label,
  name,
  error,
  helperText,
  checkboxSize = 'md',
  disabled = false,
  className = '',
  ...props
}, ref) => {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-5 w-5',
    lg: 'h-6 w-6',
  };

  const checkboxClasses = clsx(
    'peer appearance-none border-2 rounded transition-all duration-200 cursor-pointer',
    'focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-amber-500',
    'checked:bg-amber-500 checked:border-amber-500',
    'disabled:bg-gray-100 disabled:cursor-not-allowed disabled:border-gray-300',
    error 
      ? 'border-red-500' 
      : 'border-gray-300',
    sizeClasses[checkboxSize],
    className
  );

  const iconSizeClasses = {
    sm: 'h-3 w-3',
    md: 'h-4 w-4',
    lg: 'h-5 w-5',
  };

  return (
    <div className="w-full">
      <div className="flex items-start gap-2">
        <div className="relative flex items-center">
          <input
            ref={ref}
            type="checkbox"
            id={name}
            name={name}
            disabled={disabled}
            className={checkboxClasses}
            aria-invalid={error ? 'true' : 'false'}
            aria-describedby={error ? `${name}-error` : helperText ? `${name}-helper` : undefined}
            {...props}
          />
          <Check 
            className={clsx(
              'absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 text-white pointer-events-none opacity-0 peer-checked:opacity-100 transition-opacity',
              iconSizeClasses[checkboxSize]
            )}
            strokeWidth={3}
          />
        </div>
        {label && (
          <label 
            htmlFor={name} 
            className={clsx(
              'text-sm font-medium cursor-pointer select-none',
              disabled ? 'text-gray-400' : 'text-gray-700'
            )}
          >
            {label}
          </label>
        )}
      </div>
      {error && (
        <p id={`${name}-error`} className="mt-1.5 ml-7 text-sm text-red-600 flex items-center gap-1">
          <svg className="h-4 w-4" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
          </svg>
          {error}
        </p>
      )}
      {helperText && !error && (
        <p id={`${name}-helper`} className="mt-1.5 ml-7 text-sm text-gray-500">{helperText}</p>
      )}
    </div>
  );
});

Checkbox.displayName = 'Checkbox';

export default Checkbox;
