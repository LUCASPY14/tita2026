import { forwardRef, type InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
}

const base =
  'w-full border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white ' +
  'placeholder:text-slate-400 ' +
  'focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500 ' +
  'transition-colors duration-150 ' +
  'disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed'

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, className = '', ...props }, ref) => (
    <div className={label ? 'flex flex-col gap-1.5' : ''}>
      {label && (
        <label className="text-xs font-semibold text-slate-500 uppercase tracking-wide">
          {label}
        </label>
      )}
      <input ref={ref} className={`${base} ${className}`} {...props} />
    </div>
  )
)

Input.displayName = 'Input'
export default Input
