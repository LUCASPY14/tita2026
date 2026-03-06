// cypress/support/commands.ts
/// <reference types="cypress" />

// Comando para login
Cypress.Commands.add('login', (email: string, password: string) => {
  cy.request({
    method: 'POST',
    url: `${Cypress.env('API_BASE_URL')}/auth/login/`,
    body: {
      email,
      password
    }
  }).then((response) => {
    window.localStorage.setItem('authToken', response.body.access)
    window.localStorage.setItem('refreshToken', response.body.refresh)
    window.localStorage.setItem('user', JSON.stringify(response.body.user))
  })
})

// Comando para logout
Cypress.Commands.add('logout', () => {
  window.localStorage.removeItem('authToken')
  window.localStorage.removeItem('refreshToken')
  window.localStorage.removeItem('user')
  cy.clearCookies()
})

// Comando para verificar que un elemento está visible y clickeable
Cypress.Commands.add('clickWhenReady', (selector: string) => {
  cy.get(selector)
    .should('be.visible')
    .should('not.be.disabled')
    .click()
})

// Comando para esperar a que termine la carga
Cypress.Commands.add('waitForLoad', () => {
  cy.get('[data-testid="loading"]', { timeout: 10000 }).should('not.exist')
})

// Comando para crear tarjeta de prueba
Cypress.Commands.add('createTestCard', (cardNumber: string, balance: number) => {
  return cy.request({
    method: 'POST',
    url: `${Cypress.env('API_BASE_URL')}/tarjetas/`,
    headers: {
      'Authorization': `Bearer ${window.localStorage.getItem('authToken')}`
    },
    body: {
      nro_tarjeta: cardNumber,
      saldo_actual: balance,
      estado: 'activa',
      fecha_creacion: new Date().toISOString(),
      limite_credito: 100000
    }
  })
})

// Comando para verificar notificación de éxito
Cypress.Commands.add('verifySuccessToast', (message?: string) => {
  cy.get('[data-testid="toast-success"]', { timeout: 5000 })
    .should('be.visible')
  if (message) {
    cy.get('[data-testid="toast-success"]').should('contain.text', message)
  }
})

// Comando para verificar notificación de error
Cypress.Commands.add('verifyErrorToast', (message?: string) => {
  cy.get('[data-testid="toast-error"]', { timeout: 5000 })
    .should('be.visible')
  if (message) {
    cy.get('[data-testid="toast-error"]').should('contain.text', message)
  }
})

// Extend Cypress namespace to include custom commands
declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Login command
       * @param email User email
       * @param password User password
       */
      login(email: string, password: string): Chainable<void>
      
      /**
       * Logout command
       */
      logout(): Chainable<void>
      
      /**
       * Click when element is ready
       * @param selector CSS selector
       */
      clickWhenReady(selector: string): Chainable<void>
      
      /**
       * Wait for loading to finish
       */
      waitForLoad(): Chainable<void>
      
      /**
       * Create test card
       * @param cardNumber Card number
       * @param balance Initial balance
       */
      createTestCard(cardNumber: string, balance: number): Chainable<any>
      
      /**
       * Verify success toast notification
       * @param message Optional message to verify
       */
      verifySuccessToast(message?: string): Chainable<void>
      
      /**
       * Verify error toast notification
       * @param message Optional message to verify
       */
      verifyErrorToast(message?: string): Chainable<void>
    }
  }
}

export {}