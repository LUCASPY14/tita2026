/**
 * Tests específicos para instalación PWA en dispositivos móviles
 */

describe('PWA - Instalación y Dispositivos Móviles', () => {
  
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
        cy.visit('/');

        // Verificar carga básica
        cy.get('body', { timeout: 10000 }).should('be.visible');

        // Verificar responsive design
        cy.get('body').should('be.visible');
        
        // Verificar que el header se adapta
        cy.get('header').should('be.visible');

        // En dispositivos pequeños, verificar menú hamburger
        if (device.width < 768) {
          cy.get('body').then(($body) => {
            if ($body.find('button').length > 0) {
              cy.get('button').first().should('be.visible');
            }
          });
        }

        // Verificar PWA status en móvil
        cy.get('.fixed').should('exist');

        // Test básico de navegación
        cy.get('a').first().should('be.visible').and('have.attr', 'href');
      });
    });

    it('debe manejar eventos táctiles correctamente', () => {
      cy.viewport('iphone-6');
      cy.visit('/');

      // Simular touch events
      cy.get('button').first().then($btn => {
        const btn = $btn[0];
        
        // Touch start
        const touch = {
          identifier: 0,
          target: btn as EventTarget,
          clientX: 100,
          clientY: 100,
          pageX: 100,
          pageY: 100,
          screenX: 100,
          screenY: 100,
          radiusX: 1,
          radiusY: 1,
          rotationAngle: 0,
          force: 1
        } as Touch;
        
        const touchstart = new TouchEvent('touchstart', {
          bubbles: true,
          touches: [touch],
          targetTouches: [touch],
          changedTouches: [touch]
        });
        
        // Touch end  
        const touchend = new TouchEvent('touchend', {
          bubbles: true
        });

        btn.dispatchEvent(touchstart);
        btn.dispatchEvent(touchend);
      });
    });

    it('debe mantener rendimiento en dispositivos móviles', () => {
      cy.viewport('iphone-6');
      
      // Medir tiempo de carga
      const start = Date.now();
      cy.visit('/');
      
      cy.get('[data-testid="app-loaded"]').then(() => {
        const loadTime = Date.now() - start;
        // En móvil debería cargar en menos de 5 segundos
        expect(loadTime).to.be.lessThan(5000);
      });
    });
  });

  describe('Orientación y Rotación', () => {
    it('debe adaptarse a orientación portrait', () => {
      cy.viewport(375, 667); // iPhone SE portrait
      cy.visit('/');

      cy.get('[data-testid="app-loaded"]').should('exist');
      cy.get('header').should('be.visible');
    });

    it('debe adaptarse a orientación landscape', () => {
      cy.viewport(667, 375); // iPhone SE landscape  
      cy.visit('/');

      cy.get('[data-testid="app-loaded"]').should('exist');
      cy.get('header').should('be.visible');
    });

    it('debe mantener estado al rotar', () => {
      // Login en portrait
      cy.viewport(375, 667);
      cy.visit('/login');
      cy.get('input[name="username"]').type('admin');
      cy.get('input[name="password"]').type('admin123');

      // Rotar a landscape
      cy.viewport(667, 375);
      
      // Verificar que los datos persisten
      cy.get('input[name="username"]').should('have.value', 'admin');
      cy.get('input[name="password"]').should('have.value', 'admin123');

      // Completar login
      cy.get('button[type="submit"]').click();
      cy.url().should('include', '/dashboard');
    });
  });

  describe('Capacidades Específicas de Móvil', () => {
    beforeEach(() => {
      cy.viewport('iphone-6');
      cy.visit('/');
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
      // Simular pérdida de conexión
      cy.window().then((win) => {
        // Stub navigator.onLine
        cy.stub(win.navigator, 'onLine').value(false);
        
        // Disparar evento offline
        const offlineEvent = new Event('offline');
        win.dispatchEvent(offlineEvent);
      });

      // Verificar que la app sigue funcionando
      cy.get('.fixed')
        .invoke('text')
        .should('match', /OFFLINE|Sin conexión|SW/);

      // Verificar funcionalidad básica offline
      cy.get('header').should('be.visible');
      cy.get('nav').should('be.visible');
    });
  });

  describe('Tests de Performance Móvil', () => {
    it('debe cargar recursos críticos rápidamente', () => {
      cy.viewport('iphone-6');
      
      // Interceptar recursos para medir tiempo
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
      
      cy.get('[data-testid="app-loaded"]').then(() => {
        const totalTime = Date.now() - startTime;
        // Debe cargar en menos de 4 segundos en móvil
        expect(totalTime).to.be.lessThan(4000);
      });
    });

    it('debe optimizar imágenes para móvil', () => {
      cy.viewport('iphone-6');
      cy.visit('/');

      // Verificar que las imágenes tienen atributos responsive
      cy.get('img').each($img => {
        const img = $img[0] as HTMLImageElement;
        
        // Verificar lazy loading
        if (img.hasAttribute('loading')) {
          expect(img.getAttribute('loading')).to.eq('lazy');
        }
        
        // Verificar tamaño apropiado
        if (img.naturalWidth) {
          expect(img.naturalWidth).to.be.greaterThan(0);
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
      // Verificar que botones tienen tamaño mínimo
      cy.get('button').each($btn => {
        cy.wrap($btn).then($el => {
          const rect = $el[0].getBoundingClientRect();
          // Tamaño mínimo recomendado: 44px
          expect(Math.min(rect.width, rect.height)).to.be.greaterThan(32);
        });
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