import { useCallback, useEffect, useMemo, useState } from 'react'
import toast from 'react-hot-toast'
import { Edit2, Trash2, Plus, ChevronRight } from 'lucide-react'
import api from '../../services/api'
import Button from '../../components/ui/Button'
import Modal from '../../components/ui/Modal'
import { extractErrorMessage, inputClass, labelClass, type DeleteTarget } from './helpers'
import type { Pais, Departamento, Ciudad } from '../clientes/shared'

type ModalState =
  | { nivel: 'pais'; editing: Pais | null }
  | { nivel: 'departamento'; editing: Departamento | null }
  | { nivel: 'ciudad'; editing: Ciudad | null }

export default function TabUbicaciones({ onDelete }: { onDelete: (t: DeleteTarget) => void }) {
  const [paises, setPaises] = useState<Pais[]>([])
  const [departamentos, setDepartamentos] = useState<Departamento[]>([])
  const [ciudades, setCiudades] = useState<Ciudad[]>([])
  const [loading, setLoading] = useState(false)

  const [paisSel, setPaisSel] = useState<number | null>(null)
  const [deptoSel, setDeptoSel] = useState<number | null>(null)

  const [modal, setModal] = useState<ModalState | null>(null)
  const [nombreForm, setNombreForm] = useState('')
  const [paisForm, setPaisForm] = useState<number | ''>('')
  const [deptoForm, setDeptoForm] = useState<number | ''>('')
  const [saving, setSaving] = useState(false)

  const load = useCallback(async () => {
    setLoading(true)
    try {
      const [p, d, c] = await Promise.all([
        api.get('/clientes/paises/', { params: { page_size: 200 } }),
        api.get('/clientes/departamentos/', { params: { page_size: 500 } }),
        api.get('/clientes/ciudades/', { params: { page_size: 1000 } }),
      ])
      setPaises(p.data.results ?? p.data ?? [])
      setDepartamentos(d.data.results ?? d.data ?? [])
      setCiudades(c.data.results ?? c.data ?? [])
    } catch { toast.error('Error al cargar ubicaciones') }
    finally { setLoading(false) }
  }, [])

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => { load() }, [load])

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (paisSel === null && paises.length > 0) setPaisSel(paises[0].id_pais)
  }, [paises, paisSel])

  const departamentosDelPais = useMemo(
    () => departamentos.filter(d => d.pais === paisSel),
    [departamentos, paisSel],
  )
  const ciudadesDelDepto = useMemo(
    () => ciudades.filter(c => c.departamento === deptoSel),
    [ciudades, deptoSel],
  )

  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (deptoSel !== null && !departamentosDelPais.some(d => d.id_departamento === deptoSel)) setDeptoSel(null)
  }, [departamentosDelPais, deptoSel])

  const openPais = useCallback((p?: Pais) => {
    setNombreForm(p ? p.nombre : '')
    setModal({ nivel: 'pais', editing: p ?? null })
  }, [])

  const openDepartamento = useCallback((d?: Departamento) => {
    setNombreForm(d ? d.nombre : '')
    setPaisForm(d ? (d.pais ?? '') : (paisSel ?? ''))
    setModal({ nivel: 'departamento', editing: d ?? null })
  }, [paisSel])

  const openCiudad = useCallback((c?: Ciudad) => {
    setNombreForm(c ? c.nombre : '')
    setDeptoForm(c ? (c.departamento ?? '') : (deptoSel ?? ''))
    setModal({ nivel: 'ciudad', editing: c ?? null })
  }, [deptoSel])

  const save = useCallback(async () => {
    if (!modal) return
    if (!nombreForm.trim()) { toast.error('Ingresá el nombre'); return }
    if (modal.nivel === 'departamento' && !paisForm) { toast.error('Elegí el país'); return }
    if (modal.nivel === 'ciudad' && !deptoForm) { toast.error('Elegí el departamento'); return }

    setSaving(true)
    try {
      if (modal.nivel === 'pais') {
        const payload = { nombre: nombreForm.trim() }
        if (modal.editing) await api.put(`/clientes/paises/${modal.editing.id_pais}/`, payload)
        else await api.post('/clientes/paises/', payload)
        toast.success(modal.editing ? 'País actualizado' : 'País creado')
      } else if (modal.nivel === 'departamento') {
        const payload = { nombre: nombreForm.trim(), pais: Number(paisForm) }
        if (modal.editing) await api.put(`/clientes/departamentos/${modal.editing.id_departamento}/`, payload)
        else await api.post('/clientes/departamentos/', payload)
        toast.success(modal.editing ? 'Departamento actualizado' : 'Departamento creado')
      } else {
        const payload = { nombre: nombreForm.trim(), departamento: Number(deptoForm) }
        if (modal.editing) await api.put(`/clientes/ciudades/${modal.editing.id_ciudad}/`, payload)
        else await api.post('/clientes/ciudades/', payload)
        toast.success(modal.editing ? 'Ciudad actualizada' : 'Ciudad creada')
      }
      setModal(null)
      load()
    } catch (err) { toast.error(extractErrorMessage(err)) }
    finally { setSaving(false) }
  }, [modal, nombreForm, paisForm, deptoForm, load])

  const modalTitle =
    modal?.nivel === 'pais' ? (modal.editing ? 'Editar País' : 'Nuevo País')
    : modal?.nivel === 'departamento' ? (modal.editing ? 'Editar Departamento' : 'Nuevo Departamento')
    : modal?.nivel === 'ciudad' ? (modal.editing ? 'Editar Ciudad' : 'Nueva Ciudad')
    : ''

  return (
    <>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <UbicacionColumna
          titulo="Países"
          items={paises.map(p => ({ id: p.id_pais, nombre: p.nombre }))}
          seleccionadoId={paisSel}
          onSeleccionar={setPaisSel}
          onNuevo={() => openPais()}
          onEditar={id => openPais(paises.find(p => p.id_pais === id))}
          onEliminar={id => {
            const p = paises.find(x => x.id_pais === id)
            if (p) onDelete({ url: `/clientes/paises/${id}/`, label: p.nombre, reloadFn: load })
          }}
          loading={loading}
          vacio="Sin países cargados"
        />
        <UbicacionColumna
          titulo="Departamentos"
          subtitulo={paisSel ? paises.find(p => p.id_pais === paisSel)?.nombre : undefined}
          items={departamentosDelPais.map(d => ({ id: d.id_departamento, nombre: d.nombre }))}
          seleccionadoId={deptoSel}
          onSeleccionar={setDeptoSel}
          onNuevo={() => openDepartamento()}
          onEditar={id => openDepartamento(departamentos.find(d => d.id_departamento === id))}
          onEliminar={id => {
            const d = departamentos.find(x => x.id_departamento === id)
            if (d) onDelete({ url: `/clientes/departamentos/${id}/`, label: d.nombre, reloadFn: load })
          }}
          loading={loading}
          disabled={!paisSel}
          vacio={paisSel ? 'Sin departamentos en este país' : 'Elegí un país'}
        />
        <UbicacionColumna
          titulo="Ciudades"
          subtitulo={deptoSel ? departamentos.find(d => d.id_departamento === deptoSel)?.nombre : undefined}
          items={ciudadesDelDepto.map(c => ({ id: c.id_ciudad, nombre: c.nombre }))}
          seleccionadoId={null}
          onSeleccionar={() => {}}
          onNuevo={() => openCiudad()}
          onEditar={id => openCiudad(ciudades.find(c => c.id_ciudad === id))}
          onEliminar={id => {
            const c = ciudades.find(x => x.id_ciudad === id)
            if (c) onDelete({ url: `/clientes/ciudades/${id}/`, label: c.nombre, reloadFn: load })
          }}
          loading={loading}
          disabled={!deptoSel}
          vacio={deptoSel ? 'Sin ciudades en este departamento' : 'Elegí un departamento'}
        />
      </div>

      <Modal
        open={!!modal}
        title={modalTitle}
        onOk={save}
        onCancel={() => setModal(null)}
        okText={modal?.editing ? 'Guardar' : 'Crear'}
        confirmLoading={saving}
        width={420}
      >
        <div className="space-y-4">
          {modal?.nivel === 'departamento' && (
            <div>
              <label className={labelClass}>País *</label>
              <select value={paisForm} onChange={e => setPaisForm(e.target.value ? Number(e.target.value) : '')} className={inputClass}>
                <option value="">Seleccionar país...</option>
                {paises.map(p => <option key={p.id_pais} value={p.id_pais}>{p.nombre}</option>)}
              </select>
            </div>
          )}
          {modal?.nivel === 'ciudad' && (
            <div>
              <label className={labelClass}>Departamento *</label>
              <select value={deptoForm} onChange={e => setDeptoForm(e.target.value ? Number(e.target.value) : '')} className={inputClass}>
                <option value="">Seleccionar departamento...</option>
                {departamentos.map(d => (
                  <option key={d.id_departamento} value={d.id_departamento}>
                    {d.nombre}{d.pais_nombre ? ` — ${d.pais_nombre}` : ''}
                  </option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label className={labelClass}>Nombre *</label>
            <input value={nombreForm} onChange={e => setNombreForm(e.target.value)} className={inputClass} autoFocus />
          </div>
        </div>
      </Modal>
    </>
  )
}

// ─── Columna reutilizable ───────────────────────────────────────────────────

function UbicacionColumna({
  titulo, subtitulo, items, seleccionadoId, onSeleccionar, onNuevo, onEditar, onEliminar, loading, disabled, vacio,
}: {
  titulo: string
  subtitulo?: string
  items: { id: number; nombre: string }[]
  seleccionadoId: number | null
  onSeleccionar: (id: number) => void
  onNuevo: () => void
  onEditar: (id: number) => void
  onEliminar: (id: number) => void
  loading: boolean
  disabled?: boolean
  vacio: string
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-100 shadow-sm overflow-hidden flex flex-col">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-100">
        <div>
          <h3 className="text-sm font-semibold text-slate-800">{titulo}</h3>
          {subtitulo && <p className="text-xs text-slate-400 mt-0.5">{subtitulo}</p>}
        </div>
        <Button size="sm" variant="primary" onClick={onNuevo} disabled={disabled}>
          <Plus className="w-3.5 h-3.5" />
        </Button>
      </div>
      <div className="max-h-[420px] overflow-y-auto divide-y divide-slate-50">
        {loading ? (
          <div className="px-4 py-6 text-center text-sm text-slate-400">Cargando…</div>
        ) : items.length === 0 ? (
          <div className="px-4 py-6 text-center text-sm text-slate-400">{vacio}</div>
        ) : items.map(item => (
          <div
            key={item.id}
            onClick={() => onSeleccionar(item.id)}
            className={`group flex items-center gap-2 px-4 py-2.5 cursor-pointer transition-colors ${
              seleccionadoId === item.id ? 'bg-green-50' : 'hover:bg-slate-50'
            }`}
          >
            <span className={`flex-1 text-sm truncate ${seleccionadoId === item.id ? 'text-green-700 font-medium' : 'text-slate-700'}`}>
              {item.nombre}
            </span>
            <div className="flex items-center gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity">
              <button onClick={e => { e.stopPropagation(); onEditar(item.id) }} className="p-1 text-slate-400 hover:text-slate-700 rounded cursor-pointer">
                <Edit2 className="w-3.5 h-3.5" />
              </button>
              <button onClick={e => { e.stopPropagation(); onEliminar(item.id) }} className="p-1 text-slate-400 hover:text-red-600 rounded cursor-pointer">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </div>
            {seleccionadoId === item.id && <ChevronRight className="w-3.5 h-3.5 text-green-600 shrink-0" />}
          </div>
        ))}
      </div>
    </div>
  )
}
