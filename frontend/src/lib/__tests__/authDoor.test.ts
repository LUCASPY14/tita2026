import { describe, it, expect, beforeEach } from 'vitest'
import { setAuthDoor, getAuthDoorRoute } from '../authDoor'

beforeEach(() => {
  localStorage.clear()
})

describe('authDoor', () => {
  it('sin nada guardado, devuelve /login por defecto', () => {
    expect(getAuthDoorRoute()).toBe('/login')
  })

  it('recuerda y devuelve la ruta de cada puerta conocida', () => {
    setAuthDoor('pos')
    expect(getAuthDoorRoute()).toBe('/pos')

    setAuthDoor('cobranzas')
    expect(getAuthDoorRoute()).toBe('/cobranzas')

    setAuthDoor('comedor')
    expect(getAuthDoorRoute()).toBe('/comedor-acceso')

    setAuthDoor('admin')
    expect(getAuthDoorRoute()).toBe('/login')
  })

  it('un valor desconocido en localStorage cae al default', () => {
    localStorage.setItem('auth_door', 'algo-inventado')
    expect(getAuthDoorRoute()).toBe('/login')
  })
})
