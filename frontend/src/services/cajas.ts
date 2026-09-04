import api from './api'

export interface CierreCaja {
  id_cierre:      number
  caja:           number
  caja_nombre?:   string
  empleado:       number
  monto_inicial:  number
  monto_final:    number | null
  estado:         'ABIERTO' | 'CERRADO'
  fecha_apertura: string
  fecha_cierre:   string | null
}

const cajasService = {
  getMiCaja: <T = CierreCaja>() =>
    api.get<T>('/contabilidad/cierres-caja/mi-caja/'),
}

export default cajasService
