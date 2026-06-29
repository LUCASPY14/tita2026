import { useState, useRef, useEffect, useLayoutEffect } from 'react'
import { createPortal } from 'react-dom'

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
  const [isFocused, setIsFocused] = useState(false)
  const [dropdownStyle, setDropdownStyle] = useState<React.CSSProperties>({})
  const wrapperRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  const selected = options.find((o) => o.value === value)

  const displayValue = isFocused ? query : (selected?.label ?? '')

  const filtered = filterLocal
    ? options.filter((o) => o.label.toLowerCase().includes(displayValue.toLowerCase()))
    : options

  // Recalculate dropdown position based on input's viewport rect
  const updatePosition = () => {
    if (!inputRef.current) return
    const rect = inputRef.current.getBoundingClientRect()
    setDropdownStyle({
      position: 'fixed',
      top: rect.bottom + 6,
      left: rect.left,
      width: rect.width,
      zIndex: 9999,
    })
  }

  useLayoutEffect(() => {
    if (open) updatePosition()
  }, [open, displayValue])

  useEffect(() => {
    if (!open) return
    const handleScroll = () => updatePosition()
    const handleResize = () => updatePosition()
    window.addEventListener('scroll', handleScroll, true)
    window.addEventListener('resize', handleResize)
    return () => {
      window.removeEventListener('scroll', handleScroll, true)
      window.removeEventListener('resize', handleResize)
    }
  }, [open])

  useEffect(() => {
    const handleClick = (e: MouseEvent) => {
      if (
        wrapperRef.current && !wrapperRef.current.contains(e.target as Node) &&
        !(e.target as Element)?.closest('[data-combobox-dropdown]')
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && filtered.length > 0) {
      const first = filtered[0]
      onChange(first.value, first)
      setQuery(first.label)
      setOpen(false)
      e.preventDefault()
    } else if (e.key === 'Escape') {
      setOpen(false)
    }
  }

  const dropdown = open && (filtered.length > 0 || query.length > 0) ? createPortal(
    <ul
      data-combobox-dropdown
      role="listbox"
      style={dropdownStyle}
      className="bg-white border border-slate-200 rounded-xl shadow-lg shadow-slate-200/60 max-h-52 overflow-y-auto"
    >
      {filtered.length > 0 ? (
        filtered.map((opt) => (
          <li
            key={opt.value}
            role="option"
            aria-selected={opt.value === value}
            className="px-3.5 py-3 text-base text-slate-700 hover:bg-green-50 hover:text-green-700 cursor-pointer transition-colors first:rounded-t-xl last:rounded-b-xl"
            onMouseDown={() => {
              onChange(opt.value, opt)
              setQuery(opt.label)
              setOpen(false)
            }}
          >
            {opt.label}
          </li>
        ))
      ) : (
        <li className="px-3.5 py-3 text-base text-slate-400 text-center">Sin resultados</li>
      )}
    </ul>,
    document.body,
  ) : null

  return (
    <div ref={wrapperRef} className={`relative ${className}`}>
      <input
        ref={inputRef}
        role="combobox"
        aria-expanded={open}
        aria-haspopup="listbox"
        aria-autocomplete="list"
        autoComplete="off"
        className={[
          'w-full border border-slate-200 rounded-xl px-3.5 py-2.5 text-base text-slate-900 bg-white',
          'placeholder:text-slate-400',
          'focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-500',
          'transition-colors duration-150',
        ].join(' ')}
        placeholder={placeholder}
        value={displayValue}
        onFocus={() => { setQuery(selected?.label ?? ''); setOpen(true); setIsFocused(true) }}
        onBlur={() => setIsFocused(false)}
        onChange={(e) => {
          setQuery(e.target.value)
          setOpen(true)
          onSearch?.(e.target.value)
        }}
        onKeyDown={handleKeyDown}
      />
      {dropdown}
    </div>
  )
}
