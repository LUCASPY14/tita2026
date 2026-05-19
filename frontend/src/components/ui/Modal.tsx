import { type ReactNode, useEffect } from 'react'
import { X } from 'lucide-react'
import Button from './Button'

interface ModalProps {
  open: boolean
  title: string
  onCancel: () => void
  onOk?: () => void
  okText?: string
  cancelText?: string
  confirmLoading?: boolean
  children: ReactNode
  width?: number
  /** null = no footer; ReactNode = custom footer; undefined = default OK/Cancel */
  footer?: ReactNode | null
}

export default function Modal({
  open,
  title,
  onOk,
  onCancel,
  okText = 'Aceptar',
  cancelText = 'Cancelar',
  confirmLoading = false,
  children,
  width = 480,
  footer,
}: ModalProps) {
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  const defaultFooter = (
    <>
      <Button variant="secondary" onClick={onCancel}>{cancelText}</Button>
      {onOk && (
        <Button variant="primary" onClick={onOk} loading={confirmLoading}>{okText}</Button>
      )}
    </>
  )

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div
        className="absolute inset-0 bg-slate-900/50 backdrop-blur-sm"
        onClick={onCancel}
      />
      <div
        className="relative bg-white rounded-2xl shadow-2xl shadow-slate-900/20 flex flex-col max-h-[90vh]"
        style={{ width: Math.min(width, window.innerWidth - 32) }}
      >
        {/* Header */}
        <div className="flex items-center justify-between px-6 py-4 border-b border-slate-100 shrink-0">
          <h3 className="text-base font-semibold text-slate-800 truncate pr-4">{title}</h3>
          <button
            onClick={onCancel}
            className="p-1.5 rounded-lg text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors cursor-pointer shrink-0"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Body */}
        <div className="px-6 py-5 overflow-y-auto flex-1">{children}</div>

        {/* Footer */}
        {footer !== null && (
          <div className="flex justify-end gap-2 px-6 py-4 border-t border-slate-100 bg-slate-50/60 rounded-b-2xl shrink-0">
            {footer !== undefined ? footer : defaultFooter}
          </div>
        )}
      </div>
    </div>
  )
}
