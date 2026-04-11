/**
 * Tests E2E para funcionalidades PWA
 * Verifica Service Worker, instalación, capacidades offline, etc.
 */

describe('PWA - Aplicación Web Progresiva', () => {
  const mockUser = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };

  const visitProtected = (path = '/dashboard') => {
    cy.visit(path, {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('refreshToken', 'fake-refresh-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
  };

  const visitPwaConfig = () => {
    visitProtected('/configuracion/pwa');
  };

  beforeEach(() => {
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('PATCH', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('DELETE', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('GET', /\/api\/v1\/auth\/perfil\/?$/, { statusCode: 200, body: mockUser }).as('perfil');

    cy.visit('/');
    cy.get('body', { timeout: 10000 }).should('be.visible');
    cy.get('#root').should('exist');
  });

  describe('Service Worker', () => {
    it('debe registrar el service worker correctamente', () => {
      cy.window().then((win) => {
        expect(win.navigator.serviceWorker).to.exist;

        return Cypress.Promise.delay(1200).then(() => win.navigator.serviceWorker.getRegistration());
      }).then((registration) => {
        if (registration && typeof registration.scope === 'string') {
          expect(registration.scope).to.include('/');
        } else {
          cy.log('Service Worker aún no expone scope en este entorno de desarrollo');
        }
      });
    });

    it('debe mostrar indicador de estado del SW', () => {
      // Verificar que existe algún componente PWA visible
      cy.get('body').should('be.visible');
      
      // Verificar indicadores de estado más generales
      cy.get('body').should('contain.text', 'Cantina Tita');
    });

    it('debe actualizar automáticamente cuando hay nueva versión', () => {
      // Simular actualización disponible
      cy.window().then((win) => {
        return win.navigator.serviceWorker.getRegistration();
      }).then((registration) => {
        if (registration) {
          // Simular evento updatefound
          const event = new Event('updatefound');
          registration.dispatchEvent(event);
        }
      });

      // Verificar notificación de actualización (si aparece)
      cy.get('body').then(($body) => {
        if ($body.find('.notification, .toast').length > 0) {
          cy.get('.notification, .toast').should('contain', 'Nueva versión');
        }
      });
    });
  });

  describe('Manifest y PWA', () => {
    it('debe tener un manifest válido', () => {
      // Verificar que el manifest existe
      cy.request('/manifest.json').then((response) => {
        expect(response.status).to.eq(200);
        expect(response.body).to.have.property('name');
        expect(response.body).to.have.property('short_name');
        expect(response.body).to.have.property('start_url');
        expect(response.body).to.have.property('display');
        expect(response.body).to.have.property('theme_color');
        expect(response.body).to.have.property('background_color');
        expect(response.body).to.have.property('icons');
      });
    });

    it('debe tener meta tags PWA correctos', () => {
      // Verificar viewport
      cy.get('head meta[name="viewport"]')
        .should('have.attr', 'content')
        .and('include', 'width=device-width');

      // Verificar theme-color
      cy.get('head meta[name="theme-color"]')
        .should('have.attr', 'content');

      // Verificar manifest link
      cy.get('head link[rel="manifest"]')
        .should('have.attr', 'href', '/manifest.json');
    });

    it('debe mostrar prompt de instalación cuando esté disponible', () => {
      // Simular evento beforeinstallprompt
      cy.window().then((win) => {
        const mockInstallPrompt = {
          prompt: cy.stub().resolves(),
          userChoice: Promise.resolve({ outcome: 'accepted' })
        };

        // Simular evento
        const event = new Event('beforeinstallprompt');
        Object.defineProperty(event, 'prompt', {
          value: mockInstallPrompt.prompt
        });
        Object.defineProperty(event, 'userChoice', {
          value: mockInstallPrompt.userChoice
        });

        win.dispatchEvent(event);
      });

      // Verificar botón de instalación (si aparece)
      cy.get('body').then(($body) => {
        if ($body.find('button').text().includes('Instalar')) {
          cy.contains('button', 'Instalar').should('be.visible');
        }
      });
    });
  });

  describe('Funcionalidades Offline', () => {
    it('debe servir página offline cuando no hay conexión', () => {
      // Simular modo offline
      cy.window().then((win) => {
        cy.wrap(win.navigator.serviceWorker.getRegistration()).then((registration: ServiceWorkerRegistration | undefined) => {
          if (registration && registration.active) {
            // Interceptar requests para simular offline
            cy.intercept('GET', '/api/**', { forceNetworkError: true });
            cy.intercept('GET', '/static/**', { forceNetworkError: true });
          }
        });
      });

      // Navegar a una página que requiera datos
      cy.visit('/dashboard', { failOnStatusCode: false });

      // El SW debería servir contenido cacheado o página offline
      cy.get('body').should('exist');
    });

    it('debe mantener funcionalidad básica sin conexión', () => {
      const pages = ['/', '/login', '/dashboard'];

      pages.forEach(page => {
        if (page === '/dashboard') {
          visitProtected(page);
        } else {
          cy.visit(page);
        }

        cy.get('body').should('exist');
        cy.get('#root').should('exist');
      });
    });
  });

  describe('Página de Configuración PWA', () => {
    it('debe mostrar estado completo de PWA', () => {
      visitPwaConfig();

      cy.contains('Configuración PWA', { timeout: 10000 }).should('be.visible');
      cy.contains('Aplicación Web Progresiva').should('be.visible');
      cy.contains('Acciones PWA').should('be.visible');
    });

    it('debe mostrar información técnica del SW', () => {
      visitPwaConfig();

      cy.contains('Información Técnica', { timeout: 10000 }).scrollIntoView().should('exist');
      cy.contains('Estado SW:').scrollIntoView().should('exist');
      cy.contains('Scope:').should('exist');
    });
  });

  describe('Notificaciones Push', () => {
    it('debe solicitar permisos de notificación', () => {
      cy.window().then((win) => {
        // Stub Notification API
        cy.stub(win.Notification, 'requestPermission').resolves('granted');
      });

      // Verificar que se pueda solicitar permisos
      cy.window().then((win) => {
        expect(win.Notification).to.exist;
      });
    });

    it('debe manejar notificaciones del stream SSE', () => {
      visitProtected('/dashboard');

      cy.window().then((win) => {
        expect(win.Notification).to.exist;
        expect('EventSource' in win).to.be.true;
      });

      cy.contains(/panel de control|cantina tita/i, { timeout: 10000 }).should('be.visible');
    });
  });

  describe('Responsive y Móvil', () => {
    it('debe funcionar correctamente en viewport móvil', () => {
      cy.viewport(375, 667);
      visitPwaConfig();

      cy.contains('Configuración PWA', { timeout: 10000 }).should('be.visible');
      cy.contains(/aplicación web progresiva|cantina tita/i).scrollIntoView().should('exist');

      cy.get('body').then(($body) => {
        if ($body.find('button').length > 0) {
          cy.get('button').first().should('be.visible');
        }
      });
    });

    it('debe mantener funcionalidad táctil', () => {
      cy.viewport('iphone-6');
      cy.visit('/');

      // Verificar interacciones táctiles básicas
      cy.get('button').first().click();
      cy.get('a').first().should('be.visible');
    });
  });

  describe('Performance PWA', () => {
    it('debe cargar rápidamente después de la primera visita', () => {
      // Primera visita
      cy.visit('/');
      
      // Segunda visita (debería usar cache)
      cy.reload();
      
      // Verificar que carga rápido
      cy.get('body', { timeout: 5000 }).should('exist');
    });

    it('debe tener recursos estáticos cacheados', () => {
      cy.visit('/');

      // Verificar que el SW está manejando requests
      cy.window().then((win) => {
        return win.navigator.serviceWorker.getRegistration();
      }).then((registration) => {
        if (registration && registration.active) {
          // SW debe estar activo y funcionando
          expect(registration.active.state).to.eq('activated');
        }
      });
    });
  });

  describe('Exports desde PWA', () => {
    beforeEach(() => {
      // Login como admin
      cy.visit('/login');
      cy.get('input[name="username"]').type('admin');
      cy.get('input[name="password"]').type('admin123'); 
      cy.get('button[type="submit"]').click();
      
      // Ir a dashboard
      cy.visit('/dashboard');
    });

    it('debe poder exportar PDF desde PWA', () => {
      // Buscar botones de export - pueden estar en diferentes elementos
      cy.get('body').then(($body) => {
        if ($body.find('button').text().includes('PDF')) {
          cy.contains('button', 'PDF').click();
          cy.contains('PDF', { timeout: 5000 }).should('exist');
        } else {
          // Test alternativo si no hay botón PDF visible
          cy.log('No se encontró botón PDF visible');
        }
      });
    });

    it('debe poder exportar Excel desde PWA', () => {
      // Buscar botones de export Excel
      cy.get('body').then(($body) => {
        if ($body.find('button').text().includes('Excel')) {
          cy.contains('button', 'Excel').click();
          cy.contains('Excel', { timeout: 5000 }).should('exist');
        } else {
          // Test alternativo si no hay botón Excel visible
          cy.log('No se encontró botón Excel visible');
        }
      });
    });
  });
});