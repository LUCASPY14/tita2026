import React, { useState, useEffect } from 'react';
import { CreditCard, Save, X } from 'lucide-react';
import { Modal, Button, Spinner } from '../../../components/common';
import api from '../../../services/api';
import type { Hijo, Tarjeta } from '../../../types';

interface TarjetaFormModalProps {
  hijo: Hijo;
  tarjeta?: Tarjeta | null;
  onClose: () => void;
  onSave: () => void;
}

interface TarjetaFormData {
  nro_tarjeta: string;
  estado: string;
  saldo_actual: number;
  saldo_alerta: number | '';
  limite_credito: number;
  fecha_vencimiento: string;
  permite_saldo_negativo: boolean;
  notificar_saldo_bajo: boolean;
  codigo_barras: string;
}

const generarNroTarjeta = (hijoId: number): string => {
  const timestamp = Date.now().toString().slice(-6);
  return `TRJ-${String(hijoId).padStart(4, '0')}-${timestamp}`;
};

const imprimirTicketTarjeta = (nroTarjeta: string, hijo: Hijo) => {
  const fecha = new Date();
  const fechaStr = fecha.toLocaleDateString('es-PY');
  const horaStr = fecha.toLocaleTimeString('es-PY', { hour: '2-digit', minute: '2-digit' });

  const html = `<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8" />
  <title>Tarjeta ${nroTarjeta}</title>
  <style>
    * { margin: 0; padding: 0; box-sizing: border-box; }
    body { font-family: monospace; width: 280px; padding: 10px; }
    .hr   { border: none; border-top: 1px dashed #888; margin: 8px 0; }
    .c    { text-align: center; }
    .l    { text-align: left; }
    .bold { font-weight: bold; }
    .title { font-size: 16px; font-weight: bold; letter-spacing: 2px; }
    .name  { font-size: 14px; font-weight: bold; margin-bottom: 3px; }
    .row   { font-size: 12px; color: #444; margin-bottom: 2px; }
    .card  { font-size: 15px; font-weight: bold; letter-spacing: 1px; margin: 4px 0; }
    .ok    { font-size: 13px; font-weight: bold; color: #15803d; }
    .xs    { font-size: 10px; color: #aaa; }
    @media print {
      @page { margin: 0; size: 80mm auto; }
      body  { width: 100%; }
    }
  </style>
</head>
<body>
  <div class="c" style="padding-bottom:8px;">
    <p class="title">CANTINA TITA</p>
    <p class="xs">Comprobante de Tarjeta</p>
  </div>
  <hr class="hr" />
  <div class="l">
    <p class="row"><span class="bold">Fecha:</span> ${fechaStr}</p>
    <p class="row"><span class="bold">Hora:</span>  ${horaStr}</p>
  </div>
  <hr class="hr" />
  <div class="l">
    <p class="name">${hijo.nombre} ${hijo.apellido}</p>
    ${hijo.grado ? `<p class="row"><span class="bold">Curso:</span> ${hijo.grado}</p>` : ''}
  </div>
  <hr class="hr" />
  <div class="c">
    <p class="xs">Número de Tarjeta</p>
    <p class="card">${nroTarjeta}</p>
    <p class="ok">TARJETA ACTIVA</p>
  </div>
  <hr class="hr" />
  <div class="c xs">
    <p>Saldo inicial: Gs. 0</p>
    <p style="margin-top:4px;">Buen provecho!</p>
  </div>
</body>
</html>`;

  const pw = window.open('', '_blank', 'width=380,height=480,toolbar=0,menubar=0,location=0,scrollbars=0');
  if (!pw) return;
  pw.document.write(html);
  pw.document.close();
  pw.focus();
  setTimeout(() => {
    pw.print();
    pw.onafterprint = () => pw.close();
  }, 300);
};

const TarjetaFormModal: React.FC<TarjetaFormModalProps> = ({ hijo, tarjeta, onClose, onSave }) => {
  const isEditing = !!tarjeta;

  const [formData, setFormData] = useState<TarjetaFormData>({
    nro_tarjeta: tarjeta?.nro_tarjeta ?? generarNroTarjeta(hijo.id_hijo),
    estado: tarjeta?.estado ?? 'Activa',
    saldo_actual: tarjeta ? Number(tarjeta.saldo_actual) : 0,
    saldo_alerta: tarjeta?.saldo_alerta != null ? Number(tarjeta.saldo_alerta) : '',
    limite_credito: tarjeta ? Number(tarjeta.limite_credito) : 0,
    fecha_vencimiento: tarjeta?.fecha_vencimiento ?? '',
    permite_saldo_negativo: tarjeta?.permite_saldo_negativo ?? false,
    notificar_saldo_bajo: tarjeta?.notificar_saldo_bajo ?? true,
    codigo_barras: tarjeta?.codigo_barras ?? '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Re-generate nro_tarjeta if hijo changes and not editing
    if (!isEditing) {
      setFormData(prev => ({ ...prev, nro_tarjeta: generarNroTarjeta(hijo.id_hijo) }));
    }
  }, [hijo.id_hijo, isEditing]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value, type } = e.target;
    const checked = (e.target as HTMLInputElement).checked;

    setFormData(prev => ({
      ...prev,
      [name]:
        type === 'checkbox'
          ? checked
          : type === 'number'
          ? value === ''
            ? ''
            : Number(value)
          : value,
    }));

    if (errors[name]) {
      setErrors(prev => { const n = { ...prev }; delete n[name]; return n; });
    }
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};
    if (!formData.nro_tarjeta.trim()) newErrors.nro_tarjeta = 'El número de tarjeta es requerido';
    if (!formData.estado) newErrors.estado = 'El estado es requerido';
    if (formData.limite_credito < 0) newErrors.limite_credito = 'No puede ser negativo';
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    setSaving(true);
    try {
      const payload: Record<string, unknown> = {
        nro_tarjeta: formData.nro_tarjeta,
        estado: formData.estado,
        limite_credito: formData.limite_credito,
        permite_saldo_negativo: formData.permite_saldo_negativo,
        notificar_saldo_bajo: formData.notificar_saldo_bajo,
        id_hijo: hijo.id_hijo,
      };

      if (formData.saldo_alerta !== '') payload.saldo_alerta = formData.saldo_alerta;
      if (formData.fecha_vencimiento) payload.fecha_vencimiento = formData.fecha_vencimiento;
      if (formData.codigo_barras.trim()) payload.codigo_barras = formData.codigo_barras.trim();

      if (isEditing) {
        // Solo se puede editar estado y configuración, NO saldo_actual (se maneja mediante recargas/consumos)
        await api.patch(`/tarjetas/${tarjeta!.nro_tarjeta}/`, {
          estado: formData.estado,
          saldo_alerta: formData.saldo_alerta !== '' ? formData.saldo_alerta : null,
          limite_credito: formData.limite_credito,
          fecha_vencimiento: formData.fecha_vencimiento || null,
          permite_saldo_negativo: formData.permite_saldo_negativo,
          notificar_saldo_bajo: formData.notificar_saldo_bajo,
          codigo_barras: formData.codigo_barras.trim() || null,
        });
      } else {
        // Al crear, saldo_actual comienza en 0
        payload.saldo_actual = 0;
        payload.fecha_creacion = new Date().toISOString();
        await api.post('/tarjetas/', payload);
        // Imprimir comprobante automáticamente
        imprimirTicketTarjeta(formData.nro_tarjeta, hijo);
      }
      onSave();
    } catch (error: any) {
      if (error.response?.data) {
        const backendErrors: Record<string, string> = {};
        Object.entries(error.response.data).forEach(([key, val]) => {
          backendErrors[key] = Array.isArray(val) ? (val as string[])[0] : String(val);
        });
        setErrors(backendErrors);
      } else {
        setErrors({ general: 'Error al guardar la tarjeta. Intentá de nuevo.' });
      }
    } finally {
      setSaving(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} size="md">
      <div className="p-6">
        {/* Header */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-lg bg-amber-100">
              <CreditCard className="h-5 w-5 text-amber-600" />
            </div>
            <div>
              <h3 className="text-lg font-semibold text-gray-900">
                {isEditing ? 'Editar Tarjeta' : 'Asignar Tarjeta'}
              </h3>
              <p className="text-sm text-gray-600">
                {hijo.nombre} {hijo.apellido}
              </p>
            </div>
          </div>
          <button onClick={onClose} className="text-gray-400 hover:text-gray-600 transition-colors">
            <X className="h-6 w-6" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          {errors.general && (
            <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-sm text-red-700">
              {errors.general}
            </div>
          )}

          {/* Número de tarjeta */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Número de Tarjeta <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              name="nro_tarjeta"
              value={formData.nro_tarjeta}
              onChange={handleChange}
              disabled={isEditing}
              maxLength={20}
              className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 ${
                isEditing ? 'bg-gray-50 text-gray-500 cursor-not-allowed' : ''
              } ${errors.nro_tarjeta ? 'border-red-500' : 'border-gray-300'}`}
              placeholder="TRJ-0001-123456"
            />
            {errors.nro_tarjeta && <p className="mt-1 text-xs text-red-600">{errors.nro_tarjeta}</p>}
            {!isEditing && (
              <p className="mt-1 text-xs text-gray-500">Generado automáticamente. Podés modificarlo.</p>
            )}
          </div>

          {/* Estado + Código de barras */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Estado</label>
              <select
                name="estado"
                value={formData.estado}
                onChange={handleChange}
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
              >
                <option value="Activa">Activa</option>
                <option value="Bloqueada">Bloqueada</option>
                <option value="Inactiva">Inactiva</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Código de Barras</label>
              <input
                type="text"
                name="codigo_barras"
                value={formData.codigo_barras}
                onChange={handleChange}
                maxLength={50}
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 ${
                  errors.codigo_barras ? 'border-red-500' : 'border-gray-300'
                }`}
                placeholder="Opcional"
              />
              {errors.codigo_barras && <p className="mt-1 text-xs text-red-600">{errors.codigo_barras}</p>}
            </div>
          </div>

          {/* Saldo alerta + Límite crédito */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Alerta de Saldo (Gs.)
              </label>
              <input
                type="number"
                name="saldo_alerta"
                value={formData.saldo_alerta}
                onChange={handleChange}
                min="0"
                step="1000"
                className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                placeholder="Ej: 10000"
              />
              <p className="mt-1 text-xs text-gray-500">Recibís notificación cuando el saldo baja de este monto.</p>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Límite de Crédito (Gs.)
              </label>
              <input
                type="number"
                name="limite_credito"
                value={formData.limite_credito}
                onChange={handleChange}
                min="0"
                step="1000"
                className={`w-full rounded-lg border px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500 ${
                  errors.limite_credito ? 'border-red-500' : 'border-gray-300'
                }`}
              />
              {errors.limite_credito && <p className="mt-1 text-xs text-red-600">{errors.limite_credito}</p>}
            </div>
          </div>

          {/* Fecha de vencimiento */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">Fecha de Vencimiento</label>
            <input
              type="date"
              name="fecha_vencimiento"
              value={formData.fecha_vencimiento}
              onChange={handleChange}
              min={new Date().toISOString().split('T')[0]}
              className="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
            />
            <p className="mt-1 text-xs text-gray-500">Opcional. Dejá vacío si no vence.</p>
          </div>

          {/* Opciones */}
          <div className="space-y-3 p-4 bg-gray-50 rounded-lg">
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="permite_saldo_negativo"
                checked={formData.permite_saldo_negativo}
                onChange={handleChange}
                className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
              />
              <div>
                <span className="text-sm font-medium text-gray-700">Permite saldo negativo</span>
                <p className="text-xs text-gray-500">El estudiante puede comprar aunque no tenga saldo (hasta el límite de crédito).</p>
              </div>
            </label>
            <label className="flex items-center gap-3 cursor-pointer">
              <input
                type="checkbox"
                name="notificar_saldo_bajo"
                checked={formData.notificar_saldo_bajo}
                onChange={handleChange}
                className="h-4 w-4 rounded border-gray-300 text-amber-600 focus:ring-amber-500"
              />
              <div>
                <span className="text-sm font-medium text-gray-700">Notificar saldo bajo</span>
                <p className="text-xs text-gray-500">Enviar notificación cuando el saldo esté por debajo del monto de alerta.</p>
              </div>
            </label>
          </div>

          {/* Saldo actual (solo lectura en edición) */}
          {isEditing && (
            <div className="p-3 bg-blue-50 border border-blue-200 rounded-lg text-sm text-blue-800">
              <span className="font-medium">Saldo actual:</span>{' '}
              Gs. {Number(tarjeta!.saldo_actual).toLocaleString('es-PY')}
              <span className="ml-2 text-xs text-blue-600">(se gestiona desde Recargas)</span>
            </div>
          )}

          {/* Botones */}
          <div className="flex gap-3 pt-2 border-t">
            <Button type="button" variant="outline" onClick={onClose} disabled={saving} className="flex-1">
              Cancelar
            </Button>
            <Button
              type="submit"
              disabled={saving}
              leftIcon={saving ? <Spinner size="sm" /> : <Save className="h-4 w-4" />}
              className="flex-1"
            >
              {saving ? 'Guardando...' : isEditing ? 'Guardar Cambios' : 'Asignar Tarjeta'}
            </Button>
          </div>
        </form>
      </div>
    </Modal>
  );
};

export default TarjetaFormModal;
