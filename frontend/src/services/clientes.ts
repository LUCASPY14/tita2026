import api from './api'

export interface Hijo {
  id_hijo:               number
  nombre:                string
  apellido:              string
  nombre_completo?:      string
  grado:                 number | null
  grado_nombre?:         string
  cliente_responsable:   number
  activo:                boolean
}

export interface PaginatedResponse<T> {
  count:    number
  results:  T[]
  next:     string | null
  previous: string | null
}

const clientesService = {
  getHijos: <T = Hijo>(params?: Record<string, unknown>) =>
    api.get<PaginatedResponse<T>>('/clientes/hijos/', { params }),
}

export default clientesService
