import { useEffect, useState } from 'react'
import api from '../services/api'

export interface DatosEmpresaPublico {
  razon_social: string
  ruc: string
  email: string
  telefono: string
}

const VACIO: DatosEmpresaPublico = { razon_social: '', ruc: '', email: '', telefono: '' }

/** Razón social, RUC, email y teléfono — público, sin requerir sesión (portal). */
export function useDatosEmpresaPublico(): DatosEmpresaPublico | null {
  const [datos, setDatos] = useState<DatosEmpresaPublico | null>(null)

  useEffect(() => {
    api.get<DatosEmpresaPublico>('/contabilidad/datos-empresa/publico/')
      .then(({ data }) => setDatos(data))
      .catch(() => setDatos(VACIO))
  }, [])

  return datos
}
