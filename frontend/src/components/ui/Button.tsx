import { type ButtonHTMLAttributes, type ReactNode } from 'react'
import { Loader2 } from 'lucide-react'

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  block?: boolean
  icon?: ReactNode
}

const variants = {
  primary:
    'bg-green-600 text-white hover:bg-green-700 active:bg-green-800 ' +
    'shadow-sm shadow-green-600/25 ' +
    'focus-visible:ring-green-500 ' +
    'disabled:bg-green-300 disabled:shadow-none',
  secondary:
    'bg-white text-slate-700 border border-slate-200 ' +
    'hover:bg-slate-50 hover:border-slate-300 active:bg-slate-100 ' +
    'focus-visible:ring-slate-400 ' +
    'disabled:text-slate-400 disabled:bg-slate-50',
  danger:
    'bg-red-600 text-white hover:bg-red-700 active:bg-red-800 ' +
    'shadow-sm shadow-red-600/25 ' +
    'focus-visible:ring-red-500 ' +
    'disabled:bg-red-300 disabled:shadow-none',
  ghost:
    'bg-transparent text-slate-600 hover:bg-slate-100 hover:text-slate-800 active:bg-slate-200 ' +
    'focus-visible:ring-slate-400 ' +
    'disabled:text-slate-300',
}

const sizes = {
  sm: 'text-xs px-2.5 py-1.5 gap-1.5',
  md: 'text-sm px-3.5 py-2 gap-1.5',
  lg: 'text-sm px-5 py-2.5 gap-2',
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
        'inline-flex items-center justify-center rounded-xl font-medium',
        'transition-all duration-150 cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1',
        'active:scale-[0.98]',
        variants[variant],
        sizes[size],
        block ? 'w-full' : '',
        disabled || loading ? 'cursor-not-allowed opacity-60 active:scale-100' : '',
        className,
      ].join(' ')}
    >
      {loading ? (
        <Loader2 className="animate-spin h-4 w-4 shrink-0" />
      ) : icon ? (
        <span className="shrink-0">{icon}</span>
      ) : null}
      {children}
    </button>
  )
}
