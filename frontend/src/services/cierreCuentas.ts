import api from './api'
import type { Cierre, CierreDetalle, Resolucion, ResumenCierres } from '../pages/cierrecuentas/shared'

export interface Paginado<T> { count: number; results: T[] }

export interface NuevaResolucion {
  tipo: string
  bolsillo_origen: string
  monto: number
  bolsillo_destino?: string
  hijo_destino?: number | null
  metodo_pago?: string
  referencia?: string
  motivo?: string
}

export interface RespuestaResolucion {
  resolucion: Resolucion
  advertencia?: string
}

const cierreCuentasService = {
  listar: (params: Record<string, unknown>) =>
    api.get<Paginado<Cierre>>('/cierre-cuentas/cierres/', { params }),

  detalle: (id: number) => api.get<CierreDetalle>(`/cierre-cuentas/cierres/${id}/`),

  resumen: (anio: number) => api.get<ResumenCierres>('/cierre-cuentas/cierres/resumen/', { params: { anio } }),

  abrirMasivo: (anio: number) =>
    api.post<{ anio: number; creados: number; existentes: number }>('/cierre-cuentas/cierres/abrir-masivo/', { anio }),

  registrar: (id: number, datos: NuevaResolucion) =>
    api.post<RespuestaResolucion>(`/cierre-cuentas/cierres/${id}/resoluciones/`, datos),

  cerrarConSaldo: (id: number, motivo: string) =>
    api.post<CierreDetalle>(`/cierre-cuentas/cierres/${id}/cerrar/`, { motivo }),

  pendientes: (anio: number) =>
    api.get<Paginado<Resolucion>>('/cierre-cuentas/resoluciones/', {
      params: { estado: 'SOLICITADA', cierre__anio: anio, page_size: 100, ordering: 'fecha_solicitud' },
    }),

  aprobar: (id: number) => api.post<RespuestaResolucion>(`/cierre-cuentas/resoluciones/${id}/aprobar/`),

  rechazar: (id: number, motivo: string) =>
    api.post<RespuestaResolucion>(`/cierre-cuentas/resoluciones/${id}/rechazar/`, { motivo }),
}

export default cierreCuentasService
