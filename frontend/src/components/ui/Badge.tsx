export type BadgeColor = 'green' | 'red' | 'orange' | 'blue' | 'purple' | 'default'

const colors: Record<BadgeColor, string> = {
  green: 'bg-green-100 text-green-800',
  red: 'bg-red-100 text-red-800',
  orange: 'bg-orange-100 text-orange-800',
  blue: 'bg-blue-100 text-blue-800',
  purple: 'bg-purple-100 text-purple-800',
  default: 'bg-gray-100 text-gray-700',
}

interface BadgeProps {
  color?: BadgeColor
  children: React.ReactNode
  className?: string
}

export default function Badge({ color = 'default', children, className = '' }: BadgeProps) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${colors[color]} ${className}`}>
      {children}
    </span>
  )
}
