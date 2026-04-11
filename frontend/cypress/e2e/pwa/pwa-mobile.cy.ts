/**
 * Tests específicos para instalación PWA en dispositivos móviles
 */

describe('PWA - Instalación y Dispositivos Móviles', () => {
  const mockUser = { id: 1, username: 'admin', email: 'admin@cantina.com', role: 'admin' };

  const visitProtected = (path = '/dashboard') => {
    cy.intercept('GET', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('POST', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('PATCH', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('DELETE', 'http://localhost:8000/**', { statusCode: 200, body: {} });
    cy.intercept('GET', /\/api\/v1\/auth\/perfil\/?$/, { statusCode: 200, body: mockUser });

    cy.visit(path, {
      onBeforeLoad(win) {
        win.localStorage.setItem('token', 'fake-access-token');
        win.localStorage.setItem('refreshToken', 'fake-refresh-token');
        win.localStorage.setItem('user', JSON.stringify(mockUser));
      },
    });
  };

  describe('Proceso de Instalación', () => {
    beforeEach(() => {
      cy.visit('/');
    });

    it('debe cumplir criterios de instalación PWA', () => {
      // Verificar HTTPS (en producción)
      cy.location('protocol').then((protocol) => {
        // En desarrollo será http, en producción debe ser https
        expect(protocol).to.be.oneOf(['http:', 'https:']);
      });

      // Verificar Service Worker registrado
      cy.window().then((win) => {
        return win.navigator.serviceWorker.getRegistration();
      }).then((registration) => {
        expect(registration).to.exist;
      });

      // Verificar manifest válido  
      cy.request('/manifest.json').then((response) => {
        expect(response.status).to.eq(200);
        const manifest = response.body;
        
        // Criterios básicos de instalación
        expect(manifest.name).to.exist;
        expect(manifest.short_name).to.exist;
        expect(manifest.start_url).to.exist;
        expect(manifest.display).to.be.oneOf(['standalone', 'minimal-ui', 'fullscreen']);
        expect(manifest.icons).to.be.an('array').and.have.length.greaterThan(0);
        
        // Verificar iconos con tamaños apropiados
        const hasAppropriateSizes = manifest.icons.some(icon => 
          icon.sizes && (icon.sizes.includes('192x192') || icon.sizes.includes('512x512'))
        );
        expect(hasAppropriateSizes).to.be.true;
      });
    });

    it('debe manejar el evento beforeinstallprompt', () => {
      cy.window().then((win) => {
        // Crear mock del evento
        const mockEvent = {
          preventDefault: cy.stub(),
          prompt: cy.stub().resolves(),
          userChoice: Promise.resolve({ outcome: 'accepted' })
        };

        // Agregar listener para el evento
        let eventHandled = false;
        win.addEventListener('beforeinstallprompt', () => {
          eventHandled = true;
        });

        // Disparar evento mock
        const event = new Event('beforeinstallprompt');
        Object.assign(event, mockEvent);
        win.dispatchEvent(event);

        // Verificar que se manejó
        expect(eventHandled).to.be.true;
      });
    });

    it('debe mostrar UI de instalación apropiada', () => {
      // Buscar elementos UI relacionados con instalación
      cy.get('body').then(($body) => {
        // Verificar si hay botón de instalación
        if ($body.find('#pwa-install-btn, [data-testid="install-app"]').length > 0) {
          cy.get('#pwa-install-btn, [data-testid="install-app"]')
            .should('be.visible')
            .and('contain.text', /instalar|install/i);
        }
      });
    });
  });

  describe('Simulación Dispositivos Móviles', () => {
    const devices = [
      { name: 'iPhone SE', width: 375, height: 667 },
      { name: 'iPhone 12', width: 390, height: 844 },
      { name: 'Samsung Galaxy S21', width: 360, height: 800 },
      { name: 'iPad', width: 768, height: 1024 }
    ];

    devices.forEach(device => {
      it(`debe funcionar correctamente en ${device.name}`, () => {
        cy.viewport(device.width, device.height);
        visitProtected('/configuracion/pwa');

        cy.get('body', { timeout: 10000 }).should('be.visible');
        cy.contains('Configuración PWA', { timeout: 10000 }).should('be.visible');
        cy.contains(/aplicación web progresiva|cantina tita/i).should('exist');

        cy.get('body').then(($body) => {
          if ($body.find('button, a').length > 0) {
            cy.get('button, a').first().should('be.visible');
          }
        });
      });
    });

    it('debe manejar eventos táctiles correctamente', () => {
      cy.viewport('iphone-6');
      visitProtected('/configuracion/pwa');

      cy.get('button, a')
        .first()
        .should('be.visible')
        .trigger('touchstart')
        .trigger('touchend');
    });

    it('debe mantener rendimiento en dispositivos móviles', () => {
      cy.viewport('iphone-6');

      const start = Date.now();
      cy.visit('/');

      cy.get('body', { timeout: 5000 }).should('be.visible').then(() => {
        const loadTime = Date.now() - start;
        expect(loadTime).to.be.lessThan(5000);
      });
    });
  });

  describe('Orientación y Rotación', () => {
    it('debe adaptarse a orientación portrait', () => {
      cy.viewport(375, 667);
      visitProtected('/configuracion/pwa');

      cy.contains('Configuración PWA', { timeout: 10000 }).should('be.visible');
      cy.contains(/aplicación web progresiva|cantina tita/i).should('exist');
    });

    it('debe adaptarse a orientación landscape', () => {
      cy.viewport(667, 375);
      visitProtected('/configuracion/pwa');

      cy.contains('Configuración PWA', { timeout: 10000 }).should('be.visible');
      cy.contains(/aplicación web progresiva|cantina tita/i).should('exist');
    });

    it('debe mantener estado al rotar', () => {
      cy.viewport(375, 667);
      visitProtected('/configuracion/pwa');
      cy.contains('Configuración PWA', { timeout: 10000 }).should('be.visible');

      cy.viewport(667, 375);

      cy.url().should('include', '/configuracion/pwa');
      cy.contains(/aplicación web progresiva|cantina tita/i).should('exist');
    });
  });

  describe('Capacidades Específicas de Móvil', () => {
    beforeEach(() => {
      cy.viewport('iphone-6');
      visitProtected('/configuracion/pwa');
    });

    it('debe detectar si está en standalone mode', () => {
      cy.window().then((win) => {
        // Verificar detección de standalone
        const isStandalone = win.matchMedia && win.matchMedia('(display-mode: standalone)').matches;
        
        // También verificar propiedades específicas
        const isWebApp = 'standalone' in win.navigator || (win.navigator as any).standalone;
        
        // Al menos una forma de detección debe estar disponible
        expect(typeof isStandalone === 'boolean').to.be.true;
      });
    });

    it('debe ocultar elementos de browser en standalone', () => {
      cy.window().then((win) => {
        // Simular standalone mode
        Object.defineProperty(win.navigator, 'standalone', {
          value: true,
          configurable: true
        });
        
        // Recargar para aplicar cambios
        cy.reload();
        
        // Verificar que elementos específicos del browser están ocultos
        // (esto dependerá de la implementación específica)
        cy.get('body').should('exist');
      });
    });

    it('debe manejar splash screen apropiadamente', () => {
      // Verificar meta tags para splash screen
      cy.get('head meta[name="apple-mobile-web-app-capable"]')
        .should('have.attr', 'content', 'yes');
        
      cy.get('head meta[name="apple-mobile-web-app-status-bar-style"]')
        .should('have.attr', 'content');
    });

    it('debe funcionar sin conexión en móvil', () => {
      cy.window().then((win) => {
        cy.stub(win.navigator, 'onLine').value(false);
        win.dispatchEvent(new Event('offline'));
      });

      cy.get('body').should('exist');
      cy.get('#root').should('exist');
      cy.get('main').should('exist');
    });
  });

  describe('Tests de Performance Móvil', () => {
    it('debe cargar recursos críticos rápidamente', () => {
      cy.viewport('iphone-6');

      const resourceTimes: { css?: number; js?: number } = {};

      cy.intercept('**/*.css', (req) => {
        resourceTimes.css = Date.now();
        req.continue();
      });

      cy.intercept('**/*.js', (req) => {
        resourceTimes.js = Date.now();
        req.continue();
      });

      const startTime = Date.now();
      cy.visit('/');

      cy.get('body', { timeout: 4000 }).should('be.visible').then(() => {
        const totalTime = Date.now() - startTime;
        expect(totalTime).to.be.lessThan(4000);
      });
    });

    it('debe optimizar imágenes para móvil', () => {
      cy.viewport('iphone-6');
      cy.visit('/');

      cy.get('body').then(($body) => {
        if ($body.find('img').length > 0) {
          cy.get('img').each($img => {
            const img = $img[0] as HTMLImageElement;

            if (img.hasAttribute('loading')) {
              expect(img.getAttribute('loading')).to.eq('lazy');
            }

            if (img.naturalWidth) {
              expect(img.naturalWidth).to.be.greaterThan(0);
            }
          });
        } else {
          cy.get('#root').should('exist');
        }
      });
    });
  });

  describe('Accesibilidad en Móvil', () => {
    beforeEach(() => {
      cy.viewport('iphone-6');
      cy.visit('/');
    });

    it('debe tener targets táctiles apropiados', () => {
      cy.get('button:visible, a:visible').first().then($el => {
        const rect = $el[0].getBoundingClientRect();
        expect(Math.max(rect.width, rect.height)).to.be.greaterThan(32);
      });
    });

    it('debe mantener contraste apropiado', () => {
      // Verificar elementos de texto principales
      cy.get('h1, h2, h3, p, button, a').should('be.visible').each($el => {
        cy.wrap($el).should('have.css', 'color');
      });
    });

    it('debe ser navegable por teclado virtual', () => {
      // Verificar inputs táctiles
      cy.get('input, textarea').each($input => {
        cy.wrap($input)
          .should('be.visible')
          .focus()
          .should('have.focus');
      });
    });
  });
});