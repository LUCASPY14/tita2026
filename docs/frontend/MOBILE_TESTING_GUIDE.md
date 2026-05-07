
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


### iPhone (375x667)
**URL:** http://localhost:3000

- [ ] ✅ Página se carga correctamente
- [ ] ✅ Service Worker se registra
- [ ] ✅ Botón de instalación aparece (si disponible)
- [ ] ✅ Navegación funciona con toques
- [ ] ✅ Textos son legibles (no muy pequeños)
- [ ] ✅ Botones tiene tamaño táctil apropiado (>44px)
- [ ] ✅ Página funciona en orientación portrait
- [ ] ✅ Página funciona en orientación landscape
- [ ] ✅ Cache funciona (recargar offline)
- [ ] ✅ Notificaciones funcionan (si implementadas)

**Notas específicas:**
- Abrir DevTools -> Toggle device (375x667)
- Verificar en modo standalone si es posible
- Probar en red 3G simulada


### Android (360x640)
**URL:** http://localhost:3000

- [ ] ✅ Página se carga correctamente
- [ ] ✅ Service Worker se registra
- [ ] ✅ Botón de instalación aparece (si disponible)
- [ ] ✅ Navegación funciona con toques
- [ ] ✅ Textos son legibles (no muy pequeños)
- [ ] ✅ Botones tiene tamaño táctil apropiado (>44px)
- [ ] ✅ Página funciona en orientación portrait
- [ ] ✅ Página funciona en orientación landscape
- [ ] ✅ Cache funciona (recargar offline)
- [ ] ✅ Notificaciones funcionan (si implementadas)

**Notas específicas:**
- Abrir DevTools -> Toggle device (360x640)
- Verificar en modo standalone si es posible
- Probar en red 3G simulada


### tablet (768x1024)
**URL:** http://localhost:3000

- [ ] ✅ Página se carga correctamente
- [ ] ✅ Service Worker se registra
- [ ] ✅ Botón de instalación aparece (si disponible)
- [ ] ✅ Navegación funciona con toques
- [ ] ✅ Textos son legibles (no muy pequeños)
- [ ] ✅ Botones tiene tamaño táctil apropiado (>44px)
- [ ] ✅ Página funciona en orientación portrait
- [ ] ✅ Página funciona en orientación landscape
- [ ] ✅ Cache funciona (recargar offline)
- [ ] ✅ Notificaciones funcionan (si implementadas)

**Notas específicas:**
- Abrir DevTools -> Toggle device (768x1024)
- Verificar en modo standalone si es posible
- Probar en red 3G simulada


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

```bash
# Ejecutar tests automáticos  
npm run test:mobile

# Solo Lighthouse móvil
npm run audit:mobile

# Tests Cypress en móvil
npm run test:pwa:mobile
```
