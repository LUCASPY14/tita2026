import { forwardRef, type InputHTMLAttributes } from 'react'

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
  label?: string
}

const base = 'w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-green-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500'

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, className = '', ...props }, ref) => (
    <div className={label ? 'flex flex-col gap-1' : ''}>
      {label && <label className="text-sm font-medium text-gray-700">{label}</label>}
      <input ref={ref} className={`${base} ${className}`} {...props} />
    </div>
  )
)

Input.displayName = 'Input'
export default Input
