import { forwardRef, useId, type InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
}

const base =
  'w-full border rounded-xl px-3 py-2 text-sm text-slate-900 bg-white ' +
  'placeholder:text-slate-400 ' +
  'focus:outline-none focus:ring-2 transition-colors duration-150 ' +
  'disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed'

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, className = '', ...props }, ref) => {
    const autoId = useId()
    const id = props.id ?? autoId
    const errorId = `${id}-error`

    return (
      <div className={label ? 'flex flex-col gap-1.5' : ''}>
        {label && (
          <label htmlFor={id} className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
            {label}
          </label>
        )}
        <input
          ref={ref}
          {...props}
          id={id}
          aria-invalid={!!error}
          aria-describedby={error ? errorId : undefined}
          className={[
            base,
            error
              ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
              : 'border-slate-200 focus:ring-green-500/30 focus:border-green-500',
            className,
          ].join(' ')}
        />
        {error && <p id={errorId} className="text-xs text-red-500 mt-0.5">{error}</p>}
      </div>
    )
  }
)

Input.displayName = 'Input'
export default Input
