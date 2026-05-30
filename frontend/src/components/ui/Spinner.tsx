import { Loader2 } from 'lucide-react'

export default function Spinner({ className = '' }: { className?: string }) {
  return (
    <div className={`flex justify-center items-center ${className}`} role="status">
      <Loader2 className="animate-spin w-8 h-8 text-green-600" aria-hidden="true" />
      <span className="sr-only">Cargando...</span>
    </div>
  )
}
