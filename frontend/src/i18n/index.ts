import i18n from 'i18next'
import { initReactI18next } from 'react-i18next'
import LanguageDetector from 'i18next-browser-languagedetector'

import es from './es.json'
import en from './en.json'

i18n
  .use(LanguageDetector)
  .use(initReactI18next)
  .init({
    resources: {
      es: { translation: es },
      en: { translation: en },
    },
    fallbackLng: 'es',
    // 'languageOnly' normalizes regional variants: 'es-PY' → 'es', 'en-US' → 'en'
    // Avoids supportedLngs strict-filtering rejecting regional codes in i18next v25
    load: 'languageOnly',
    interpolation: {
      escapeValue: false, // React already escapes
    },
    detection: {
      order: ['localStorage', 'navigator'],
      caches: ['localStorage'],
      lookupLocalStorage: 'cantina_lang',
    },
  })

export default i18n
