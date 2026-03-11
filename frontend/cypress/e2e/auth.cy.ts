/**
 * Tests E2E - Flujo de Autenticación
 * Cubre: login, logout, 2FA redirect, recuperar contraseña
 */

describe('Autenticación', () => {
  const API = Cypress.env('API_BASE_URL') || 'http://localhost:8000/api/v1';

  beforeEach(() => {
    cy.clearLocalStorage();
    cy.clearCookies();
  });

  // ── Login ──────────────────────────────────────────────────────────────────

  describe('Página de Login', () => {
    beforeEach(() => {
      cy.visit('/login');
    });

    it('muestra el formulario de login correctamente', () => {
      cy.get('#username').should('be.visible');
      cy.get('#password').should('be.visible');
      cy.contains('button', 'Iniciar Sesión').should('be.visible');
      cy.contains('¿Olvidaste tu contraseña?').should('be.visible');
    });

    it('muestra error con credenciales incorrectas', () => {
      cy.intercept('POST', `${API}/auth/login/`, {
        statusCode: 401,
        body: { detail: 'Credenciales inválidas' },
      }).as('loginFail');

      cy.get('#username').type('usuario_incorrecto');
      cy.get('#password').type('clave_incorrecta');
      cy.contains('button', 'Iniciar Sesión').click();

      cy.wait('@loginFail');
      // El formulario permanece visible (no hubo redirección)
      cy.get('#username').should('be.visible');
    });

    it('redirige al dashboard tras login exitoso', () => {
      cy.intercept('POST', `${API}/auth/login/`, {
        statusCode: 200,
        body: {
          success: true,
          requiere_2fa: false,
          tokens: { access: 'fake-access-token', refresh: 'fake-refresh-token' },
          empleado: {
            id: 1,
            username: 'admin',
            email: 'admin@cantina.com',
            role: 'admin',
          },
        },
      }).as('loginOk');

      cy.intercept('GET', `${API}/auth/perfil/`, {
        statusCode: 200,
        body: {
          id: 1,
          username: 'admin',
          email: 'admin@cantina.com',
          role: 'admin',
        },
      }).as('perfil');

      cy.get('#username').type('admin');
      cy.get('#password').type('admin123');
      cy.contains('button', 'Iniciar Sesión').click();

      cy.wait('@loginOk');
      cy.url().should('include', '/dashboard');
    });

    it('redirige a /verificar-2fa cuando el login requiere 2FA', () => {
      cy.intercept('POST', `${API}/auth/login/`, {
        statusCode: 200,
        body: {
          success: true,
          requiere_2fa: true,
          token_temporal: 'temp-2fa-token-xyz',
        },
      }).as('login2FA');

      cy.get('#username').type('admin');
      cy.get('#password').type('admin123');
      cy.contains('button', 'Iniciar Sesión').click();

      cy.wait('@login2FA');
      cy.url().should('include', '/verificar-2fa');
    });

    it('el enlace "¿Olvidaste tu contraseña?" lleva a /recuperar-password', () => {
      cy.contains('¿Olvidaste tu contraseña?').click();
      cy.url().should('include', '/recuperar-password');
    });
  });

  // ── Verificación 2FA ───────────────────────────────────────────────────────

  describe('Verificación 2FA', () => {
    beforeEach(() => {
      // Simular que ya se guardó el token temporal
      cy.window().then((win) => {
        win.sessionStorage.setItem('cantina_2fa_temp_token', 'temp-2fa-token-xyz');
      });
      cy.visit('/verificar-2fa');
    });

    it('muestra los 6 campos de dígito', () => {
      cy.get('input[maxlength="1"]').should('have.length', 6);
    });

    it('muestra error si el código es incorrecto', () => {
      cy.intercept('POST', `${API}/2fa/verificar/`, {
        statusCode: 400,
        body: { detail: 'Código inválido' },
      }).as('verify2FAFail');

      // Teclear el código dígito a dígito
      cy.get('input[maxlength="1"]').eq(0).type('1');
      cy.get('input[maxlength="1"]').eq(1).type('2');
      cy.get('input[maxlength="1"]').eq(2).type('3');
      cy.get('input[maxlength="1"]').eq(3).type('4');
      cy.get('input[maxlength="1"]').eq(4).type('5');
      cy.get('input[maxlength="1"]').eq(5).type('6');

      cy.contains('button', 'Verificar').click();
      cy.wait('@verify2FAFail');
      // El formulario permanece visible
      cy.get('input[maxlength="1"]').should('be.visible');
    });
  });

  // ── Recuperar Contraseña ───────────────────────────────────────────────────

  describe('Recuperar Contraseña', () => {
    it('muestra el formulario de solicitud de recuperación', () => {
      cy.visit('/recuperar-password');
      cy.get('input[type="email"]').should('be.visible');
      cy.contains('button', 'Enviar').should('be.visible');
    });

    it('pasa al paso "email enviado" tras solicitar recuperación', () => {
      cy.intercept('POST', `${API}/password/solicitar/`, {
        statusCode: 200,
        body: { detail: 'Email enviado' },
      }).as('solicitar');

      cy.visit('/recuperar-password');
      cy.get('input[type="email"]').type('admin@cantina.com');
      cy.contains('button', 'Enviar').click();

      cy.wait('@solicitar');
      // Debe mostrar mensaje de confirmación de email enviado
      cy.contains(/enviado|correo|email/i).should('be.visible');
    });
  });

  // ── Logout ─────────────────────────────────────────────────────────────────

  describe('Logout programático', () => {
    it('clearLocalStorage elimina las credenciales', () => {
      cy.window().then((win) => {
        win.localStorage.setItem('token', 'some-token');
        win.localStorage.setItem('user', JSON.stringify({ id: 1, username: 'admin' }));
      });

      cy.clearLocalStorage();

      cy.window().then((win) => {
        expect(win.localStorage.getItem('token')).to.be.null;
        expect(win.localStorage.getItem('user')).to.be.null;
      });
    });
  });
});
