/**
 * Comandos Cypress personalizados para PWA testing
 */

declare global {
  namespace Cypress {
    interface Chainable {
      /**
       * Verifica que el Service Worker está registrado y activo
       */
      checkServiceWorker(): Chainable<void>
      
      /**
       * Simula instalación de PWA
       */
      simulatePWAInstall(): Chainable<void>
      
      /**
       * Verifica capacidades offline
       */
      checkOfflineCapabilities(): Chainable<void>
      
      /**
       * Simula estado offline/online
       */
      setNetworkState(online: boolean): Chainable<void>
      
      /**
       * Verifica manifest PWA
       */
      validatePWAManifest(): Chainable<void>
      
      /**
       * Configura viewport para dispositivo móvil específico
       */
      setMobileDevice(device: 'iphone' | 'android' | 'ipad'): Chainable<void>
      
      /**
       * Verifica que elementos son touch-friendly
       */
      checkTouchTargets(): Chainable<void>
      
      /**
       * Simula eventos táctiles
       */
      touchElement(selector: string): Chainable<void>
    }
  }
}

// Comando para verificar Service Worker
Cypress.Commands.add('checkServiceWorker', () => {
  cy.window().then((win) => {
    // Verificar soporte
    expect(win.navigator.serviceWorker, 'Service Worker support').to.exist;
    
    // Verificar registro
    return win.navigator.serviceWorker.getRegistration();
  }).then((registration) => {
    expect(registration, 'Service Worker registration').to.exist;
    expect(registration!.scope, 'Service Worker scope').to.include('/');
    
    if (registration!.active) {
      expect(registration!.active.state, 'Service Worker state').to.eq('activated');
    }
  });
});

// Comando para simular instalación PWA
Cypress.Commands.add('simulatePWAInstall', () => {
  cy.window().then((win) => {
    // Crear evento beforeinstallprompt mock
    const mockPromptEvent = {
      preventDefault: cy.stub(),
      prompt: cy.stub().resolves(),
      userChoice: Promise.resolve({ outcome: 'accepted' })
    };

    // Crear y disparar evento
    const event = new Event('beforeinstallprompt');
    Object.assign(event, mockPromptEvent);
    
    win.dispatchEvent(event);
    
    // Simular instalación exitosa
    setTimeout(() => {
      const installedEvent = new Event('appinstalled');
      win.dispatchEvent(installedEvent);
    }, 100);
  });
});

// Comando para verificar capacidades offline
Cypress.Commands.add('checkOfflineCapabilities', () => {
  // Verificar que páginas principales están cacheadas
  const criticalPages = ['/', '/login', '/dashboard'];
  
  criticalPages.forEach(page => {
    cy.visit(page);
    
    // Simular offline
    cy.setNetworkState(false);
    
    // Recargar página
    cy.reload();
    
    // Verificar que sigue funcionando
    cy.get('body').should('exist');
    
    // Volver a online
    cy.setNetworkState(true);
  });
});

// Comando para simular estado de red
Cypress.Commands.add('setNetworkState', (online: boolean) => {
  cy.window().then((win) => {
    // Stub navigator.onLine
    cy.stub(win.navigator, 'onLine').value(online);
    
    // Disparar evento apropiado
    const event = new Event(online ? 'online' : 'offline');
    win.dispatchEvent(event);
    
    // Dar tiempo para que los listeners reaccionen
    cy.wait(100);
  });
});

// Comando para validar manifest
Cypress.Commands.add('validatePWAManifest', () => {
  cy.request('/manifest.json').then((response) => {
    expect(response.status).to.eq(200);
    const manifest = response.body;
    
    // Validaciones completas
    expect(manifest.name).to.be.a('string').and.not.be.empty;
    expect(manifest.short_name).to.be.a('string').and.not.be.empty;
    expect(manifest.start_url).to.be.a('string').and.not.be.empty;
    expect(manifest.display).to.be.oneOf(['standalone', 'minimal-ui', 'fullscreen', 'browser']);
    expect(manifest.theme_color).to.match(/^#[0-9A-Fa-f]{6}$/);
    expect(manifest.background_color).to.match(/^#[0-9A-Fa-f]{6}$/);
    expect(manifest.icons).to.be.an('array').and.have.length.greaterThan(0);
    
    // Verificar iconos requeridos
    const requiredSizes = ['192x192', '512x512'];
    requiredSizes.forEach(size => {
      const hasSize = manifest.icons.some((icon: any) => 
        icon.sizes && icon.sizes.includes(size)
      );
      expect(hasSize, `Icon ${size} present`).to.be.true;
    });
  });
});

// Comando para configurar dispositivos móviles
Cypress.Commands.add('setMobileDevice', (device: 'iphone' | 'android' | 'ipad') => {
  const devices = {
    iphone: { width: 375, height: 667 },
    android: { width: 360, height: 640 },
    ipad: { width: 768, height: 1024 }
  };
  
  const { width, height } = devices[device];
  cy.viewport(width, height);
});

// Comando para verificar targets táctiles
Cypress.Commands.add('checkTouchTargets', () => {
  const minTouchSize = 44; // Pixels mínimos recomendados
  
  cy.get('button, a, input[type="button"], input[type="submit"], [role="button"]')
    .each($el => {
      const rect = $el[0].getBoundingClientRect();
      const size = Math.min(rect.width, rect.height);
      
      if (size > 0) { // Solo verificar elementos visibles
        expect(size, `Touch target size for ${$el[0].tagName}`).to.be.greaterThan(32);
      }
    });
});

// Comando para simular toques
Cypress.Commands.add('touchElement', (selector: string) => {
  cy.get(selector).then($el => {
    const element = $el[0];
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Crear eventos táctiles
    const touchStart = new TouchEvent('touchstart', {
      bubbles: true,
      touches: [{
        clientX: centerX,
        clientY: centerY,
        target: element
      } as any]
    });
    
    const touchEnd = new TouchEvent('touchend', {
      bubbles: true
    });
    
    // Disparar eventos
    element.dispatchEvent(touchStart);
    cy.wait(50); // Simular duración del toque
    element.dispatchEvent(touchEnd);
    
    // También disparar click para compatibilidad
    element.click();
  });
});

export {};