import React from 'react';
import { AlertTriangle } from 'lucide-react';
import Modal, { ModalFooter } from './Modal';

interface ConfirmDialogProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title: string;
  message: string;
  confirmText?: string;
  cancelText?: string;
  isLoading?: boolean;
  variant?: 'primary' | 'success' | 'danger';
}

const ConfirmDialog: React.FC<ConfirmDialogProps> = ({
  isOpen,
  onClose,
  onConfirm,
  title,
  message,
  confirmText = 'Confirmar',
  cancelText = 'Cancelar',
  isLoading = false,
  variant = 'danger',
}) => {
  const iconClass = variant === 'success'
    ? 'bg-green-100'
    : variant === 'primary'
    ? 'bg-blue-100'
    : 'bg-red-100';

  const iconColor = variant === 'success'
    ? 'text-green-600'
    : variant === 'primary'
    ? 'text-blue-600'
    : 'text-red-600';

  return (
    <Modal
      isOpen={isOpen}
      onClose={onClose}
      title={title}
      size="sm"
      closeOnOverlayClick={!isLoading}
      footer={
        <ModalFooter
          onCancel={onClose}
          onConfirm={onConfirm}
          cancelText={cancelText}
          confirmText={confirmText}
          confirmVariant={variant}
          isLoading={isLoading}
        />
      }
    >
      <div className="flex items-start gap-3">
        <div className={`flex h-10 w-10 flex-shrink-0 items-center justify-center rounded-full ${iconClass}`}>
          <AlertTriangle className={`h-5 w-5 ${iconColor}`} />
        </div>
        <p className="mt-2 text-sm text-gray-600">{message}</p>
      </div>
    </Modal>
  );
};

export default ConfirmDialog;
