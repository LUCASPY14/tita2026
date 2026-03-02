import React from 'react';
import { Toaster, ToastBar, toast as hotToast } from 'react-hot-toast';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';

/**
 * Toast Provider - Configuración global de notificaciones
 * Usar en App.tsx o index.tsx para activar notificaciones
 */
export const ToastProvider: React.FC = () => {
  return (
    <Toaster
      position="top-right"
      reverseOrder={false}
      gutter={8}
      toastOptions={{
        duration: 4000,
        style: {
          background: '#fff',
          color: '#374151',
          padding: '12px 16px',
          borderRadius: '0.5rem',
          boxShadow: '0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)',
          maxWidth: '500px',
        },
        success: {
          duration: 3000,
          iconTheme: {
            primary: '#10b981',
            secondary: '#fff',
          },
        },
        error: {
          duration: 5000,
          iconTheme: {
            primary: '#ef4444',
            secondary: '#fff',
          },
        },
      }}
    >
      {(t) => (
        <ToastBar toast={t}>
          {({ icon, message }) => (
            <div className="flex items-center gap-3 w-full">
              <div className="flex-shrink-0">
                {icon}
              </div>
              <div className="flex-1 text-sm font-medium">
                {message}
              </div>
              {t.type !== 'loading' && (
                <button
                  onClick={() => hotToast.dismiss(t.id)}
                  className="flex-shrink-0 text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <X size={16} />
                </button>
              )}
            </div>
          )}
        </ToastBar>
      )}
    </Toaster>
  );
};

/**
 * Toast Utilities - Funciones helper para mostrar notificaciones
 */
export const toast = {
  success: (message: string, options?: any) => {
    return hotToast.success(message, {
      icon: <CheckCircle className="h-5 w-5 text-green-500" />,
      ...options,
    });
  },

  error: (message: string, options?: any) => {
    return hotToast.error(message, {
      icon: <XCircle className="h-5 w-5 text-red-500" />,
      ...options,
    });
  },

  warning: (message: string, options?: any) => {
    return hotToast(message, {
      icon: <AlertCircle className="h-5 w-5 text-yellow-500" />,
      ...options,
    });
  },

  info: (message: string, options?: any) => {
    return hotToast(message, {
      icon: <Info className="h-5 w-5 text-blue-500" />,
      ...options,
    });
  },

  loading: (message: string, options?: any) => {
    return hotToast.loading(message, options);
  },

  promise: <T,>(
    promise: Promise<T>,
    messages: {
      loading: string;
      success: string | ((data: T) => string);
      error: string | ((error: any) => string);
    },
    options?: any
  ) => {
    return hotToast.promise(
      promise,
      {
        loading: messages.loading,
        success: (data) => {
          const msg = typeof messages.success === 'function' 
            ? messages.success(data) 
            : messages.success;
          return msg;
        },
        error: (error) => {
          const msg = typeof messages.error === 'function' 
            ? messages.error(error) 
            : messages.error;
          return msg;
        },
      },
      options
    );
  },

  dismiss: (toastId?: string) => {
    return hotToast.dismiss(toastId);
  },

  remove: (toastId?: string) => {
    return hotToast.remove(toastId);
  },
};

// Custom toast con título y descripción
export const toastCustom = {
  success: (title: string, description?: string) => {
    return hotToast.custom(
      (t) => (
        <div className={`${t.visible ? 'animate-enter' : 'animate-leave'} bg-white rounded-lg shadow-lg p-4 flex items-start gap-3 max-w-md`}>
          <CheckCircle className="h-5 w-5 text-green-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{title}</p>
            {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
          </div>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={16} />
          </button>
        </div>
      ),
      { duration: 4000 }
    );
  },

  error: (title: string, description?: string) => {
    return hotToast.custom(
      (t) => (
        <div className={`${t.visible ? 'animate-enter' : 'animate-leave'} bg-white rounded-lg shadow-lg p-4 flex items-start gap-3 max-w-md`}>
          <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{title}</p>
            {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
          </div>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={16} />
          </button>
        </div>
      ),
      { duration: 5000 }
    );
  },

  warning: (title: string, description?: string) => {
    return hotToast.custom(
      (t) => (
        <div className={`${t.visible ? 'animate-enter' : 'animate-leave'} bg-white rounded-lg shadow-lg p-4 flex items-start gap-3 max-w-md`}>
          <AlertCircle className="h-5 w-5 text-yellow-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{title}</p>
            {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
          </div>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={16} />
          </button>
        </div>
      ),
      { duration: 4000 }
    );
  },

  info: (title: string, description?: string) => {
    return hotToast.custom(
      (t) => (
        <div className={`${t.visible ? 'animate-enter' : 'animate-leave'} bg-white rounded-lg shadow-lg p-4 flex items-start gap-3 max-w-md`}>
          <Info className="h-5 w-5 text-blue-500 flex-shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="font-semibold text-gray-900">{title}</p>
            {description && <p className="text-sm text-gray-600 mt-1">{description}</p>}
          </div>
          <button
            onClick={() => hotToast.dismiss(t.id)}
            className="text-gray-400 hover:text-gray-600"
          >
            <X size={16} />
          </button>
        </div>
      ),
      { duration: 4000 }
    );
  },
};

export default toast;
