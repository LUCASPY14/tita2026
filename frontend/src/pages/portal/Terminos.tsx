import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ShieldCheck, Mail, Phone, ArrowLeft } from 'lucide-react'
import api from '../../services/api'
import LogoSinFondo from '../../components/LogoSinFondo'

const CONTACTO_EMAIL = 'admin@cantinatita.com'
const CONTACTO_TELEFONO = '+595 981 410 938'

interface DatosEmpresaPublico {
  razon_social: string
  ruc: string
}

function Seccion({ numero, titulo, children }: { numero: number; titulo: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h2 className="text-base font-bold text-slate-800">{numero}. {titulo}</h2>
      <div className="text-sm text-slate-600 leading-relaxed space-y-2">{children}</div>
    </section>
  )
}

export default function PortalTerminos() {
  const [empresa, setEmpresa] = useState<DatosEmpresaPublico | null>(null)

  useEffect(() => {
    api.get<DatosEmpresaPublico>('/contabilidad/datos-empresa/publico/')
      .then(({ data }) => setEmpresa(data))
      .catch(() => setEmpresa(null))
  }, [])

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-2xl mx-auto px-4 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <LogoSinFondo src="/logo-cantina.png" alt="Cantina Tita" className="h-12 w-auto mix-blend-multiply" />
            <p className="text-xs text-slate-400 hidden sm:block">Portal de Padres</p>
          </div>
          <Link
            to="/portal/login"
            className="flex items-center gap-1.5 text-sm text-green-600 hover:text-green-700 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" />
            Volver
          </Link>
        </div>
      </header>

      <main className="max-w-2xl mx-auto px-4 py-8">
        <div className="bg-white rounded-2xl border border-slate-100 shadow-sm p-6 sm:p-8 space-y-6">
          <div className="text-center mb-2">
            <div className="inline-flex items-center justify-center w-14 h-14 rounded-full bg-green-100 mb-3">
              <ShieldCheck className="w-7 h-7 text-green-600" />
            </div>
            <h1 className="text-xl font-bold text-slate-900">Términos y Condiciones de Uso</h1>
            <p className="text-sm text-slate-400 mt-1">Portal de Padres — Cantina Tita</p>
          </div>

          <Seccion numero={1} titulo="Objeto y aceptación">
            <p>
              El objeto de los presentes Términos y Condiciones es regular el acceso y uso del Portal de Padres
              de Cantina Tita (en adelante, "la Plataforma"), una aplicación web destinada a los padres, madres y
              responsables legales (en adelante, "el Usuario") de alumnos del colegio, que permite consultar el
              saldo de la tarjeta escolar y la cuenta de almuerzo de sus hijos/as, recargar saldo, visualizar el
              historial de consumos y facturas, y gestionar notificaciones. Al acceder y utilizar la Plataforma,
              el Usuario acepta de forma plena e incondicional estos Términos y Condiciones. El uso continuado de
              la Plataforma implica la aceptación tácita de cualquier modificación posterior a los mismos.
            </p>
          </Seccion>

          <Seccion numero={2} titulo="Medios de pago admitidos">
            <p>Los medios de pago habilitados en la Plataforma para la recarga de saldo son:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Tarjetas de crédito y débito (Visa y Mastercard).</li>
              <li>Código QR generado por la Plataforma.</li>
              <li>Tarjeta guardada (con token), para recargas posteriores sin reingresar los datos de la tarjeta.</li>
            </ul>
          </Seccion>

          <Seccion numero={3} titulo="Bancard — procesamiento de pagos">
            <p>
              El procesamiento de todos los pagos y el enrolamiento de tarjetas se realiza a través de{' '}
              <strong>Bancard</strong>, la procesadora de pagos autorizada. Cantina Tita no recibe, almacena ni
              tiene acceso a los datos completos de la tarjeta del Usuario (número, fecha de vencimiento, CVV) —
              dichos datos son entregados directamente a Bancard a través de su plataforma segura de checkout.
              Cantina Tita únicamente recibe de Bancard una confirmación del resultado de la transacción y, en
              caso de que el Usuario opte por guardar la tarjeta, un token de referencia que no permite
              reconstruir los datos originales de la tarjeta.
            </p>
          </Seccion>

          <Seccion numero={4} titulo="Definiciones">
            <ul className="list-disc pl-5 space-y-1">
              <li><strong>Usuario:</strong> el padre, madre o responsable legal registrado en la Plataforma.</li>
              <li><strong>Alumno/a:</strong> el/la hijo/a del Usuario, vinculado a su cuenta por la administración del colegio.</li>
              <li><strong>Cuenta:</strong> el acceso individual del Usuario a la Plataforma, de uso personal e intransferible.</li>
              <li><strong>Tarjeta escolar:</strong> la tarjeta con la que el/la alumno/a realiza consumos en la cantina.</li>
              <li><strong>Enrolamiento:</strong> el proceso de registro seguro de una tarjeta de pago a través de Bancard.</li>
            </ul>
          </Seccion>

          <Seccion numero={5} titulo="Registro y alta de cuenta">
            <p>
              El alta de la cuenta del Usuario en el Portal de Padres es realizada por la administración de
              Cantina Tita. El Usuario recibe credenciales iniciales (usuario y contraseña provisoria) y debe
              cambiar la contraseña en su primer ingreso. El Usuario es responsable de mantener la
              confidencialidad de sus credenciales y de la verificación en dos pasos (código de aplicación
              autenticadora o huella/Face ID) requerida para acceder a la Plataforma, así como de notificar a
              Cantina Tita cualquier uso no autorizado de su cuenta.
            </p>
          </Seccion>

          <Seccion numero={6} titulo="Uso de la Plataforma">
            <p>A través de la Plataforma, el Usuario podrá:</p>
            <ul className="list-disc pl-5 space-y-1">
              <li>Consultar el saldo de la tarjeta escolar y de la cuenta corriente de almuerzo de sus hijos/as.</li>
              <li>Recargar saldo mediante los medios de pago habilitados (Sección 2).</li>
              <li>Consultar el historial de consumos y descargar facturas.</li>
              <li>Recibir notificaciones sobre saldo bajo, vencimientos y novedades.</li>
            </ul>
            <p>
              Las recargas realizadas a través de la Plataforma se acreditan de forma inmediata una vez
              confirmado el pago por Bancard. En caso de que una recarga sea rechazada o falle, el monto no
              debitado no genera ningún cargo al Usuario.
            </p>
          </Seccion>

          <Seccion numero={7} titulo="Reembolsos">
            <p>
              En caso de que se detecte un error en el monto efectivamente pagado por el Usuario (por ejemplo,
              un cobro por un importe distinto al de la recarga solicitada), y una vez verificado dicho error por
              Cantina Tita, la devolución del importe correspondiente se realizará mediante transferencia
              bancaria a una cuenta a nombre del Usuario. El Usuario deberá comunicar el reclamo a través de los
              canales de Atención al Usuario (Sección 8), indicando la fecha, el monto y el medio de pago
              utilizado en la operación observada.
            </p>
          </Seccion>

          <Seccion numero={8} titulo="Atención al Usuario">
            <p>Para consultas, reclamos o inconvenientes relacionados con la Plataforma, el Usuario puede contactar a Cantina Tita a través de:</p>
            <div className="flex flex-col gap-2 pt-1">
              <a href={`mailto:${CONTACTO_EMAIL}`} className="flex items-center gap-2 text-green-700 hover:underline w-fit">
                <Mail className="w-4 h-4" /> {CONTACTO_EMAIL}
              </a>
              <a href={`tel:${CONTACTO_TELEFONO.replace(/\s/g, '')}`} className="flex items-center gap-2 text-green-700 hover:underline w-fit">
                <Phone className="w-4 h-4" /> {CONTACTO_TELEFONO}
              </a>
            </div>
          </Seccion>

          <Seccion numero={9} titulo="Seguridad">
            <p>
              Cantina Tita advierte al Usuario sobre la existencia de intentos de fraude (phishing, suplantación
              de identidad, etc.) que buscan obtener credenciales o datos de pago. Cantina Tita nunca solicitará
              al Usuario su contraseña, código de verificación en dos pasos, ni los datos completos de su tarjeta
              por teléfono, correo electrónico o mensajería. Es responsabilidad del Usuario no compartir esta
              información con terceros.
            </p>
          </Seccion>

          <Seccion numero={10} titulo="Disponibilidad del servicio">
            <p>
              Cantina Tita no garantiza el acceso ininterrumpido a la Plataforma y no será responsable por
              fallas, indisponibilidad o demoras originadas en Internet, en los servidores, o en la plataforma de
              Bancard, ajenas a su control directo. Ante cualquier inconveniente, se procurará restablecer el
              servicio a la brevedad posible.
            </p>
          </Seccion>

          <Seccion numero={11} titulo="Propiedad intelectual">
            <p>
              La Plataforma, su nombre, logotipos y contenidos son propiedad de Cantina Tita y se encuentran
              protegidos por la legislación aplicable en materia de propiedad intelectual. Queda prohibida su
              reproducción, modificación o distribución sin autorización expresa.
            </p>
          </Seccion>

          <Seccion numero={12} titulo="Modificaciones">
            <p>
              Cantina Tita podrá modificar estos Términos y Condiciones en cualquier momento. Las modificaciones
              serán publicadas en la Plataforma y entrarán en vigencia desde su publicación. El uso continuado de
              la Plataforma luego de una modificación implica su aceptación.
            </p>
          </Seccion>

          <Seccion numero={13} titulo="Datos de la empresa">
            {empresa?.razon_social ? (
              <p>
                <strong>{empresa.razon_social}</strong>{empresa.ruc && <> — RUC {empresa.ruc}</>}
              </p>
            ) : (
              <p className="text-slate-400 italic">Cargando datos de la empresa…</p>
            )}
          </Seccion>
        </div>
      </main>
    </div>
  )
}
