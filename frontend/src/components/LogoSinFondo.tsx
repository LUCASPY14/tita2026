import { useEffect, useRef } from 'react'

interface Props {
  src: string
  alt: string
  className?: string
}

/**
 * Renderiza un logo "flotando" sin caja visible detrás, sin importar el
 * color de fondo de la página. El PNG original tiene un fondo sólido (no
 * transparente); acá lo pintamos de blanco puro por canvas y usamos
 * mix-blend-mode:multiply — blanco × cualquier color = ese mismo color,
 * así el rectángulo desaparece de verdad (no solo "se parece" al fondo).
 */
export default function LogoSinFondo({ src, alt, className }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const img = new Image()
    img.onload = () => {
      const canvas = canvasRef.current
      if (!canvas) return
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      canvas.width  = img.naturalWidth
      canvas.height = img.naturalHeight
      ctx.drawImage(img, 0, 0)
      const w = canvas.width, h = canvas.height
      const imageData = ctx.getImageData(0, 0, w, h)
      const { data } = imageData

      // Muestrear color de fondo desde la esquina superior-izquierda
      const bgR = data[0], bgG = data[1], bgB = data[2]
      const TOL = 28  // tolerancia de color para detectar el fondo

      const isBg = (i: number) =>
        Math.abs(data[i] - bgR) < TOL &&
        Math.abs(data[i + 1] - bgG) < TOL &&
        Math.abs(data[i + 2] - bgB) < TOL

      // BFS flood-fill desde los 4 bordes: marca solo el fondo EXTERIOR.
      // El interior del contorno del logo no es alcanzable desde los bordes.
      const visited = new Uint8Array(w * h)
      const queue: number[] = []

      const seed = (px: number) => {
        if (!visited[px] && isBg(px * 4)) { visited[px] = 1; queue.push(px) }
      }
      for (let x = 0; x < w; x++) { seed(x); seed((h - 1) * w + x) }
      for (let y = 0; y < h; y++) { seed(y * w); seed(y * w + w - 1) }

      for (let head = 0; head < queue.length; head++) {
        const px = queue[head]
        const x = px % w, y = (px / w) | 0
        if (y > 0)     seed(px - w)
        if (y < h - 1) seed(px + w)
        if (x > 0)     seed(px - 1)
        if (x < w - 1) seed(px + 1)
      }

      // Fondo exterior → blanco puro. Con mix-blend-mode:multiply en CSS,
      // blanco × fondo-página = fondo-página (el rectángulo desaparece).
      for (let px = 0; px < w * h; px++) {
        if (visited[px]) {
          const i = px * 4
          data[i] = 255; data[i + 1] = 255; data[i + 2] = 255; data[i + 3] = 255
        }
      }
      ctx.putImageData(new ImageData(data, canvas.width, canvas.height), 0, 0)
    }
    img.src = src
  }, [src])

  return <canvas ref={canvasRef} aria-label={alt} className={className} />
}
