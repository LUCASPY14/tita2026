import Combobox from '../../components/ui/Combobox'
import type { Pais, Departamento, Ciudad } from './shared'

interface Props {
  paises: Pais[]
  departamentos: Departamento[]
  ciudades: Ciudad[]
  paisId: number | null
  departamentoId: number | null
  ciudadId: number | null
  onChangePais: (id: number | null) => void
  onChangeDepartamento: (id: number | null) => void
  onChangeCiudad: (id: number | null) => void
}

const labelClass = 'block text-sm font-semibold text-slate-500 uppercase tracking-wide mb-1.5'

/** País → Departamento → Ciudad en cascada — cada nivel se filtra por el
 * elegido en el anterior, y cambiar uno resetea los de abajo. */
export default function SelectorUbicacion({
  paises, departamentos, ciudades, paisId, departamentoId, ciudadId,
  onChangePais, onChangeDepartamento, onChangeCiudad,
}: Props) {
  const departamentosFiltrados = paisId
    ? departamentos.filter(d => d.pais === paisId)
    : departamentos
  const ciudadesFiltradas = departamentoId
    ? ciudades.filter(c => c.departamento === departamentoId)
    : []

  return (
    <div className="grid grid-cols-3 gap-4">
      <div>
        <label className={labelClass}>País</label>
        <Combobox
          options={paises.map(p => ({ value: p.id_pais, label: p.nombre }))}
          value={paisId ?? undefined}
          onChange={(v) => {
            onChangePais(Number(v))
            onChangeDepartamento(null)
            onChangeCiudad(null)
          }}
          filterLocal
          placeholder="Buscar país..."
        />
      </div>
      <div>
        <label className={labelClass}>Departamento</label>
        <Combobox
          options={departamentosFiltrados.map(d => ({ value: d.id_departamento, label: d.nombre }))}
          value={departamentoId ?? undefined}
          onChange={(v) => {
            onChangeDepartamento(Number(v))
            onChangeCiudad(null)
          }}
          filterLocal
          placeholder={paisId ? 'Buscar departamento...' : 'Elegí un país primero'}
        />
      </div>
      <div>
        <label className={labelClass}>Ciudad</label>
        <Combobox
          options={ciudadesFiltradas.map(c => ({ value: c.id_ciudad, label: c.nombre }))}
          value={ciudadId ?? undefined}
          onChange={(v) => onChangeCiudad(Number(v))}
          filterLocal
          placeholder={departamentoId ? 'Buscar ciudad...' : 'Elegí un departamento primero'}
        />
      </div>
    </div>
  )
}
