// cypress/e2e/ventas/punto-venta.cy.ts
/// <reference types="cypress" />
describe('Punto de Venta', () => {
  beforeEach(() => {
    cy.fixture('users').then((users) => {
      cy.login(users.cajero.email, users.cajero.password)
    })
    cy.visit('/punto-venta')
  })

  afterEach(() => {
    cy.logout()
  })

  it('debe mostrar interfaz de punto de venta', () => {
    cy.get('[data-testid="pos-interface"]').should('be.visible')
    cy.get('[data-testid="product-search"]').should('be.visible')
    cy.get('[data-testid="cart-items"]').should('be.visible')
    cy.get('[data-testid="card-reader"]').should('be.visible')
  })

  it('debe buscar y agregar productos al carrito', () => {
    cy.fixture('productos').then((productos) => {
      // Buscar producto
      cy.get('[data-testid="product-search"]').type(productos.almuerzo_completo.nombre)
      cy.get('[data-testid="product-item"]').first().click()
      
      // Verificar en carrito
      cy.get('[data-testid="cart-items"]')
        .should('contain.text', productos.almuerzo_completo.nombre)
        .and('contain.text', productos.almuerzo_completo.precio.toLocaleString())
      
      // Verificar total
      cy.get('[data-testid="cart-total"]')
        .should('contain.text', productos.almuerzo_completo.precio.toLocaleString())
    })
  })

  it('debe procesar venta con tarjeta exitosa', () => {
    cy.fixture('productos').then((productos) => {
      cy.fixture('tarjetas').then((tarjetas) => {
        // Agregar producto al carrito
        cy.get('[data-testid="product-search"]').type(productos.bebida_gaseosa.nombre)
        cy.get('[data-testid="product-item"]').first().click()
        
        // Escanear tarjeta
        cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
        cy.get('[data-testid="read-card-button"]').click()
        
        // Verificar información de tarjeta
        cy.get('[data-testid="card-info"]').should('be.visible')
        cy.get('[data-testid="card-balance"]')
          .should('contain.text', tarjetas.tarjeta_activa.saldo_actual.toLocaleString())
        
        // Procesar venta
        cy.get('[data-testid="process-sale-button"]').should('not.be.disabled')
        cy.clickWhenReady('[data-testid="process-sale-button"]')
        
        // Verificar venta exitosa
        cy.verifySuccessToast('Venta procesada exitosamente')
        cy.get('[data-testid="receipt-modal"]').should('be.visible')
      })
    })
  })

  it('debe rechazar venta con saldo insuficiente', () => {
    cy.fixture('productos').then((productos) => {
      cy.fixture('tarjetas').then((tarjetas) => {
        // Agregar producto caro al carrito
        cy.get('[data-testid="product-search"]').type(productos.almuerzo_completo.nombre)
        cy.get('[data-testid="product-item"]').first().click()
        
        // Agregar más productos para superar saldo
        cy.get('[data-testid="add-quantity-button"]').click({ multiple: true })
        
        // Escanear tarjeta con poco saldo
        cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_bloqueada.nro_tarjeta)
        cy.get('[data-testid="read-card-button"]').click()
        
        // Intentar procesar venta
        cy.get('[data-testid="process-sale-button"]').click()
        
        // Verificar error
        cy.verifyErrorToast('Saldo insuficiente')
        cy.get('[data-testid="insufficient-balance-modal"]').should('be.visible')
      })
    })
  })

  it('debe manejar tarjeta bloqueada', () => {
    cy.fixture('tarjetas').then((tarjetas) => {
      // Escanear tarjeta bloqueada
      cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_bloqueada.nro_tarjeta)
      cy.get('[data-testid="read-card-button"]').click()
      
      // Verificar mensaje de tarjeta bloqueada
      cy.verifyErrorToast('Tarjeta bloqueada')
      cy.get('[data-testid="blocked-card-modal"]').should('be.visible')
    })
  })

  it('debe permitir cancelar venta', () => {
    cy.fixture('productos').then((productos) => {
      // Agregar productos
      cy.get('[data-testid="product-search"]').type(productos.snack_papas.nombre)
      cy.get('[data-testid="product-item"]').first().click()
      
      // Cancelar venta
      cy.get('[data-testid="cancel-sale-button"]').click()
      cy.get('[data-testid="confirm-cancel-button"]').click()
      
      // Verificar carrito limpio
      cy.get('[data-testid="cart-items"]').should('be.empty')
      cy.get('[data-testid="cart-total"]').should('contain.text', '0')
    })
  })

  it('debe imprimir recibo después de venta exitosa', () => {
    cy.fixture('productos').then((productos) => {
      cy.fixture('tarjetas').then((tarjetas) => {
        // Completar venta exitosa
        cy.get('[data-testid="product-search"]').type(productos.bebida_gaseosa.nombre)
        cy.get('[data-testid="product-item"]').first().click()
        cy.get('[data-testid="card-input"]').type(tarjetas.tarjeta_activa.nro_tarjeta)
        cy.get('[data-testid="read-card-button"]').click()
        cy.clickWhenReady('[data-testid="process-sale-button"]')
        
        // Verificar recibo y opciones de impresión
        cy.get('[data-testid="receipt-modal"]').should('be.visible')
        cy.get('[data-testid="print-receipt-button"]').should('be.visible')
        cy.get('[data-testid="email-receipt-button"]').should('be.visible')
        
        // Imprimir recibo
        cy.get('[data-testid="print-receipt-button"]').click()
        cy.verifySuccessToast('Recibo enviado a impresora')
      })
    })
  })
})