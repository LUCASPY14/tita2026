import { useEffect, useState } from 'react'
import api from '../services/api'

/**
 * Trae una imagen protegida (requiere JWT) vía la instancia de axios ya
 * autenticada, y la expone como blob URL para usar en <img src>.
 * Devuelve null mientras carga, si no hay url, o si el pedido falla
 * (403/404) — el componente que la usa debe mostrar un placeholder en
 * ese caso.
 */
export function useAuthenticatedImage(url: string | null | undefined): string | null {
  const [blobUrl, setBlobUrl] = useState<string | null>(null)

  useEffect(() => {
    // Limpiar sincrónicamente cuando la url pasa a null (sin foto / permiso
    // denegado) es intencional: no hay nada async que esperar en ese caso.
    if (!url) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setBlobUrl(null)
      return
    }
    let objectUrl: string | null = null
    let cancelled = false

    api.get(url, { responseType: 'blob' })
      .then(({ data }) => {
        if (cancelled) return
        objectUrl = URL.createObjectURL(data as Blob)
        setBlobUrl(objectUrl)
      })
      .catch(() => { if (!cancelled) setBlobUrl(null) })

    return () => {
      cancelled = true
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [url])

  return blobUrl
}
