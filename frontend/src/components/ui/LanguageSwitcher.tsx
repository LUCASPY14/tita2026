import { useTranslation } from 'react-i18next'

const LANGS = [
  { code: 'es', label: 'ES', flag: '🇵🇾' },
  { code: 'en', label: 'EN', flag: '🇺🇸' },
]

export default function LanguageSwitcher({ className = '' }: { className?: string }) {
  const { i18n } = useTranslation()
  const current = i18n.resolvedLanguage ?? 'es'

  return (
    <div className={`flex items-center gap-1 ${className}`}>
      {LANGS.map(({ code, label, flag }) => (
        <button
          key={code}
          onClick={() => i18n.changeLanguage(code)}
          title={flag}
          className={`px-2 py-1 rounded text-xs font-semibold transition-colors cursor-pointer ${
            current === code
              ? 'bg-green-600 text-white'
              : 'bg-slate-100 text-slate-500 hover:bg-slate-200'
          }`}
        >
          {label}
        </button>
      ))}
    </div>
  )
}
