import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { describe, it, expect, vi, beforeEach } from 'vitest'

vi.mock('../../../services/api', () => ({
  default: { get: vi.fn(), post: vi.fn(), put: vi.fn() },
}))

vi.mock('react-hot-toast', () => ({
  default: { error: vi.fn(), success: vi.fn() },
}))

import api from '../../../services/api'
import toast from 'react-hot-toast'
import TabConfigAlmuerzo from '../TabConfigAlmuerzo'

const GRADOS = [
  { id_grado: 1, nombre: '1° Grado', nivel: 1, orden: 1, es_ultimo: false, activo: true, siguiente: null, siguiente_nombre: null },
  { id_grado: 9, nombre: '9° Grado', nivel: 9, orden: 9, es_ultimo: true, activo: true, siguiente: null, siguiente_nombre: null },
]

beforeEach(() => {
  vi.clearAllMocks()
})

function mockCarga(config: unknown) {
  vi.mocked(api.get).mockImplementation((url: string) => {
    if (url === '/clientes/grados/') return Promise.resolve({ data: { results: GRADOS } })
    if (url === '/almuerzos/configuracion/') return Promise.resolve({ data: { results: config ? [config] : [] } })
    return Promise.reject(new Error(`url inesperada: ${url}`))
  })
}

describe('TabConfigAlmuerzo', () => {
  it('sin configuración previa muestra "Sin restricción" en ambos selects', async () => {
    mockCarga(null)
    render(<TabConfigAlmuerzo />)
    expect(await screen.findAllByText('Sin restricción')).toHaveLength(2)
  })

  it('con configuración previa precarga los grados guardados', async () => {
    mockCarga({
      id_configuracion_almuerzo: 1, grado_desde: 1, grado_hasta: 9,
      grado_desde_nombre: '1° Grado', grado_hasta_nombre: '9° Grado',
    })
    render(<TabConfigAlmuerzo />)
    await waitFor(() => expect(api.get).toHaveBeenCalledWith('/almuerzos/configuracion/', { params: { page_size: 1 } }))
    const [desde, hasta] = await screen.findAllByRole('combobox')
    expect((desde as HTMLSelectElement).value).toBe('1')
    expect((hasta as HTMLSelectElement).value).toBe('9')
  })

  it('crea la configuración con POST cuando no existía ninguna', async () => {
    mockCarga(null)
    vi.mocked(api.post).mockResolvedValue({
      data: { id_configuracion_almuerzo: 1, grado_desde: 1, grado_hasta: 9, grado_desde_nombre: '1° Grado', grado_hasta_nombre: '9° Grado' },
    } as never)
    render(<TabConfigAlmuerzo />)
    const [desde, hasta] = await screen.findAllByRole('combobox')
    await userEvent.selectOptions(desde, '1')
    await userEvent.selectOptions(hasta, '9')
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }))
    await waitFor(() => {
      expect(api.post).toHaveBeenCalledWith('/almuerzos/configuracion/', { grado_desde: 1, grado_hasta: 9 })
    })
    expect(toast.success).toHaveBeenCalledWith('Configuración guardada')
  })

  it('edita la configuración existente con PUT', async () => {
    mockCarga({
      id_configuracion_almuerzo: 7, grado_desde: 1, grado_hasta: 9,
      grado_desde_nombre: '1° Grado', grado_hasta_nombre: '9° Grado',
    })
    vi.mocked(api.put).mockResolvedValue({
      data: { id_configuracion_almuerzo: 7, grado_desde: null, grado_hasta: null, grado_desde_nombre: null, grado_hasta_nombre: null },
    } as never)
    render(<TabConfigAlmuerzo />)
    const [desde, hasta] = await screen.findAllByRole('combobox')
    await waitFor(() => expect((desde as HTMLSelectElement).value).toBe('1'))
    await userEvent.selectOptions(desde, '')
    await userEvent.selectOptions(hasta, '')
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }))
    await waitFor(() => {
      expect(api.put).toHaveBeenCalledWith('/almuerzos/configuracion/7/', { grado_desde: null, grado_hasta: null })
    })
  })

  it('exige los dos extremos del rango, no solo uno', async () => {
    mockCarga(null)
    render(<TabConfigAlmuerzo />)
    const [desde] = await screen.findAllByRole('combobox')
    await userEvent.selectOptions(desde, '1')
    await userEvent.click(screen.getByRole('button', { name: /Guardar/i }))
    expect(toast.error).toHaveBeenCalledWith('Definí los dos extremos del rango, o dejalos vacíos los dos')
    expect(api.post).not.toHaveBeenCalled()
  })
})
