// cypress/e2e/almuerzos/gestion-almuerzos.cy.ts
/// <reference types="cypress" />

describe('Gestion de Almuerzos', () => {
  const mockAdmin = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };

  beforeEach(() => {
    // Interceptar TODAS las llamadas a la API para evitar 401 del backend real
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: { count: 0, results: [] } });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.visit('/almuerzos', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockAdmin));
      },
    });
  });

  afterEach(() => {
    cy.clearLocalStorage();
  });

  it('debe mostrar la pagina de almuerzos', () => {
    cy.contains('Almuerzos').should('be.visible');
  });

  it('debe mostrar el tab Registro de Consumo', () => {
    cy.contains('Registro').should('be.visible');
  });

  it('debe mostrar el tab Planes de Almuerzo', () => {
    cy.contains('Planes').should('be.visible');
  });

  it('debe mostrar el tab Suscripciones', () => {
    cy.contains('Suscripciones').should('be.visible');
  });

  it('debe mostrar el tab Historial', () => {
    cy.contains('Historial').should('be.visible');
  });

  it('debe mostrar el tab Facturacion', () => {
    cy.contains('Facturación').should('be.visible');
  });

  it('debe navegar al tab de planes', () => {
    cy.contains('button', 'Planes').click();
    cy.url().should('include', '/almuerzos');
  });

  it('debe navegar al tab de suscripciones', () => {
    cy.contains('button', 'Suscripciones').click();
    cy.url().should('include', '/almuerzos');
  });

  it('debe mantener sesion activa', () => {
    cy.url().should('include', '/almuerzos');
    cy.url().should('not.include', '/login');
  });
});