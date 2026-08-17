import api from './api'

// Tipo base — campos garantizados en toda respuesta de /core/tarjetas/
export interface TarjetaBase {
  nro_tarjeta:  string
  hijo:         number
  hijo_nombre:  string
  hijo_grado:   string | null
  saldo_actual: number | string
  estado:       'ACTIVA' | 'BLOQUEADA' | 'INACTIVA'
}

export interface MovimientoTarjeta {
  id:               number
  tarjeta:          string
  tarjeta_nro:      string
  tipo:             string
  monto:            number | string
  saldo_anterior:   number | string
  saldo_resultante: number | string
  descripcion:      string
  fecha_creacion:   string
}

export interface CargaSaldo {
  id:                 number
  tarjeta:            string
  cliente_origen:     number | null
  monto_cargado:      number | string
  metodo_pago:        string
  estado:             'PENDIENTE' | 'CONFIRMADA' | 'RECHAZADA' | 'CANCELADA'
  responsable:        number | null
  fecha_carga:        string
  fecha_confirmacion: string | null
}

export interface Paginated<T> {
  count:    number
  results:  T[]
  next:     string | null
  previous: string | null
}

const tarjetasService = {
  // Genérico: la página pasa su propio tipo local para obtener tipado correcto
  buscar: <T = TarjetaBase>(search: string) =>
    api.get<Paginated<T>>('/core/tarjetas/', { params: { search } }),

  listar: <T = TarjetaBase>(params?: Record<string, unknown>) =>
    api.get<Paginated<T>>('/core/tarjetas/', { params }),

  getByNro: <T = TarjetaBase>(nro: string) =>
    api.get<T>(`/core/tarjetas/${nro}/`),

  crear: (data: Record<string, unknown>) =>
    api.post<TarjetaBase>('/core/tarjetas/', data),

  actualizar: (nro: string, data: Record<string, unknown>) =>
    api.patch<TarjetaBase>(`/core/tarjetas/${nro}/`, data),

  bloquear: <T = TarjetaBase>(nro: string) =>
    api.post<T>(`/core/tarjetas/${nro}/bloquear/`),

  activar: <T = TarjetaBase>(nro: string) =>
    api.post<T>(`/core/tarjetas/${nro}/activar/`),

  getMovimientos: <T = MovimientoTarjeta>(nro_tarjeta: string, page_size = 20) =>
    api.get<Paginated<T>>('/core/movimientos-tarjeta/', {
      params: { tarjeta: nro_tarjeta, page_size },
    }),

  getCargas: <T = CargaSaldo>(nro_tarjeta: string, page_size = 20) =>
    api.get<Paginated<T>>('/core/cargas-saldo/', {
      params: { tarjeta: nro_tarjeta, page_size },
    }),

  crearCarga: (data: { tarjeta: string; monto_cargado: number; metodo_pago: string; referencia?: string; nro_factura?: string }) =>
    api.post<CargaSaldo>('/core/cargas-saldo/', data),

  confirmarCarga: (id: number, nro_factura?: string) =>
    api.post(`/core/cargas-saldo/${id}/confirmar/`, nro_factura ? { nro_factura } : {}),
}

export default tarjetasService
