// cypress/e2e/auth/login.cy.ts
/// <reference types="cypress" />

describe('Autenticación', () => {
  beforeEach(() => {
    cy.visit('/')
  })

  it('debe mostrar formulario de login en página inicial', () => {
    cy.get('[data-testid="login-form"]').should('be.visible')
    cy.get('[data-testid="email-input"]').should('be.visible')
    cy.get('[data-testid="password-input"]').should('be.visible')
    cy.get('[data-testid="login-button"]').should('be.visible')
  })

  it('debe validar campos requeridos', () => {
    cy.get('[data-testid="login-button"]').click()
    
    cy.get('[data-testid="email-error"]')
      .should('be.visible')
      .and('contain.text', 'Email es requerido')
    
    cy.get('[data-testid="password-error"]')
      .should('be.visible')
      .and('contain.text', 'Contraseña es requerida')
  })

  it('debe validar formato de email', () => {
    cy.get('[data-testid="email-input"]').type('email-invalido')
    cy.get('[data-testid="password-input"]').type('123456')
    cy.get('[data-testid="login-button"]').click()
    
    cy.get('[data-testid="email-error"]')
      .should('be.visible')
      .and('contain.text', 'Email inválido')
  })

  it('debe mostrar error con credenciales incorrectas', () => {
    cy.get('[data-testid="email-input"]').type('wrong@test.com')
    cy.get('[data-testid="password-input"]').type('wrongpass')
    cy.get('[data-testid="login-button"]').click()
    
    cy.verifyErrorToast('Credenciales inválidas')
  })

  it('debe realizar login exitoso con credenciales correctas', () => {
    cy.fixture('users').then((users) => {
      cy.get('[data-testid="email-input"]').type(users.admin.email)
      cy.get('[data-testid="password-input"]').type(users.admin.password)
      cy.get('[data-testid="login-button"]').click()
      
      // Verificar redirección al dashboard
      cy.url().should('include', '/dashboard')
      cy.get('[data-testid="user-menu"]').should('be.visible')
      cy.get('[data-testid="user-name"]').should('contain.text', users.admin.name)
    })
  })

  it('debe recordar usuario autenticado al refrescar página', () => {
    cy.fixture('users').then((users) => {
      // Login
      cy.login(users.admin.email, users.admin.password)
      cy.visit('/dashboard')
      
      // Refrescar página
      cy.reload()
      
      // Verificar que sigue autenticado
      cy.url().should('include', '/dashboard')
      cy.get('[data-testid="user-menu"]').should('be.visible')
    })
  })
})