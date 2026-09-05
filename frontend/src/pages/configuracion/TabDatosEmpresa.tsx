import { useCallback, useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import SelectorUbicacion from '../clientes/SelectorUbicacion'
import type { Pais, Departamento, Ciudad } from '../clientes/shared'
import { extractErrorMessage, inputClass, labelClass, type DatosEmpresa } from './helpers'

type EmpForm = {
  ruc: string
  razon_social: string
  nombre_fantasia: string
  direccion: string
  ciudad: number | null
  telefono: string
  email: string
  activo: boolean
}

const EMPTY: EmpForm = {
  ruc: '', razon_social: '', nombre_fantasia: '', direccion: '',
  ciudad: null, telefono: '', email: '', activo: true,
}

export default function TabDatosEmpresa() {
  const [empresa, setEmpresa] = useState<DatosEmpresa | null>(null)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState<EmpForm>(EMPTY)
  const [saving, setSaving] = useState(false)
  const [paises, setPaises] = useState<Pais[]>([])
  const [departamentos, setDepartamentos] = useState<Departamento[]>([])
  const [ciudades, setCiudades] = useState<Ciudad[]>([])
  const [paisId, setPaisId] = useState<number | null>(null)
  const [departamentoId, setDepartamentoId] = useState<number | null>(null)
  const savedRef = useRef<EmpForm | null>(null)
  const formRef = useRef(form)
  // eslint-disable-next-line react-hooks/refs
  formRef.current = form

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [empRes, paisesRes, deptosRes, ciudadesRes] = await Promise.all([
        api.get('/contabilidad/datos-empresa/', { params: { page_size: 1 } }),
        api.get('/clientes/paises/', { params: { page_size: 200 } }),
        api.get('/clientes/departamentos/', { params: { page_size: 200 } }),
        api.get('/clientes/ciudades/', { params: { page_size: 200 } }),
      ])
      const listaPaises: Pais[] = paisesRes.data.results ?? paisesRes.data
      const listaDeptos: Departamento[] = deptosRes.data.results ?? deptosRes.data
      const listaCiudades: Ciudad[] = ciudadesRes.data.results ?? ciudadesRes.data
      setPaises(listaPaises)
      setDepartamentos(listaDeptos)
      setCiudades(listaCiudades)

      const emp: DatosEmpresa | null = (empRes.data.results ?? empRes.data ?? [])[0] ?? null
      setEmpresa(emp)
      if (emp) {
        const f: EmpForm = {
          ruc: emp.ruc,
          razon_social: emp.razon_social,
          nombre_fantasia: emp.nombre_fantasia ?? '',
          direccion: emp.direccion ?? '',
          ciudad: emp.ciudad,
          telefono: emp.telefono ?? '',
          email: emp.email ?? '',
          activo: emp.activo,
        }
        setForm(f)
        savedRef.current = f
        const ciudadActual = emp.ciudad ? listaCiudades.find(c => c.id_ciudad === emp.ciudad) : undefined
        const departamentoActual = ciudadActual
          ? listaDeptos.find(d => d.id_departamento === ciudadActual.departamento)
          : undefined
        setDepartamentoId(ciudadActual?.departamento ?? null)
        setPaisId(departamentoActual?.pais ?? null)
      }
    } catch { toast.error('Error al cargar datos de empresa') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (!savedRef.current) return
      if (JSON.stringify(formRef.current) !== JSON.stringify(savedRef.current)) {
        e.preventDefault()
      }
    }
    window.addEventListener('beforeunload', handler)
    return () => window.removeEventListener('beforeunload', handler)
  }, [])

  const save = useCallback(async () => {
    if (!form.ruc || !form.razon_social) { toast.error('RUC y razón social son obligatorios'); return }
    setSaving(true)
    try {
      if (empresa) {
        await api.put(`/contabilidad/datos-empresa/${empresa.id_datos_empresa}/`, form)
      } else {
        await api.post('/contabilidad/datos-empresa/', form)
      }
      toast.success('Datos guardados')
      savedRef.current = { ...form }
      load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [form, empresa, load])

  const f = (field: keyof EmpForm) => (e: React.ChangeEvent<HTMLInputElement>) =>
    setForm(prev => ({ ...prev, [field]: e.target.value }))

  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 max-w-2xl space-y-4">
      {loading ? (
        <div className="text-sm text-slate-400">Cargando...</div>
      ) : (
        <>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>RUC *</label>
              <input value={form.ruc} onChange={f('ruc')} className={inputClass} placeholder="80012345-1" />
            </div>
            <div>
              <label className={labelClass}>Razón Social *</label>
              <input value={form.razon_social} onChange={f('razon_social')} className={inputClass} />
            </div>
          </div>
          <div>
            <label className={labelClass}>Nombre de Fantasía</label>
            <input value={form.nombre_fantasia} onChange={f('nombre_fantasia')} className={inputClass} placeholder="Nombre comercial (opcional)" />
          </div>
          <div>
            <label className={labelClass}>Dirección</label>
            <input value={form.direccion} onChange={f('direccion')} className={inputClass} />
          </div>
          <SelectorUbicacion
            paises={paises}
            departamentos={departamentos}
            ciudades={ciudades}
            paisId={paisId}
            departamentoId={departamentoId}
            ciudadId={form.ciudad}
            onChangePais={setPaisId}
            onChangeDepartamento={setDepartamentoId}
            onChangeCiudad={(id) => setForm(prev => ({ ...prev, ciudad: id }))}
          />
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className={labelClass}>Teléfono</label>
              <input value={form.telefono} onChange={f('telefono')} className={inputClass} />
            </div>
            <div>
              <label className={labelClass}>Email</label>
              <input type="email" value={form.email} onChange={f('email')} className={inputClass} />
            </div>
          </div>
          <div className="pt-2">
            <Button variant="primary" loading={saving} onClick={save}>Guardar cambios</Button>
          </div>
        </>
      )}
    </div>
  )
}
