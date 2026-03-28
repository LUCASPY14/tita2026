/**
 * Configuración simplificada para testing móvil manual
 * Para casos donde Playwright no esté disponible
 */

class SimpleMobileTest {
  constructor() {
    this.baseUrl = 'http://localhost:3000';
    this.testDevices = [
      { name: 'iPhone', width: 375, height: 667 },
      { name: 'Android', width: 360, height: 640 },
      { name: 'tablet', width: 768, height: 1024 }
    ];
  }

  // Generar URLs de prueba para diferentes dispositivos
  generateTestUrls() {
    const tests = [];
    
    this.testDevices.forEach(device => {
      tests.push({
        device: device.name,
        url: this.baseUrl,
        viewport: `${device.width}x${device.height}`,
        checklist: this.getPWAChecklist()
      });
    });

    return tests;
  }

  getPWAChecklist() {
    return [
      '✅ Página se carga correctamente',
      '✅ Service Worker se registra',
      '✅ Botón de instalación aparece (si disponible)',
      '✅ Navegación funciona con toques',
      '✅ Textos son legibles (no muy pequeños)',
      '✅ Botones tiene tamaño táctil apropiado (>44px)',
      '✅ Página funciona en orientación portrait',
      '✅ Página funciona en orientación landscape',
      '✅ Cache funciona (recargar offline)',
      '✅ Notificaciones funcionan (si implementadas)'
    ];
  }

  generateManualTestGuide() {
    let guide = `
# 📱 Guía de Testing Móvil Manual - PWA Cantina Tita

## Dispositivos de Prueba Recomendados

### Smartphones
- iPhone (Safari): iOS 12+
- Android (Chrome): Android 7+
- Android (Firefox): última versión

### Tablets  
- iPad (Safari): iPadOS 13+
- Android Tablet (Chrome): Android 7+

## Checklist por Dispositivo

`;

    this.testDevices.forEach(device => {
      guide += `\n### ${device.name} (${device.width}x${device.height})\n`;
      guide += `**URL:** ${this.baseUrl}\n\n`;
      
      this.getPWAChecklist().forEach(check => {
        guide += `- [ ] ${check}\n`;
      });
      
      guide += '\n**Notas específicas:**\n';
      guide += `- Abrir DevTools -> Toggle device (${device.width}x${device.height})\n`;
      guide += '- Verificar en modo standalone si es posible\n';
      guide += '- Probar en red 3G simulada\n\n';
    });

    guide += `
## Pruebas Específicas de PWA

### 1. Instalación
- [ ] Aparece banner de instalación
- [ ] Se puede instalar desde menú del navegador
- [ ] Ícono aparece en pantalla principal
- [ ] Se abre en modo standalone

### 2. Service Worker
- [ ] Se registra correctamente (DevTools -> Application -> Service Workers)
- [ ] Cachea recursos estáticos
- [ ] Funciona offline (DevTools -> Network -> Offline)

### 3. Manifest
- [ ] /manifest.json es accesible
- [ ] Tiene todos los campos requeridos
- [ ] Íconos están disponibles en tamaños requeridos

### 4. Performance Móvil
- [ ] First Contentful Paint < 2s
- [ ] Largest Contentful Paint < 2.5s  
- [ ] Cumulative Layout Shift < 0.1
- [ ] First Input Delay < 100ms

### 5. Accesibilidad Móvil
- [ ] Touch targets ≥ 44px
- [ ] Contraste suficiente
- [ ] Texto escalable
- [ ] Navegable por teclado virtual

## Herramientas de Testing

### Chrome DevTools
1. F12 → Toggle Device Toolbar
2. Seleccionar dispositivo o viewport custom
3. Application tab → Manifest, Service Workers
4. Lighthouse tab → PWA audit

### Firefox DevTools  
1. F12 → Responsive Design Mode
2. Application tab (solo en Developer Edition)

### Safari Web Inspector (Mac)
1. Develop → Enter Responsive Design Mode
2. Web Inspector → Application (iOS 11.3+)

## Automatizar con Scripts

\`\`\`bash
# Ejecutar tests automáticos  
npm run test:mobile

# Solo Lighthouse móvil
npm run audit:mobile

# Tests Cypress en móvil
npm run test:pwa:mobile
\`\`\`
`;

    return guide;
  }

  async writeTestGuide() {
    const fs = require('fs').promises;
    const guide = this.generateManualTestGuide();
    
    try {
      await fs.writeFile('MOBILE_TESTING_GUIDE.md', guide);
      console.log('✅ Guía de testing móvil creada: MOBILE_TESTING_GUIDE.md');
    } catch (error) {
      console.log('❌ Error escribiendo guía:', error.message);
    }
  }

  displayQuickTest() {
    console.log('📱 QUICK MOBILE TEST CHECKLIST\n');
    console.log('Copy this URL to different devices:');
    console.log(`🔗 ${this.baseUrl}\n`);
    
    console.log('Essential PWA Checks:');
    this.getPWAChecklist().forEach((check, index) => {
      console.log(`${index + 1}. ${check}`);
    });
    
    console.log('\n💡 Tip: Use Chrome DevTools Device Mode for quick testing');
    console.log('💡 Tip: Run `node scripts/mobile-device-test.js` for automated testing');
  }
}

// Export
module.exports = SimpleMobileTest;

// Run if called directly
if (require.main === module) {
  const tester = new SimpleMobileTest();
  tester.displayQuickTest();
  
  // Create guide file
  tester.writeTestGuide().catch(console.error);
}