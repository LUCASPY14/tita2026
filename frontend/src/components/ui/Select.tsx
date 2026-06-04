import { type SelectHTMLAttributes } from 'react'

interface Option {
  value: string | number
  label: string
}

interface SelectProps extends SelectHTMLAttributes<HTMLSelectElement> {
  options: Option[]
  placeholder?: string
}

export default function Select({ options, placeholder, className = '', ...props }: SelectProps) {
  return (
    <select
      className={[
        'w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-base text-slate-700 bg-white',
        'focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500',
        'transition-colors duration-150',
        'disabled:bg-slate-50 disabled:text-slate-400 disabled:cursor-not-allowed',
        'cursor-pointer',
        className,
      ].join(' ')}
      {...props}
    >
      {placeholder && <option value="" disabled>{placeholder}</option>}
      {options.map((opt) => (
        <option key={opt.value} value={opt.value}>
          {opt.label}
        </option>
      ))}
    </select>
  )
}
