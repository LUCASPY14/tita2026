import { useState, useRef, useEffect } from 'react'

interface Option {
  value: string | number
  label: string
  data?: unknown
}

interface ComboboxProps {
  options: Option[]
  value?: string | number
  onChange: (value: string | number, option: Option) => void
  onSearch?: (query: string) => void
  placeholder?: string
  filterLocal?: boolean
  className?: string
}

export default function Combobox({
  options,
  value,
  onChange,
  onSearch,
  placeholder = 'Buscar...',
  filterLocal = false,
  className = '',
}: ComboboxProps) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  const selected = options.find((o) => o.value === value)

  const filtered = filterLocal
    ? options.filter((o) => o.label.toLowerCase().includes(query.toLowerCase()))
    : options

  useEffect(() => {
    if (selected) setQuery(selected.label)
  }, [selected?.label])

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  return (
    <div ref={ref} className={`relative ${className}`}>
      <input
        className={[
          'w-full border border-slate-200 rounded-xl px-3 py-2 text-sm text-slate-900 bg-white',
          'placeholder:text-slate-400',
          'focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500',
          'transition-colors duration-150',
        ].join(' ')}
        placeholder={placeholder}
        value={query}
        onFocus={() => setOpen(true)}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
          onSearch?.(e.target.value)
        }}
      />
      {open && filtered.length > 0 && (
        <ul className="absolute z-50 w-full mt-1.5 bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/60 max-h-52 overflow-y-auto">
          {filtered.map((opt) => (
            <li
              key={opt.value}
              className="px-3 py-2.5 text-sm text-slate-700 hover:bg-green-50 hover:text-green-700 cursor-pointer transition-colors first:rounded-t-xl last:rounded-b-xl"
              onMouseDown={() => {
                onChange(opt.value, opt)
                setQuery(opt.label)
                setOpen(false)
              }}
            >
              {opt.label}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
