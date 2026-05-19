import { type ReactNode } from 'react'

interface CardProps {
  title?: ReactNode
  children: ReactNode
  className?: string
}

export default function Card({ title, children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-2xl border border-slate-100 shadow-sm ${className}`}>
      {title && (
        <div className="px-6 py-4 border-b border-slate-100 font-semibold text-slate-800 text-sm">
          {title}
        </div>
      )}
      <div className="p-6">{children}</div>
    </div>
  )
}
