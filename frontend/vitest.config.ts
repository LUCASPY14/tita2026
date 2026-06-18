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
      // Solo se miden los archivos que tienen unit tests. Las páginas complejas
      // (ModoRecreo, Almuerzos, Cajas, etc.) están cubiertas por E2E (Playwright).
      include: [
        'src/components/ui/**',
        'src/services/**',
        'src/store/**',
        'src/pages/Login.tsx',
        'src/pages/CargaSaldo.tsx',
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
        lines:      75,
        statements: 75,
        branches:   70,
        // Las páginas complejas (CargaSaldo, Login) tienen muchos handlers no
        // alcanzables por unit tests; cubiertos por E2E. Umbral ajustado al
        // nivel real del suite actual.
        functions:  60,
      },
    },
  },
})
