import { type ButtonHTMLAttributes, type ReactNode } from 'react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  block?: boolean
  icon?: ReactNode
}

const variants = {
  primary: 'bg-green-600 text-white hover:bg-green-700 disabled:bg-green-300',
  secondary: 'bg-gray-100 text-gray-800 hover:bg-gray-200 disabled:bg-gray-100 disabled:text-gray-400 border border-gray-300',
  danger: 'bg-red-600 text-white hover:bg-red-700 disabled:bg-red-300',
  ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 disabled:text-gray-300',
}

const sizes = {
  sm: 'text-xs px-2 py-1 gap-1',
  md: 'text-sm px-3 py-2 gap-1.5',
  lg: 'text-base px-4 py-2.5 gap-2',
}

export default function Button({
  variant = 'secondary',
  size = 'md',
  loading = false,
  block = false,
  icon,
  children,
  disabled,
  className = '',
  ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={[
        'inline-flex items-center justify-center rounded-md font-medium transition-colors cursor-pointer',
        variants[variant],
        sizes[size],
        block ? 'w-full' : '',
        disabled || loading ? 'cursor-not-allowed opacity-70' : '',
        className,
      ].join(' ')}
    >
      {loading && (
        <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
        </svg>
      )}
      {!loading && icon}
      {children}
    </button>
  )
}
