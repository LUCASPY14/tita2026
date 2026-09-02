import { useEffect, useState } from 'react'
import { useForm, useWatch } from 'react-hook-form'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Combobox from '../../components/ui/Combobox'
import Input from '../../components/ui/Input'
import Modal from '../../components/ui/Modal'
import {
  extractErrorMessage, BLANK_CLIENTE, RUC_CI_REGEX,
  type Cliente, type ClienteForm, type TipoCliente, type ListaPrecio, type Ciudad,
} from './shared'

interface Props {
  open: boolean
  cliente: Cliente | null
  tiposCliente: TipoCliente[]
  listasPrecios: ListaPrecio[]
  ciudades: Ciudad[]
  onClose: () => void
  onSaved: () => void
}

export default function ModalCliente({ open, cliente, tiposCliente, listasPrecios, ciudades, onClose, onSaved }: Props) {
  const [saving, setSaving] = useState(false)
  const { register, handleSubmit, reset, control, setValue, formState: { errors } } = useForm<ClienteForm>({
    defaultValues: BLANK_CLIENTE,
  })
  const activo = useWatch({ control, name: 'activo' })
  const ciudadVal = useWatch({ control, name: 'ciudad' })
  const modalidadFacturacion = useWatch({ control, name: 'modalidad_facturacion' })
  const permiteCC = useWatch({ control, name: 'permite_cuenta_corriente' })

  useEffect(() => {
    if (!open) return
    reset(cliente
      ? {
          nombres: cliente.nombres,
          apellidos: cliente.apellidos,
          razon_social: cliente.razon_social ?? '',
          ruc_ci: cliente.ruc_ci,
          direccion: cliente.direccion ?? '',
          ciudad: cliente.ciudad ?? '',
          telefono: cliente.telefono ?? '',
          email: cliente.email ?? '',
          limite_credito: cliente.limite_credito,
          permite_cuenta_corriente: cliente.permite_cuenta_corriente,
          activo: cliente.activo,
          lista_precio: String(cliente.lista_precio),
          tipo_cliente: String(cliente.tipo_cliente),
          modalidad_facturacion: cliente.modalidad_facturacion ?? 'INMEDIATA',
        }
      : BLANK_CLIENTE
    )
  }, [open, cliente, reset])

  const onSubmit = handleSubmit(async (form) => {
    setSaving(true)
    const payload = {
      ...form,
      limite_credito: Number(form.limite_credito) || 0,
      lista_precio: Number(form.lista_precio),
      tipo_cliente: Number(form.tipo_cliente),
    }
    try {
      if (cliente) {
        await api.patch(`/clientes/clientes/${cliente.id}/`, payload)
        toast.success('Cliente actualizado')
      } else {
        await api.post('/clientes/clientes/', payload)
        toast.success('Cliente creado')
      }
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  })

  const selectClass = (hasError?: boolean) => [
    'w-full border rounded-xl px-3 py-2 text-base text-slate-900 bg-white',
    'focus:outline-none focus:ring-2 transition-colors duration-150',
    hasError
      ? 'border-red-300 focus:ring-red-500/20 focus:border-red-500'
      : 'border-slate-200 focus:ring-green-500/30 focus:border-green-500',
  ].join(' ')
  const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

  return (
    <Modal
      open={open}
      title={cliente ? `Editar — ${cliente.apellidos}, ${cliente.nombres}` : 'Nuevo Cliente'}
      onCancel={onClose}
      onOk={onSubmit}
      okText={cliente ? 'Guardar Cambios' : 'Crear Cliente'}
      confirmLoading={saving}
      width={680}
    >
      <div className="space-y-5">
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input
            label="Nombres *"
            placeholder="Ej: Juan Carlos"
            error={errors.nombres?.message}
            {...register('nombres', { required: 'El nombre es obligatorio' })}
          />
          <Input
            label="Apellidos *"
            placeholder="Ej: González Pérez"
            error={errors.apellidos?.message}
            {...register('apellidos', { required: 'Los apellidos son obligatorios' })}
          />
          <Input
            label="RUC / CI *"
            placeholder="Ej: 1234567 o 80123456-5"
            error={errors.ruc_ci?.message}
            {...register('ruc_ci', {
              required: 'El RUC/CI es obligatorio',
              pattern: { value: RUC_CI_REGEX, message: 'Formato inválido. Ej: 1234567 o 80123456-5' },
            })}
          />
          <Input label="Razón Social" placeholder="Solo si es empresa" {...register('razon_social')} />
          <Input label="Teléfono" placeholder="+595 981 000 000" {...register('telefono')} />
          <Input
            label="Email"
            type="email"
            placeholder="cliente@email.com"
            error={errors.email?.message}
            {...register('email', {
              pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: 'Email inválido' },
            })}
          />
          <Input label="Dirección" placeholder="Calle y número" {...register('direccion')} />
          <div>
            <label className="block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5">Ciudad</label>
            <Combobox
              options={ciudades.map(c => ({ value: c.nombre, label: c.nombre }))}
              value={ciudadVal || undefined}
              onChange={(v) => setValue('ciudad', String(v))}
              filterLocal
              placeholder="Buscar ciudad..."
            />
          </div>
        </div>

        <div className="border-t border-slate-100 pt-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
          <div>
            <label className={labelClass}>Tipo de Cliente *</label>
            <select className={selectClass(!!errors.tipo_cliente)} {...register('tipo_cliente', { required: 'Seleccioná un tipo' })}>
              <option value="">Seleccionar...</option>
              {tiposCliente.map(t => <option key={t.id} value={t.id}>{t.nombre}</option>)}
            </select>
            {errors.tipo_cliente && <p className="text-xs text-red-500 mt-0.5">{errors.tipo_cliente.message}</p>}
          </div>
          <div>
            <label className={labelClass}>Lista de Precio *</label>
            <select className={selectClass(!!errors.lista_precio)} {...register('lista_precio', { required: 'Seleccioná una lista' })}>
              <option value="">Seleccionar...</option>
              {listasPrecios.map(l => <option key={l.id} value={l.id}>{l.nombre}</option>)}
            </select>
            {errors.lista_precio && <p className="text-xs text-red-500 mt-0.5">{errors.lista_precio.message}</p>}
          </div>
          <Input
            label="Límite de Crédito (Gs.)"
            type="number"
            min="0"
            step="1000"
            placeholder="0"
            disabled={!permiteCC}
            {...register('limite_credito', { min: { value: 0, message: 'Debe ser ≥ 0' } })}
          />
        </div>
        {permiteCC && (
          <p className="text-xs text-slate-400 -mt-3">
            0 = sin límite de deuda. Mayor a 0 = tope máximo de deuda acumulada.
          </p>
        )}

        <div className="border-t border-slate-100 pt-4 space-y-3">
          {([
            { key: 'activo' as const, label: `Cliente ${activo ? 'activo' : 'inactivo'}`, value: activo, color: 'green' as const },
            { key: 'modalidad_facturacion' as const, label: 'Factura mensual', value: modalidadFacturacion === 'MENSUAL', color: 'blue' as const },
            { key: 'permite_cuenta_corriente' as const, label: 'Permite cuenta corriente (fiado)', value: permiteCC, color: 'blue' as const },
          ]).map(({ key, label, value, color }) => (
            <div key={key} className="flex items-center gap-3">
              <button
                type="button"
                role="switch"
                aria-checked={value}
                onClick={() => {
                  if (key === 'activo') setValue('activo', !activo)
                  else if (key === 'modalidad_facturacion') setValue('modalidad_facturacion', modalidadFacturacion === 'MENSUAL' ? 'INMEDIATA' : 'MENSUAL')
                  else setValue('permite_cuenta_corriente', !permiteCC)
                }}
                className={[
                  'relative w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2',
                  `focus:ring-${color}-500/30`,
                  value ? `bg-${color}-500` : 'bg-slate-200',
                ].join(' ')}
              >
                <span className={[
                  'absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200',
                  value ? 'translate-x-5' : 'translate-x-0',
                ].join(' ')} />
              </button>
              <div>
                <span className="text-sm text-slate-700 font-medium">{label}</span>
                {key === 'modalidad_facturacion' && (
                  <p className="text-xs text-slate-400">
                    {modalidadFacturacion === 'MENSUAL'
                      ? 'Acumula transacciones del mes para emitir una sola factura'
                      : 'Una factura por transacción (por defecto)'}
                  </p>
                )}
                {key === 'permite_cuenta_corriente' && (
                  <p className="text-xs text-slate-400">
                    {permiteCC
                      ? 'Puede comprar al fiado y recargar saldo con cargo a su cuenta corriente'
                      : 'No puede acumular deuda (desactivado por defecto)'}
                  </p>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </Modal>
  )
}
