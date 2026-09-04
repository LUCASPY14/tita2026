import { useEffect, useRef, useState } from 'react'
import toast from 'react-hot-toast'
import { Camera, Upload, X } from 'lucide-react'
import api from '../../services/api'
import Input from '../../components/ui/Input'
import Modal from '../../components/ui/Modal'
import { useAuthenticatedImage } from '../../hooks/useAuthenticatedImage'
import { extractErrorMessage, BLANK_HIJO, type GradoOption, type Hijo, type HijoForm } from './shared'

interface Props {
  open: boolean
  hijo: Hijo | null
  clienteId: number
  onClose: () => void
  onSaved: () => void
}

export default function ModalHijo({ open, hijo, clienteId, onClose, onSaved }: Props) {
  const [form, setForm] = useState<HijoForm>(BLANK_HIJO)
  const [saving, setSaving] = useState(false)
  const [photoFile, setPhotoFile] = useState<File | null>(null)
  const [photoPreview, setPhotoPreview] = useState<string | null>(null)
  const [photoRemoved, setPhotoRemoved] = useState(false)
  const [webcamActive, setWebcamActive] = useState(false)
  const [webcamError, setWebcamError] = useState<string | null>(null)
  const [grados, setGrados] = useState<GradoOption[]>([])
  const videoRef = useRef<HTMLVideoElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    api.get<{ results?: GradoOption[]; id?: number }[]>('/clientes/grados/')
      .then(res => {
        const data = res.data
        const list = Array.isArray(data)
          ? (data as GradoOption[])
          : ((data as { results?: GradoOption[] }).results ?? [])
        setGrados(list.filter(g => g.activo))
      })
      .catch(() => toast.error('Error al cargar grados'))
  }, [])

  useEffect(() => {
    if (!open) { stopWebcam(); return }
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setForm(hijo
      ? {
          nombre: hijo.nombre,
          apellido: hijo.apellido,
          fecha_nacimiento: hijo.fecha_nacimiento ?? '',
          grado: hijo.grado ? String(hijo.grado) : '',
          activo: hijo.activo,
        }
      : BLANK_HIJO
    )
    setPhotoFile(null)
    setPhotoPreview(null)
    setPhotoRemoved(false)
    setWebcamActive(false)
    setWebcamError(null)
  }, [open, hijo])

  // Foto existente (si la hay): se trae aparte porque es un endpoint
  // protegido, no una URL directa. Se apaga si el usuario ya eligió una
  // nueva foto o la quitó explícitamente.
  const existingFotoBlobUrl = useAuthenticatedImage(
    !photoFile && !photoRemoved ? (hijo?.foto_url ?? null) : null
  )
  const displaySrc = photoPreview ?? existingFotoBlobUrl

  useEffect(() => {
    if (webcamActive && videoRef.current && streamRef.current) {
      videoRef.current.srcObject = streamRef.current
    }
  }, [webcamActive])

  function stopWebcam() {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(t => t.stop())
      streamRef.current = null
    }
    setWebcamActive(false)
  }

  async function startWebcam() {
    setWebcamError(null)
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { width: { ideal: 640 }, height: { ideal: 480 }, facingMode: 'user' },
      })
      streamRef.current = stream
      setWebcamActive(true)
    } catch (err) {
      const msg = (err as Error).message ?? ''
      setWebcamError(
        msg.toLowerCase().includes('denied') || msg.toLowerCase().includes('notallowed')
          ? 'Permiso denegado. Habilitá el acceso a la cámara en tu navegador.'
          : 'No se pudo acceder a la cámara.',
      )
    }
  }

  function capturePhoto() {
    const video = videoRef.current
    const canvas = canvasRef.current
    if (!video || !canvas) return
    canvas.width = video.videoWidth || 640
    canvas.height = video.videoHeight || 480
    const ctx = canvas.getContext('2d')
    if (!ctx) return
    ctx.drawImage(video, 0, 0)
    canvas.toBlob((blob) => {
      if (!blob) return
      const file = new File([blob], 'foto_perfil.jpg', { type: 'image/jpeg' })
      setPhotoFile(file)
      setPhotoPreview(URL.createObjectURL(blob))
      stopWebcam()
    }, 'image/jpeg', 0.88)
  }

  function handleFileChange(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setPhotoFile(file)
    setPhotoPreview(URL.createObjectURL(file))
    e.target.value = ''
  }

  function setText(field: keyof HijoForm) {
    return (e: React.ChangeEvent<HTMLInputElement>) =>
      setForm(prev => ({ ...prev, [field]: e.target.value }))
  }

  async function handleSave() {
    if (!form.nombre || !form.apellido) {
      toast.error('Nombre y apellido son obligatorios')
      return
    }
    setSaving(true)
    try {
      if (photoFile) {
        const fd = new FormData()
        fd.append('nombre', form.nombre)
        fd.append('apellido', form.apellido)
        fd.append('activo', String(form.activo))
        fd.append('cliente_responsable', String(clienteId))
        if (form.fecha_nacimiento) fd.append('fecha_nacimiento', form.fecha_nacimiento)
        if (form.grado) fd.append('grado', String(Number(form.grado)))
        fd.append('foto_perfil', photoFile)
        if (hijo) {
          await api.patch(`/clientes/hijos/${hijo.id_hijo}/`, fd)
        } else {
          await api.post('/clientes/hijos/', fd)
        }
      } else {
        const payload = {
          ...form,
          fecha_nacimiento: form.fecha_nacimiento || null,
          grado: form.grado ? Number(form.grado) : null,
          cliente_responsable: clienteId,
        }
        if (hijo) {
          await api.patch(`/clientes/hijos/${hijo.id_hijo}/`, payload)
        } else {
          await api.post('/clientes/hijos/', payload)
        }
      }
      toast.success(hijo ? 'Estudiante actualizado' : 'Estudiante registrado')
      onSaved()
      onClose()
    } catch (err) {
      toast.error(extractErrorMessage(err))
    } finally {
      setSaving(false)
    }
  }

  const initials = `${form.nombre?.[0] ?? ''}${form.apellido?.[0] ?? ''}`.toUpperCase()

  return (
    <Modal
      open={open}
      title={hijo ? 'Editar Estudiante' : 'Nuevo Estudiante'}
      onCancel={() => { stopWebcam(); onClose() }}
      onOk={handleSave}
      okText={hijo ? 'Guardar Cambios' : 'Registrar'}
      confirmLoading={saving}
      width={500}
    >
      <div className="space-y-4">
        <div className="flex items-center gap-4 p-3 bg-slate-50 rounded-xl border border-slate-100">
          <div className="w-20 h-20 rounded-full overflow-hidden bg-blue-100 flex items-center justify-center border-2 border-white shadow shrink-0">
            {displaySrc
              ? <img src={displaySrc} alt="Foto" className="w-full h-full object-cover" />
              : <span className="text-blue-700 font-bold text-xl">{initials || '?'}</span>
            }
          </div>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-slate-600 mb-2">Foto del estudiante</p>
            <div className="flex flex-wrap gap-2">
              <button type="button" onClick={() => fileInputRef.current?.click()}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-slate-700">
                <Upload className="w-3.5 h-3.5" />Archivo
              </button>
              <button type="button" onClick={startWebcam}
                className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium bg-white border border-slate-200 rounded-lg hover:bg-slate-50 transition-colors text-slate-700">
                <Camera className="w-3.5 h-3.5" />Webcam
              </button>
              {displaySrc && (
                <button type="button" onClick={() => { setPhotoFile(null); setPhotoPreview(null); setPhotoRemoved(true) }}
                  className="flex items-center gap-1.5 px-3 py-1.5 text-sm font-medium text-red-600 hover:bg-red-50 border border-red-100 rounded-lg transition-colors">
                  <X className="w-3.5 h-3.5" />Quitar
                </button>
              )}
            </div>
            {webcamError && <p className="text-xs text-red-500 mt-1.5">{webcamError}</p>}
          </div>
          <input ref={fileInputRef} type="file" accept=".jpg,.jpeg,.png,.webp" className="hidden" onChange={handleFileChange} />
        </div>

        {webcamActive && (
          <div className="rounded-xl overflow-hidden border border-slate-200 bg-black">
            <video ref={videoRef} autoPlay playsInline muted className="w-full max-h-60 object-cover" />
            <div className="flex items-center justify-center gap-3 px-3 py-2 bg-slate-900">
              <button type="button" onClick={capturePhoto}
                className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 text-white text-sm font-semibold rounded-lg transition-colors">
                <Camera className="w-4 h-4" />Capturar
              </button>
              <button type="button" onClick={stopWebcam}
                className="px-4 py-2 bg-slate-600 hover:bg-slate-500 text-white text-sm font-medium rounded-lg transition-colors">
                Cancelar
              </button>
            </div>
          </div>
        )}
        <canvas ref={canvasRef} className="hidden" />

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
          <Input label="Nombre *" value={form.nombre} onChange={setText('nombre')} placeholder="Juan" />
          <Input label="Apellido *" value={form.apellido} onChange={setText('apellido')} placeholder="García" />
          <div className="flex flex-col gap-1">
            <label className="text-sm font-medium text-slate-700">Grado</label>
            <select
              value={form.grado}
              onChange={e => setForm(prev => ({ ...prev, grado: e.target.value }))}
              className="w-full px-3 py-2 text-sm border border-slate-200 rounded-lg bg-white text-slate-800 focus:outline-none focus:ring-2 focus:ring-green-500/30 focus:border-green-400"
            >
              <option value="">Sin grado</option>
              {grados.map(g => <option key={g.id_grado} value={String(g.id_grado)}>{g.nombre}</option>)}
            </select>
          </div>
          <Input label="Fecha de Nacimiento" type="date" value={form.fecha_nacimiento} onChange={setText('fecha_nacimiento')} />
        </div>

        <div className="flex items-center gap-3">
          <button
            type="button" role="switch" aria-checked={form.activo}
            onClick={() => setForm(prev => ({ ...prev, activo: !prev.activo }))}
            className={['relative w-10 h-5 rounded-full transition-colors duration-200 focus:outline-none focus:ring-2 focus:ring-green-500/30', form.activo ? 'bg-green-500' : 'bg-slate-200'].join(' ')}
          >
            <span className={['absolute top-0.5 left-0.5 w-4 h-4 bg-white rounded-full shadow-sm transition-transform duration-200', form.activo ? 'translate-x-5' : 'translate-x-0'].join(' ')} />
          </button>
          <span className="text-sm text-slate-700 font-medium">Estudiante {form.activo ? 'activo' : 'inactivo'}</span>
        </div>
      </div>
    </Modal>
  )
}
