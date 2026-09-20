import api from './api'

export type Decision = 'PROMUEVE' | 'REPITE' | 'CAMBIA' | 'EGRESA' | 'NO_CONTINUA'

export interface LineaPromocion {
  id_promocion_alumno: number
  hijo: number
  hijo_nombre: string
  hijo_activo: boolean
  grado_origen: number | null
  grado_origen_nombre: string | null
  origen_es_ultimo: boolean
  origen_siguiente: number | null
  decision: Decision
  grado_destino: number | null
  grado_destino_nombre: string | null
  motivo: string
  problema: string
}

export interface RequisitosPromocion {
  errores: string[]
  avisos: string[]
  habilitada_desde: string
  puede_aplicar: boolean
  resumen: Record<Decision, number>
}

export interface PromocionAnual {
  id_promocion: number
  anio: number
  estado: 'BORRADOR' | 'APLICADA'
  creada_por_nombre: string | null
  fecha_creacion: string
  aplicada_por_nombre: string | null
  fecha_aplicacion: string | null
  total_alumnos: number
}

export interface PromocionDetalle extends PromocionAnual {
  lineas: LineaPromocion[]
  requisitos: RequisitosPromocion
  resultado?: { actualizadas: number; omitidas: { hijo: string; motivo: string }[] }
  agregados?: number
}

export interface SugerenciaSiguientes {
  asignados: { grado: string; siguiente: string }[]
  pendientes: { grado: string; motivo: string }[]
  ya_configurados: number
  aplicado: boolean
}

const promocionService = {
  listar: () => api.get<{ results: PromocionAnual[] }>('/clientes/promociones/', { params: { page_size: 20 } }),

  detalle: (id: number) => api.get<PromocionDetalle>(`/clientes/promociones/${id}/`),

  generar: (anio: number) => api.post<PromocionDetalle>('/clientes/promociones/', { anio }),

  descartar: (id: number) => api.delete(`/clientes/promociones/${id}/`),

  refrescar: (id: number) => api.post<PromocionDetalle>(`/clientes/promociones/${id}/refrescar/`),

  actualizarLinea: (id: number, linea: number, datos: { decision: Decision; grado_destino?: number | null; motivo?: string }) =>
    api.patch<PromocionDetalle>(`/clientes/promociones/${id}/lineas/${linea}/`, datos),

  actualizarGrupo: (id: number, datos: { grado_origen: number; decision: Decision; grado_destino?: number | null }) =>
    api.post<PromocionDetalle>(`/clientes/promociones/${id}/lineas-masivas/`, datos),

  aplicar: (id: number) => api.post<PromocionDetalle>(`/clientes/promociones/${id}/aplicar/`),

  sugerirSiguientes: (aplicar: boolean) =>
    api.post<SugerenciaSiguientes>('/clientes/grados/sugerir-siguientes/', { aplicar }),
}

export default promocionService
