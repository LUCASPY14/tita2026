import { type ReactNode } from 'react'

interface CardProps {
  title?: ReactNode
  children: ReactNode
  className?: string
}

export default function Card({ title, children, className = '' }: CardProps) {
  return (
    <div className={`bg-white rounded-lg border border-gray-200 shadow-sm ${className}`}>
      {title && (
        <div className="px-4 py-3 border-b border-gray-200 font-medium text-gray-800">
          {title}
        </div>
      )}
      <div className="p-4">{children}</div>
    </div>
  )
}
