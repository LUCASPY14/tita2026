# 📊 EXPORTAR DIAGRAMAS A PDF/PNG
## Sistema Cantina TITA

---

## 🎯 Archivos HTML Creados

Se han creado **5 archivos HTML** en `docs/diagramas/` listos para exportar:

1. **01_DER_CORE_Tarjetas.html** - DER CORE (Tarjetas y Cargas)
2. **02_DER_CLIENTES.html** - DER Clientes (Gestión de clientes e hijos)
3. **03_DER_VENTAS.html** - DER Ventas (Transacciones y facturación)
4. **04_DER_INVENTARIO.html** - DER Inventario (Stock y lotes)
5. **05_DESPLIEGUE.html** - Arquitectura de Despliegue (Landscape)

---

## 🖨️ OPCIÓN 1: Exportar a PDF (Recomendado)

### Método 1: Navegador Web (Chrome/Edge)

1. **Abrir archivo HTML**:
   ```
   Click derecho en archivo .html → "Open with Live Server"
   O doble-click para abrir en navegador
   ```

2. **Imprimir/Guardar como PDF**:
   - Presionar `Ctrl+P` (Windows) o `Cmd+P` (Mac)
   - En "Destino/Destination": Seleccionar **"Guardar como PDF"** o **"Save as PDF"**
   - Configuración recomendada:
     * **Tamaño**: Letter (8.5 x 11 pulgadas)
     * **Orientación**: Portrait (vertical) para DER, Landscape (horizontal) para Despliegue
     * **Márgenes**: Predeterminados
     * **Escala**: 100%
   - Click en **"Guardar"** o **"Save"**

3. **Resultado**:
   - PDF de alta calidad listo para impresión
   - Tamaño carta (8.5" x 11")
   - Diagramas renderizados con Mermaid.js

---

## 📸 OPCIÓN 2: Exportar a PNG (Alta calidad)

### Método 1: Extensión de Chrome "Full Page Screen Capture"

1. **Instalar extensión**:
   - Chrome Web Store → Buscar "Full Page Screen Capture"
   - Instalar extensión

2. **Capturar**:
   - Abrir archivo HTML en Chrome
   - Click en icono de extensión
   - Guardar imagen PNG

### Método 2: Screenshot en VS Code

1. **Abrir Preview**:
   ```
   Abrir archivo .html en VS Code
   Click derecho → "Open Preview"
   ```

2. **Capturar**:
   - Windows: Win+Shift+S (Snipping Tool)
   - Guardar como PNG

---

## 🚀 OPCIÓN 3: Script Automatizado (PowerShell)

He creado un script para automatizar la exportación usando Puppeteer (requiere Node.js):

### Instalación de dependencias:

```powershell
# Instalar Node.js si no lo tienes
# Descargar de: https://nodejs.org/

# Navegar a la carpeta del proyecto
cd D:\tita2026\cantina_tita

# Crear carpeta para script
New-Item -ItemType Directory -Force -Path "scripts/export-diagrams"
cd scripts/export-diagrams

# Inicializar npm
npm init -y

# Instalar Puppeteer
npm install puppeteer
```

### Script de exportación:

Crear archivo `export-to-pdf.js`:

```javascript
const puppeteer = require('puppeteer');
const path = require('path');
const fs = require('fs');

const files = [
    '01_DER_CORE_Tarjetas.html',
    '02_DER_CLIENTES.html',
    '03_DER_VENTAS.html',
    '04_DER_INVENTARIO.html',
    '05_DESPLIEGUE.html'
];

(async () => {
    const browser = await puppeteer.launch();
    const page = await browser.newPage();
    
    for (const file of files) {
        const htmlPath = path.join(__dirname, '../../docs/diagramas', file);
        const pdfPath = htmlPath.replace('.html', '.pdf');
        const pngPath = htmlPath.replace('.html', '.png');
        
        console.log(`Procesando: ${file}`);
        
        // Configuración según archivo
        const isLandscape = file.includes('DESPLIEGUE');
        
        await page.goto(`file://${htmlPath}`, { waitUntil: 'networkidle0' });
        
        // Esperar a que Mermaid renderice
        await page.waitForTimeout(3000);
        
        // Exportar a PDF
        await page.pdf({
            path: pdfPath,
            format: 'Letter',
            landscape: isLandscape,
            margin: {
                top: '0.5in',
                right: '0.5in',
                bottom: '0.5in',
                left: '0.5in'
            },
            printBackground: true
        });
        
        console.log(`✅ PDF creado: ${path.basename(pdfPath)}`);
        
        // Exportar a PNG (alta resolución)
        await page.screenshot({
            path: pngPath,
            fullPage: true,
            type: 'png'
        });
        
        console.log(`✅ PNG creado: ${path.basename(pngPath)}`);
    }
    
    await browser.close();
    console.log('\n🎉 ¡Exportación completada!');
})();
```

### Ejecutar script:

```powershell
cd D:\tita2026\cantina_tita\scripts\export-diagrams
node export-to-pdf.js
```

---

## 📋 OPCIÓN 4: Desde VS Code (Sin código)

### Usando extensión "Markdown PDF"

1. **Instalar extensión**:
   ```
   Ctrl+Shift+X → Buscar "Markdown PDF" → Instalar
   ```

2. **Configurar para Mermaid**:
   ```json
   // settings.json
   {
     "markdown-pdf.executablePath": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
     "markdown-pdf.format": "Letter"
   }
   ```

3. **Exportar**:
   - Abrir archivo .md con diagramas
   - Ctrl+Shift+P → "Markdown PDF: Export (pdf)"

---

## ✅ Configuración Óptima de Impresión

### Para DER (01-04):
- **Orientación**: Portrait (Vertical)
- **Tamaño**: Letter (8.5" x 11")
- **Márgenes**: 0.5" en todos lados
- **Color**: Sí (color)
- **Calidad**: Alta

### Para Despliegue (05):
- **Orientación**: Landscape (Horizontal) ⚠️ IMPORTANTE
- **Tamaño**: Letter (8.5" x 11")
- **Márgenes**: 0.5" en todos lados
- **Color**: Sí (color)
- **Calidad**: Alta

---

## 🎨 Personalización

Para cambiar colores, tamaños o estilos, editar archivo HTML:

```html
<!-- Cambiar tema de Mermaid -->
<script>
    mermaid.initialize({ 
        startOnLoad: true,
        theme: 'dark',  // Opciones: default, dark, forest, neutral
        themeVariables: { 
            fontSize: '16px'  // Ajustar tamaño de fuente
        }
    });
</script>

<!-- Cambiar colores de fondo -->
<style>
    .container {
        background: #f0f0f0;  /* Color de fondo */
    }
</style>
```

---

## 📁 Estructura de Archivos

```
docs/
└── diagramas/
    ├── 01_DER_CORE_Tarjetas.html
    ├── 01_DER_CORE_Tarjetas.pdf      (después de exportar)
    ├── 01_DER_CORE_Tarjetas.png      (después de exportar)
    ├── 02_DER_CLIENTES.html
    ├── 02_DER_CLIENTES.pdf
    ├── 02_DER_CLIENTES.png
    ├── 03_DER_VENTAS.html
    ├── 03_DER_VENTAS.pdf
    ├── 03_DER_VENTAS.png
    ├── 04_DER_INVENTARIO.html
    ├── 04_DER_INVENTARIO.pdf
    ├── 04_DER_INVENTARIO.png
    ├── 05_DESPLIEGUE.html
    ├── 05_DESPLIEGUE.pdf
    └── 05_DESPLIEGUE.png
```

---

## 🎯 Recomendación

**Método más simple**: 
1. Abrir archivo HTML en navegador (Chrome/Edge)
2. Presionar `Ctrl+P`
3. Seleccionar "Guardar como PDF"
4. ✅ Listo!

**Para producción profesional**: 
- Usar script de Puppeteer para exportación automática
- Asegura consistencia en todos los diagramas
- Calidad optimizada para impresión

---

## ❓ Troubleshooting

### Los diagramas no se ven en el HTML
- **Solución**: Esperar 3-5 segundos después de abrir el archivo (Mermaid necesita cargar)

### PDF muestra página en blanco
- **Solución**: En opciones de impresión, activar "Background graphics" o "Gráficos de fondo"

### Diagrama muy pequeño/grande
- **Solución**: Ajustar escala en opciones de impresión (90-110%)

---

**¡Listo para imprimir! 🎉**
