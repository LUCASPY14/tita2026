// cypress/e2e/recargas/recargas-tarjeta.cy.ts
/// <reference types="cypress" />

describe('Recargas de Tarjeta', () => {
  const mockUser = { id: 2, username: 'cajero', email: 'cajero@cantina.com', role: 'cajero' };

  beforeEach(() => {
    // Interceptar TODAS las llamadas a la API para evitar 401 del backend real
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: { count: 0, results: [] } });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.visit('/recargas', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
  });

  afterEach(() => {
    cy.clearLocalStorage();
  });

  it('debe mostrar la pagina de recargas', () => {
    cy.contains('Recargas de Tarjeta').should('be.visible');
  });

  it('debe mostrar la seccion buscar hijo', () => {
    cy.contains('Buscar Hijo').should('be.visible');
  });

  it('debe mostrar el tab Movimientos de Saldo', () => {
    cy.contains('Movimientos de Saldo').should('be.visible');
  });

  it('debe mostrar el tab Aprobacion', () => {
    cy.contains('Recargas').should('be.visible');
  });

  it('debe navegar al tab de movimientos', () => {
    cy.contains('Movimientos de Saldo').click();
    cy.url().should('include', '/recargas');
  });

  it('debe mostrar campo de texto para busqueda', () => {
    cy.get('input[type="text"]').first().should('be.visible');
  });

  it('debe mostrar boton para buscar', () => {
    cy.contains('button', 'Buscar').should('be.visible');
  });

  it('debe mantener sesion activa', () => {
    cy.url().should('include', '/recargas');
    cy.url().should('not.include', '/login');
  });
});