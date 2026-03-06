// cypress/e2e/recargas/recargas-tarjeta.cy.ts
/// <reference types="cypress" />
describe('Recargas de Tarjeta', () => {
  beforeEach(() => {
    cy.fixture('users').then((users) => {
      cy.login(users.cajero.email, users.cajero.password)
    })
    cy.visit('/recargas')
  })

  afterEach(() => {
    cy.logout()
  })

  it('debe mostrar interfaz de recargas', () => {
    cy.get('[data-testid="recharge-interface"]').should('be.visible')
    cy.get('[data-testid="card-scanner"]').should('be.visible')
    cy.get('[data-testid="payment-methods"]').should('be.visible')
    cy.get('[data-testid="amount-input"]').should('be.visible')
  })

  it('debe validar monto mínimo de recarga', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      
      // Intentar recarga con monto muy bajo
      cy.get('[data-testid="amount-input"]').type('1000')
      cy.get('[data-testid="process-recharge-button"]').click()
      
      // Verificar validación
      cy.get('[data-testid="amount-error"]')
        .should('be.visible')
        .and('contain.text', 'Monto mínimo')
    })
  })

  it('debe procesar recarga en efectivo exitosamente', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      
      cy.waitForLoad()
      
      // Configurar recarga
      cy.get('[data-testid="amount-input"]').clear().type('50000')
      cy.get('[data-testid="payment-method-cash"]').click()
      
      // Procesar recarga
      cy.clickWhenReady('[data-testid="process-recharge-button"]')
      
      // Confirmar recarga
      cy.get('[data-testid="confirm-recharge-modal"]').should('be.visible')
      cy.get('[data-testid="confirm-amount"]').should('contain.text', '50.000')
      cy.get('[data-testid="confirm-button"]').click()
      
      // Verificar éxito
      cy.verifySuccessToast('Recarga procesada exitosamente')
      cy.get('[data-testid="recharge-receipt"]').should('be.visible')
    })
  })

  it('debe procesar recarga con Bancard', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      
      // Configurar recarga Bancard
      cy.get('[data-testid="amount-input"]').clear().type('100000')
      cy.get('[data-testid="payment-method-bancard"]').click()
      
      // Procesar recarga
      cy.clickWhenReady('[data-testid="process-recharge-button"]')
      
      // Simular respuesta de Bancard
      cy.get('[data-testid="bancard-modal"]').should('be.visible')
      cy.get('[data-testid="reference-input"]').type('BANC-123456789')
      cy.get('[data-testid="confirm-bancard-button"]').click()
      
      // Verificar éxito
      cy.verifySuccessToast('Recarga procesada exitosamente')
      cy.get('[data-testid="comission-info"]').should('be.visible')
    })
  })

  it('debe procesar recarga por transferencia con validación', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      
      // Configurar recarga por transferencia (monto alto)
      cy.get('[data-testid="amount-input"]').clear().type('500000')
      cy.get('[data-testid="payment-method-transfer"]').click()
      
      // Agregar comprobante
      cy.get('[data-testid="voucher-input"]').type('TRANSF-123456')
      cy.get('[data-testid="voucher-image"]').selectFile('cypress/fixtures/comprobante.jpg', { force: true })
      
      // Procesar recarga
      cy.clickWhenReady('[data-testid="process-recharge-button"]')
      
      // Verificar requiere validación
      cy.verifySuccessToast('Recarga pendiente de validación')
      cy.get('[data-testid="validation-pending-modal"]').should('be.visible')
    })
  })

  it('debe verificar histórico de recargas de tarjeta', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      
      // Ver histórico
      cy.get('[data-testid="view-history-button"]').click()
      cy.get('[data-testid="recharge-history-modal"]').should('be.visible')
      
      // Verificar columnas de histórico
      cy.get('[data-testid="history-table"]').within(() => {
        cy.get('th').should('contain.text', 'Fecha')
        cy.get('th').should('contain.text', 'Monto')
        cy.get('th').should('contain.text', 'Método')
        cy.get('th').should('contain.text', 'Estado')
      })
    })
  })

  it('debe manejar errores de conexión', () => {
    // Simular error de red
    cy.intercept('POST', '**/api/recargas/', { forceNetworkError: true })
    
    cy.fixture('tarjetas').then((tarjetas) => {
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      
      cy.get('[data-testid="amount-input"]').clear().type('50000')
      cy.get('[data-testid="payment-method-cash"]').click()
      cy.clickWhenReady('[data-testid="process-recharge-button"]')
      cy.get('[data-testid="confirm-button"]').click()
      
      // Verificar manejo de error
      cy.verifyErrorToast('Error de conexión')
      cy.get('[data-testid="retry-button"]').should('be.visible')
    })
  })

  it('debe validar duplicación de recargas', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Primera recarga
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      cy.get('[data-testid="amount-input"]').clear().type('25000')
      cy.get('[data-testid="payment-method-transfer"]').click()
      cy.get('[data-testid="voucher-input"]').type('COMP-DUPLICADO-001')
      cy.clickWhenReady('[data-testid="process-recharge-button"]')
      cy.get('[data-testid="confirm-button"]').click()
      
      // Intentar segunda recarga con mismo comprobante
      cy.visit('/recargas')
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
      cy.get('[data-testid="scan-card-button"]').click()
      cy.get('[data-testid="amount-input"]').clear().type('25000')
      cy.get('[data-testid="payment-method-transfer"]').click()
      cy.get('[data-testid="voucher-input"]').type('COMP-DUPLICADO-001')
      cy.clickWhenReady('[data-testid="process-recharge-button"]')
      
      // Verificar detección de duplicado
      cy.verifyErrorToast('Comprobante ya existe')
      cy.get('[data-testid="duplicate-voucher-modal"]').should('be.visible')
    })
  })
})