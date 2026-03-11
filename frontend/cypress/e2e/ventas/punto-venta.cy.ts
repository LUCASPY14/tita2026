// cypress/e2e/ventas/punto-venta.cy.ts
/// <reference types="cypress" />

describe('Punto de Venta', () => {
  const mockUser = { id: 2, username: 'cajero', email: 'cajero@cantina.com', role: 'cajero' };

  beforeEach(() => {
    // Interceptar TODAS las llamadas a la API para evitar 401 del backend real
    // Usar hostname especifico para NO interceptar el frontend (localhost:3000)
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: { count: 0, results: [] } });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.visit('/ventas', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
  });

  afterEach(() => {
    cy.clearLocalStorage();
  });

  it('debe mostrar titulo del punto de venta', () => {
    cy.contains('Punto de Venta').should('be.visible');
  });

  it('debe mostrar informacion de atajos de teclado', () => {
    cy.contains('Procesar venta').should('be.visible');
  });

  it('debe mostrar el tab Venta', () => {
    cy.contains('Venta').should('be.visible');
  });

  it('debe mostrar el tab Historial de Ventas', () => {
    cy.contains('Historial de Ventas').should('be.visible');
  });

  it('debe mostrar el tab Devoluciones', () => {
    cy.contains('Devoluciones').should('be.visible');
  });

  it('debe mostrar el catalogo de productos vacio', () => {
    cy.contains('No hay productos disponibles').should('be.visible');
  });

  it('debe mantener sesion activa', () => {
    cy.url().should('include', '/ventas');
    cy.url().should('not.include', '/login');
  });
});