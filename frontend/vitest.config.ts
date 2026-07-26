import { defineConfig } from 'vitest/config'
import react from '@vitejs/plugin-react'

export default defineConfig({
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  plugins: [react() as any],
  test: {
    environment: 'jsdom',
    globals: true,
    setupFiles: ['./src/test/setup.ts'],
    exclude: ['**/node_modules/**', '**/e2e/**'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      // Cobertura medida solo en las capas con unit tests dedicados.
      // Páginas (ModoRecreo, CargaSaldo, Login, portal/*) tienen tests unitarios
      // para regresión, pero su cobertura primaria es E2E Playwright — excluirlas
      // del umbral evita que las ~300 arrow functions en JSX diluyan la métrica.
      include: [
        'src/components/ui/**',
        'src/services/**',
        'src/store/**',
      ],
      exclude: [
        'src/test/**',
        'src/main.tsx',
        'src/i18n/**',
        'src/components/ui/Combobox.tsx',
        // LanguageSwitcher usa i18n.changeLanguage() — requiere browser real (E2E)
        'src/components/ui/LanguageSwitcher.tsx',
      ],
      thresholds: {
        lines:      85,
        statements: 85,
        branches:   85,
        functions:  85,
      },
    },
  },
})
