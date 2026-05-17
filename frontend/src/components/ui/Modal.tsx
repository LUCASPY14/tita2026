import { type ReactNode, useEffect } from 'react'
import Button from './Button'

interface ModalProps {
  open: boolean
  title: string
  onOk: () => void
  onCancel: () => void
  okText?: string
  cancelText?: string
  confirmLoading?: boolean
  children: ReactNode
  width?: number
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
}: ModalProps) {
  useEffect(() => {
    if (open) document.body.style.overflow = 'hidden'
    else document.body.style.overflow = ''
    return () => { document.body.style.overflow = '' }
  }, [open])

  if (!open) return null

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onCancel} />
      <div
        className="relative bg-white rounded-lg shadow-xl flex flex-col max-h-[90vh]"
        style={{ width: Math.min(width, window.innerWidth - 32) }}
      >
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
          <button onClick={onCancel} className="text-gray-400 hover:text-gray-600 text-xl leading-none">&times;</button>
        </div>
        <div className="px-6 py-4 overflow-y-auto flex-1">{children}</div>
        <div className="flex justify-end gap-2 px-6 py-4 border-t">
          <Button variant="secondary" onClick={onCancel}>{cancelText}</Button>
          <Button variant="primary" onClick={onOk} loading={confirmLoading}>{okText}</Button>
        </div>
      </div>
    </div>
  )
}
