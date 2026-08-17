import { Link } from 'react-router-dom'
import { Users, LayoutDashboard, ShoppingCart, HandCoins, Eye, Smartphone, Bell, ArrowRight } from 'lucide-react'
import LogoSinFondo from '../components/LogoSinFondo'

const ACCESS_CARDS = [
  {
    id: 'padres',
    title: 'Portal de Padres',
    description: 'Consultá el saldo, recargá la cuenta y revisá el historial de consumos de tu hijo.',
    icon: Users,
    href: '/portal/login',
    accent: '#16a34a',
    iconStyle: { background: '#f0fdf4', color: '#16a34a' },
  },
  {
    id: 'admin',
    title: 'Administración',
    description: 'Gestión completa: ventas, reportes, clientes, productos, caja y configuración.',
    icon: LayoutDashboard,
    href: '/login',
    accent: '#ea580c',
    iconStyle: { background: '#fff7ed', color: '#ea580c' },
  },
  {
    id: 'caja',
    title: 'Caja / POS',
    description: 'Punto de venta optimizado para el recreo. Rápido, táctil y sin complicaciones.',
    icon: ShoppingCart,
    href: '/pos',
    accent: '#d97706',
    iconStyle: { background: '#fffbeb', color: '#d97706' },
  },
  {
    id: 'cobranzas',
    title: 'Cobranzas',
    description: 'Gestioná cuentas corrientes, registrá cobros y seguí la deuda de cada cliente.',
    icon: HandCoins,
    href: '/cobranzas',
    accent: '#2563eb',
    iconStyle: { background: '#eff6ff', color: '#2563eb' },
  },
]

const FEATURES = [
  { icon: Eye,        label: 'Sabés lo que come tu hijo',     color: '#f97316' },
  { icon: Smartphone, label: 'Recargá desde tu celular',      color: '#2563eb' },
  { icon: Bell,       label: 'Notificaciones instantáneas',   color: '#16a34a' },
]

export default function Landing() {
  return (
    <>
      <style>{`
        * { font-family: 'Nunito', system-ui, sans-serif; box-sizing: border-box; }

        @keyframes float {
          0%, 100% { transform: translateY(0px) rotate(-1deg); }
          50%       { transform: translateY(-14px) rotate(1deg); }
        }
        @media (prefers-reduced-motion: no-preference) {
          .lf { animation: float 5.5s ease-in-out infinite; }
        }

        /* ---------- tokens ---------- */
        :root {
          --bg:       #fffbf0;
          --bg2:      #ffffff;
          --surface:  #ffffff;
          --border:   #f0ebe0;
          --text:     #1c1a15;
          --muted:    #78716c;
          --faint:    #a8a29e;
          --hero-bg:  radial-gradient(ellipse 110% 120% at 50% -10%, #fef3c7 0%, #fef9f0 55%, #fffbf0 100%);
          --badge-bg: #fff7ed;
          --badge-bd: #fed7aa;
          --badge-tx: #c2410c;
          --num-col:  #f97316;
          --scroll-tx:#ea580c;
          --scroll-bg:rgba(249,115,22,.1);
          --card-bg:  #ffffff;
          --card-bd:  #f0ebe0;
          --card-sh:  0 2px 8px rgba(0,0,0,.06);
          --card-sh2: 0 10px 28px rgba(0,0,0,.11);
          --foot-bg:  #ffffff;
          --foot-bd:  #f0ebe0;
          --lg-ink:   #a8461e;
        }
        @media (prefers-color-scheme: dark) {
          :root {
            --bg:       #18140e;
            --bg2:      #1f1a11;
            --surface:  #23190e;
            --border:   #2e2419;
            --text:     #f5f0e8;
            --muted:    #a8a29e;
            --faint:    #6b6560;
            --hero-bg:  radial-gradient(ellipse 110% 120% at 50% -10%, #2c1f08 0%, #1c150a 55%, #18140e 100%);
            --badge-bg: rgba(249,115,22,.12);
            --badge-bd: rgba(249,115,22,.25);
            --badge-tx: #fb923c;
            --num-col:  #fb923c;
            --scroll-tx:#fb923c;
            --scroll-bg:rgba(249,115,22,.12);
            --card-bg:  #23190e;
            --card-bd:  #2e2419;
            --card-sh:  0 2px 10px rgba(0,0,0,.3);
            --card-sh2: 0 10px 32px rgba(0,0,0,.4);
            --foot-bg:  #1f1a11;
            --foot-bd:  #2e2419;
            --lg-ink:   #e08256;
          }
        }
        :root[data-theme="light"] {
          --bg:#fffbf0;--bg2:#ffffff;--surface:#ffffff;--border:#f0ebe0;
          --text:#1c1a15;--muted:#78716c;--faint:#a8a29e;
          --hero-bg:radial-gradient(ellipse 110% 120% at 50% -10%,#fef3c7 0%,#fef9f0 55%,#fffbf0 100%);
          --badge-bg:#fff7ed;--badge-bd:#fed7aa;--badge-tx:#c2410c;
          --num-col:#f97316;--scroll-tx:#ea580c;--scroll-bg:rgba(249,115,22,.1);
          --card-bg:#ffffff;--card-bd:#f0ebe0;
          --card-sh:0 2px 8px rgba(0,0,0,.06);--card-sh2:0 10px 28px rgba(0,0,0,.11);
          --foot-bg:#ffffff;--foot-bd:#f0ebe0;
          --lg-ink:#a8461e;
        }
        :root[data-theme="dark"] {
          --bg:#18140e;--bg2:#1f1a11;--surface:#23190e;--border:#2e2419;
          --text:#f5f0e8;--muted:#a8a29e;--faint:#6b6560;
          --hero-bg:radial-gradient(ellipse 110% 120% at 50% -10%,#2c1f08 0%,#1c150a 55%,#18140e 100%);
          --badge-bg:rgba(249,115,22,.12);--badge-bd:rgba(249,115,22,.25);--badge-tx:#fb923c;
          --num-col:#fb923c;--scroll-tx:#fb923c;--scroll-bg:rgba(249,115,22,.12);
          --card-bg:#23190e;--card-bd:#2e2419;
          --card-sh:0 2px 10px rgba(0,0,0,.3);--card-sh2:0 10px 32px rgba(0,0,0,.4);
          --foot-bg:#1f1a11;--foot-bd:#2e2419;
          --lg-ink:#e08256;
        }

        /* ---------- layout ---------- */
        .page { min-height: 100dvh; display: flex; flex-direction: column; background: var(--bg); }

        /* ---------- hero ---------- */
        .hero {
          background: var(--hero-bg);
          padding: 2.25rem 2rem 2rem;
          display: flex; align-items: center; justify-content: center;
          gap: 2.5rem; flex-wrap: wrap;
        }
        .hero-logo { width: clamp(320px, 48vw, 520px); display: block; flex-shrink: 0; mix-blend-mode: multiply; }
        .hero-text { max-width: 420px; }
        .badge {
          display: inline-flex; align-items: center; gap: .375rem;
          background: var(--badge-bg); border: 1.5px solid var(--badge-bd);
          color: var(--badge-tx); font-size: .7rem; font-weight: 800;
          letter-spacing: .09em; text-transform: uppercase;
          padding: .275rem .75rem; border-radius: 999px; margin-bottom: 1rem;
        }
        .hero-num {
          font-size: clamp(3rem, 8vw, 5rem); font-weight: 900;
          color: var(--num-col); line-height: 1; letter-spacing: -.04em;
          margin-bottom: .1rem;
        }
        .hero-num-sub {
          font-size: .7rem; font-weight: 800; color: var(--badge-tx);
          letter-spacing: .14em; text-transform: uppercase; margin-bottom: 1rem;
        }
        .hero-divider {
          width: 2.5rem; height: 3px; border-radius: 99px; margin-bottom: 1rem;
          background: linear-gradient(90deg, #f97316, #fbbf24);
        }
        .hero-title {
          font-size: clamp(1.1rem, 2.8vw, 1.5rem); font-weight: 900;
          color: var(--text); line-height: 1.25; margin: 0 0 .75rem;
          text-wrap: balance;
        }
        .hero-body {
          font-size: clamp(.825rem, 1.8vw, .9375rem); font-weight: 600;
          color: var(--muted); line-height: 1.65; margin: 0;
        }

        /* ---------- divider ---------- */
        .section-div { height: 1px; background: var(--border); }

        /* ---------- cards section ---------- */
        .cards-section {
          flex: 1; background: var(--bg2);
          padding: 1.75rem 1.5rem 1.5rem;
        }
        .cards-inner { max-width: 960px; margin: 0 auto; }
        .cards-label {
          font-size: .75rem; font-weight: 800; letter-spacing: .1em;
          text-transform: uppercase; color: var(--faint);
          text-align: center; margin-bottom: 1.25rem;
        }
        .cards-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
        }
        .card {
          display: flex; flex-direction: column;
          background: var(--card-bg); border: 1px solid var(--card-bd);
          border-radius: 16px; overflow: hidden;
          box-shadow: var(--card-sh);
          text-decoration: none; color: inherit;
          transition: transform .2s ease, box-shadow .2s ease;
        }
        .card:hover { transform: translateY(-5px); box-shadow: var(--card-sh2); }
        .card-bar { height: 4px; width: 100%; display: block; }
        .card-inner { padding: 1.125rem 1.25rem 1.25rem; flex: 1; display: flex; flex-direction: column; }
        .card-icon {
          width: 40px; height: 40px; border-radius: 10px;
          display: flex; align-items: center; justify-content: center;
          margin-bottom: .75rem; flex-shrink: 0;
        }
        .card-title { font-size: .9375rem; font-weight: 800; color: var(--text); margin: 0 0 .375rem; }
        .card-desc  { font-size: .8125rem; font-weight: 600; color: var(--muted); line-height: 1.55; flex: 1; margin: 0 0 1rem; }
        .card-btn {
          display: inline-flex; align-items: center; gap: .3rem;
          font-size: .8rem; font-weight: 800; color: #fff;
          padding: .4rem .875rem; border-radius: 8px; align-self: flex-start;
          transition: filter .15s;
        }
        .card-btn:hover { filter: brightness(.88); }

        /* ---------- features strip ---------- */
        .features {
          background: var(--bg);
          padding: 1rem 1.5rem;
          display: flex; align-items: center; justify-content: center;
          gap: 2rem; flex-wrap: wrap;
        }
        .feature-item {
          display: flex; align-items: center; gap: .5rem;
          font-size: .8rem; font-weight: 700; color: var(--muted);
        }
        .feature-dot {
          width: 28px; height: 28px; border-radius: 50%;
          display: flex; align-items: center; justify-content: center;
          flex-shrink: 0;
        }

        /* ---------- footer ---------- */
        .foot {
          background: var(--foot-bg); border-top: 1px solid var(--foot-bd);
          padding: .875rem 1.5rem;
          display: flex; align-items: center; justify-content: space-between;
          flex-wrap: wrap; gap: .5rem;
        }
        .foot-text { font-size: .75rem; font-weight: 700; color: var(--faint); }
        .lg-signature {
          font-family: 'Caveat', cursive; font-weight: 700; font-size: 1.05rem;
          color: var(--lg-ink); margin-left: .1rem;
        }
        .foot-contacts { display: flex; flex-direction: column; align-items: flex-end; gap: .25rem; }
        .foot-link {
          display: inline-flex; align-items: center; gap: .35rem;
          font-size: .75rem; font-weight: 700; color: var(--faint);
          text-decoration: none; transition: color .15s;
        }
        .foot-link:hover { color: #f97316; }
        .foot-link.wa:hover { color: #16a34a; }

        /* ---------- responsive ---------- */
        @media (max-width: 700px) {
          .hero { flex-direction: column; text-align: center; padding: 2rem 1.25rem 1.75rem; gap: 1.5rem; }
          .hero-logo { width: 210px; }
          .hero-divider { margin-left: auto; margin-right: auto; }
          .cards-grid { grid-template-columns: 1fr; }
          .cards-section { padding: 1.25rem 1rem; }
          .features { gap: 1.25rem; }
          .foot { justify-content: center; text-align: center; }
          .foot-contacts { align-items: center; }
        }
        @media (min-width: 701px) and (max-width: 860px) {
          .cards-grid { grid-template-columns: 1fr 1fr; }
        }
      `}</style>

      <div className="page">

        {/* ── Hero: logo + legado ──────────────────────────────────────────── */}
        <section className="hero">
          <LogoSinFondo
            src="/logo-cantina.png"
            alt="La Cantina de Tita"
            className="lf hero-logo"
          />

          <div className="hero-text">
            <span className="badge">Desde 1995</span>

            <div className="hero-num">30</div>
            <div className="hero-num-sub">años de trayectoria</div>
            <div className="hero-divider" />

            <h1 className="hero-title">
              Tres décadas en el corazón de cada recreo
            </h1>
            <p className="hero-body">
              Vimos crecer a generaciones enteras. Los alumnos de ayer hoy
              traen a sus propios hijos. Seguimos aquí, con el mismo sabor
              y el mismo compromiso de siempre.
            </p>
          </div>
        </section>

        <div className="section-div" />

        {/* ── Tarjetas de acceso ───────────────────────────────────────────── */}
        <section className="cards-section">
          <div className="cards-inner">
            <p className="cards-label">¿Cómo querés acceder?</p>

            <div className="cards-grid">
              {ACCESS_CARDS.map((card) => {
                const Icon = card.icon
                return (
                  <Link key={card.id} to={card.href} className="card">
                    <span className="card-bar" style={{ background: card.accent }} />
                    <div className="card-inner">
                      <div className="card-icon" style={card.iconStyle}>
                        <Icon size={20} />
                      </div>
                      <p className="card-title">{card.title}</p>
                      <p className="card-desc">{card.description}</p>
                      <span className="card-btn" style={{ background: card.accent }}>
                        Ingresar <ArrowRight size={13} />
                      </span>
                    </div>
                  </Link>
                )
              })}
            </div>
          </div>
        </section>

        {/* ── Features strip ───────────────────────────────────────────────── */}
        <div className="section-div" />
        <div className="features">
          {FEATURES.map((f) => {
            const Icon = f.icon
            return (
              <span key={f.label} className="feature-item">
                <span
                  className="feature-dot"
                  style={{ background: f.color + '18', color: f.color }}
                >
                  <Icon size={14} />
                </span>
                {f.label}
              </span>
            )
          })}
        </div>

        {/* ── Footer ───────────────────────────────────────────────────────── */}
        <footer className="foot">
          <span className="foot-text">
            © {new Date().getFullYear()} La Cantina de Tita — cantinatita.com · Desarrollado por{' '}
            <span className="lg-signature">LGservices</span>
          </span>
          <div className="foot-contacts">
            <a href="mailto:admin@cantinatita.com" className="foot-link">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><rect x="2" y="4" width="20" height="16" rx="2"/><path d="m22 7-8.97 5.7a1.94 1.94 0 0 1-2.06 0L2 7"/></svg>
              admin@cantinatita.com
            </a>
            <a href="https://wa.me/595981410938" target="_blank" rel="noopener noreferrer" className="foot-link wa">
              <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 0 1-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 0 1-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 0 1 2.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0 0 12.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 0 0 5.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 0 0-3.48-8.413Z"/></svg>
              +595 981 410 938
            </a>
          </div>
        </footer>

      </div>
    </>
  )
}
