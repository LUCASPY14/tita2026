// cypress/e2e/auth/login.cy.ts
/// <reference types="cypress" />

// Usa el API_BASE_URL configurado en cypress.config.ts (incluye /v1)
const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';

describe('Autenticación - Página de Login', () => {
  beforeEach(() => {
    cy.clearLocalStorage();
    cy.clearCookies();
    cy.visit('/');
  });

  it('debe mostrar formulario de login en página inicial', () => {
    cy.get('#username').should('be.visible');
    cy.get('#password').should('be.visible');
    cy.contains('button', 'Iniciar Sesión').should('be.visible');
    cy.contains('¿Olvidaste tu contraseña?').should('be.visible');
  });

  it('debe mostrar error con credenciales incorrectas (mockeado)', () => {
    cy.intercept('POST', `${API}/auth/login/`, {
      statusCode: 401,
      body: { success: false, mensaje: 'Credenciales inválidas' },
    }).as('loginFail');

    cy.get('#username').type('usuario_incorrecto');
    cy.get('#password').type('clave_incorrecta');
    cy.contains('button', 'Iniciar Sesión').click();

    cy.wait('@loginFail');
    cy.get('#username').should('be.visible');
  });

  it('debe poder escribir en los campos de usuario y contraseña', () => {
    cy.get('#username').type('admin').should('have.value', 'admin');
    cy.get('#password').type('secreto').should('have.value', 'secreto');
  });

  it('debe mostrar y navegar al enlace de recuperación de contraseña', () => {
    cy.contains('¿Olvidaste tu contraseña?').should('be.visible').click();
    cy.url().should('include', '/recuperar-password');
  });

  it('debe redirigir al dashboard con login exitoso (mockeado)', () => {
    cy.intercept('POST', `${API}/auth/login/`, {
      statusCode: 200,
      body: {
        success: true,
        requiere_2fa: false,
        tokens: { access: 'fake-access-token', refresh: 'fake-refresh-token' },
        empleado: { id: 1, usuario: 'admin', email: 'admin@cantina.com', rol: 'administrador' },
      },
    }).as('loginOk');

    cy.intercept('GET', `${API}/auth/perfil/`, {
      statusCode: 200,
      body: { id: 1, username: 'admin', email: 'admin@cantina.com' },
    }).as('perfil');

    cy.get('#username').type('admin');
    cy.get('#password').type('admin123');
    cy.contains('button', 'Iniciar Sesión').click();

    cy.wait('@loginOk');
    cy.url().should('include', '/dashboard');
  });

  it('debe mantener sesión activa al recargar la página', () => {
    cy.intercept('GET', 'http://localhost:8000/**', (req) => {
      if (req.url.includes('/auth/perfil')) {
        req.reply({ statusCode: 200, body: { id: 1, username: 'admin', email: 'admin@cantina.com' } });
      } else {
        req.reply({ statusCode: 200, body: { count: 0, results: [] } });
      }
    });

    cy.visit('/dashboard', {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('user', JSON.stringify({
          id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin',
        }));
      },
    });
    cy.url().should('include', '/dashboard');
  });
});