export type BadgeColor = 'green' | 'red' | 'orange' | 'yellow' | 'blue' | 'purple' | 'default'

const colors: Record<BadgeColor, string> = {
  green:   'bg-green-100 text-green-700 ring-1 ring-inset ring-green-600/20',
  red:     'bg-red-100 text-red-700 ring-1 ring-inset ring-red-600/20',
  orange:  'bg-orange-100 text-orange-700 ring-1 ring-inset ring-orange-600/20',
  yellow:  'bg-yellow-100 text-yellow-700 ring-1 ring-inset ring-yellow-600/20',
  blue:    'bg-blue-100 text-blue-700 ring-1 ring-inset ring-blue-600/20',
  purple:  'bg-purple-100 text-purple-700 ring-1 ring-inset ring-purple-600/20',
  default: 'bg-slate-100 text-slate-600 ring-1 ring-inset ring-slate-500/20',
}

interface BadgeProps {
  color?: BadgeColor
  children: React.ReactNode
  className?: string
}

export default function Badge({ color = 'default', children, className = '' }: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${colors[color]} ${className}`}
    >
      {children}
    </span>
  )
}
