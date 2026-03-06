// cypress/support/e2e.ts
// Comando para cargar comandos comunes de Cypress
import './commands'

// Configuraciones globales
Cypress.on('uncaught:exception', (err, runnable) => {
  // returning false here prevents Cypress from failing the test
  // Útil para errores de terceros que no afectan nuestros tests
  if (err.message.includes('Script error')) {
    return false
  }
  if (err.message.includes('Non-Error promise rejection captured')) {
    return false
  }
  return true
})

// Configurar viewport por defecto
beforeEach(() => {
  cy.viewport(1280, 720)
})

// Limpiar localStorage entre tests
beforeEach(() => {
  cy.clearLocalStorage()
  cy.clearCookies()
})