import React from 'react';
import { Search, X } from 'lucide-react';
import clsx from 'clsx';

export interface SearchBarProps extends Omit<React.InputHTMLAttributes<HTMLInputElement>, 'type'> {
  onSearch?: (value: string) => void;
  onClear?: () => void;
  isLoading?: boolean;
  searchSize?: 'sm' | 'md' | 'lg';
}

const SearchBar: React.FC<SearchBarProps> = ({
  onSearch,
  onClear,
  isLoading = false,
  searchSize = 'md',
  value,
  onChange,
  placeholder = 'Buscar...',
  className = '',
  ...props
}) => {
  const [localValue, setLocalValue] = React.useState(value || '');

  React.useEffect(() => {
    setLocalValue(value || '');
  }, [value]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setLocalValue(newValue);
    onChange?.(e);
    
    // Búsqueda en tiempo real
    if (onSearch) {
      onSearch(newValue);
    }
  };

  const handleClear = () => {
    setLocalValue('');
    onClear?.();
    if (onSearch) {
      onSearch('');
    }
  };

  const sizeClasses = {
    sm: 'h-9 px-9 text-sm',
    md: 'h-10 px-10 text-base',
    lg: 'h-12 px-11 text-lg',
  };

  const iconSizes = {
    sm: 16,
    md: 18,
    lg: 20,
  };

  return (
    <div className={clsx('relative', className)}>
      <Search 
        className={clsx(
          'absolute left-3 top-1/2 -translate-y-1/2 text-gray-400',
          isLoading && 'animate-pulse'
        )}
        size={iconSizes[searchSize]}
      />
      <input
        type="search"
        value={localValue}
        onChange={handleChange}
        placeholder={placeholder}
        className={clsx(
          'w-full border border-gray-300 rounded-lg transition-all duration-200',
          'focus:outline-none focus:ring-2 focus:ring-amber-500 focus:border-amber-500',
          'placeholder:text-gray-400',
          sizeClasses[searchSize]
        )}
        {...props}
      />
      {localValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600 transition-colors"
        >
          <X size={iconSizes[searchSize]} />
        </button>
      )}
    </div>
  );
};

export default SearchBar;
