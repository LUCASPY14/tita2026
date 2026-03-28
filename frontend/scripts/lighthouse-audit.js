const lighthouse = require('lighthouse');
const chromeLauncher = require('chrome-launcher');
const fs = require('fs');
const path = require('path');

/**
 * Script de auditoría automatizada con Lighthouse
 * Genera reportes de performance, PWA, SEO, etc.
 */

const CONFIG = {
  // URLs a auditar
  urls: [
    'http://localhost:3000',
    'http://localhost:3000/login', 
    'http://localhost:3000/dashboard',
    'http://localhost:3000/ventas',
    'http://localhost:3000/productos',
    'http://localhost:3000/clientes',
  ],
  
  // Opciones de Lighthouse
  options: {
    logLevel: 'info',
    output: 'html',
    onlyCategories: ['performance', 'pwa', 'best-practices', 'seo', 'accessibility'],
    port: 0,
  },

  // Configuración específica PWA
  config: {
    extends: 'lighthouse:default',
    settings: {
      onlyAudits: [
        // Performance
        'first-contentful-paint',
        'largest-contentful-paint',
        'first-meaningful-paint',
        'speed-index',
        'total-blocking-time',
        'cumulative-layout-shift',
        
        // PWA
        'service-worker',
        'works-offline',
        'installable-manifest',
        'splash-screen',
        'themed-omnibox',
        'content-width',
        'viewport',
        'apple-touch-icon',
        'manifest-short-name-length',
        
        // Best Practices
        'uses-https',
        'redirects-http',
        
        // SEO
        'document-title',
        'meta-description',
        
        // Accessibility
        'color-contrast',
        'image-alt',
      ],
    },
  },
};

/**
 * Lanza Chrome y ejecuta auditoría
 * @param {string} url - URL a auditar
 * @returns {Promise<Object>} Resultado de la auditoría
 */
async function runLighthouse(url) {
  const chrome = await chromeLauncher.launch({
    chromeFlags: [
      '--headless',
      '--disable-gpu',
      '--no-sandbox',
      '--disable-dev-shm-usage',
      '--disable-extensions',
    ]
  });

  CONFIG.options.port = chrome.port;
  
  try {
    console.log(`🔍 Auditando: ${url}`);
    const results = await lighthouse(url, CONFIG.options, CONFIG.config);
    return results;
  } finally {
    await chrome.kill();
  }
}

/**
 * Genera reporte HTML individual
 * @param {Object} results - Resultados de Lighthouse
 * @param {string} url - URL auditada
 * @param {string} outputDir - Directorio de salida
 */
function saveReport(results, url, outputDir) {
  if (!fs.existsSync(outputDir)) {
    fs.mkdirSync(outputDir, { recursive: true });
  }
  
  const urlPath = url.replace(/[^a-zA-Z0-9]/g, '_');
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  const filename = `lighthouse_${urlPath}_${timestamp}.html`;
  const filepath = path.join(outputDir, filename);
  
  fs.writeFileSync(filepath, results.report);
  console.log(`📄 Reporte guardado: ${filepath}`);
  
  return { filepath, filename };
}

/**
 * Extrae métricas clave de los resultados
 * @param {Object} results - Resultados de Lighthouse
 * @returns {Object} Métricas procesadas
 */
function extractMetrics(results, url) {
  const score = (value) => Math.round((value || 0) * 100);
  
  const audits = results.lhr.audits;
  const categories = results.lhr.categories;
  
  return {
    url,
    timestamp: new Date().toISOString(),
    scores: {
      performance: score(categories.performance?.score),
      pwa: score(categories.pwa?.score),
      bestPractices: score(categories['best-practices']?.score),
      seo: score(categories.seo?.score),
      accessibility: score(categories.accessibility?.score),
    },
    metrics: {
      fcp: audits['first-contentful-paint']?.numericValue || 0,
      lcp: audits['largest-contentful-paint']?.numericValue || 0,
      fmp: audits['first-meaningful-paint']?.numericValue || 0,
      si: audits['speed-index']?.numericValue || 0,
      tbt: audits['total-blocking-time']?.numericValue || 0,
      cls: audits['cumulative-layout-shift']?.numericValue || 0,
    },
    pwa: {
      serviceWorker: audits['service-worker']?.score === 1,
      worksOffline: audits['works-offline']?.score === 1,
      installable: audits['installable-manifest']?.score === 1,
      splashScreen: audits['splash-screen']?.score === 1,
    }
  };
}

/**
 * Genera reporte consolidado JSON
 * @param {Array} allMetrics - Métricas de todas las URLs
 * @param {string} outputDir - Directorio de salida
 */
function generateConsolidatedReport(allMetrics, outputDir) {
  const timestamp = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  
  const summary = {
    timestamp,
    totalUrls: allMetrics.length,
    averageScores: {
      performance: Math.round(allMetrics.reduce((sum, m) => sum + m.scores.performance, 0) / allMetrics.length),
      pwa: Math.round(allMetrics.reduce((sum, m) => sum + m.scores.pwa, 0) / allMetrics.length),
      bestPractices: Math.round(allMetrics.reduce((sum, m) => sum + m.scores.bestPractices, 0) / allMetrics.length),
      seo: Math.round(allMetrics.reduce((sum, m) => sum + m.scores.seo, 0) / allMetrics.length),
      accessibility: Math.round(allMetrics.reduce((sum, m) => sum + m.scores.accessibility, 0) / allMetrics.length),
    },
    pwaStatus: {
      allHaveServiceWorker: allMetrics.every(m => m.pwa.serviceWorker),
      allWorkOffline: allMetrics.every(m => m.pwa.worksOffline),
      allInstallable: allMetrics.every(m => m.pwa.installable),
    },
    details: allMetrics,
  };
  
  const reportPath = path.join(outputDir, `lighthouse_summary_${timestamp}.json`);
  fs.writeFileSync(reportPath, JSON.stringify(summary, null, 2));
  
  console.log(`\n📊 RESUMEN DE AUDITORÍA`);
  console.log(`=========================`);
  console.log(`URLs auditadas: ${summary.totalUrls}`);
  console.log(`Performance promedio: ${summary.averageScores.performance}%`);
  console.log(`PWA promedio: ${summary.averageScores.pwa}%`);
  console.log(`Best Practices promedio: ${summary.averageScores.bestPractices}%`);
  console.log(`SEO promedio: ${summary.averageScores.seo}%`);
  console.log(`Accessibility promedio: ${summary.averageScores.accessibility}%`);
  console.log(`\n🚀 PWA Status:`);
  console.log(`Service Worker: ${summary.pwaStatus.allHaveServiceWorker ? '✅' : '❌'}`);
  console.log(`Offline: ${summary.pwaStatus.allWorkOffline ? '✅' : '❌'}`);
  console.log(`Installable: ${summary.pwaStatus.allInstallable ? '✅' : '❌'}`);
  console.log(`\n📄 Reporte detallado: ${reportPath}`);
  
  return reportPath;
}

/**
 * Función principal - ejecuta auditorías para todas las URLs
 */
async function main() {
  console.log('🚀 Iniciando auditorías Lighthouse...\n');
  
  const outputDir = path.join(__dirname, 'lighthouse-reports');
  const allMetrics = [];
  
  try {
    // Verificar que el server esté corriendo
    console.log('📡 Verificando servidor en localhost:3000...');
    
    // Ejecutar auditorías para cada URL
    for (const url of CONFIG.urls) {
      try {
        const results = await runLighthouse(url);
        const reportInfo = saveReport(results, url, outputDir);
        const metrics = extractMetrics(results, url);
        allMetrics.push(metrics);
        
        // Mostrar scores individuales
        console.log(`   Performance: ${metrics.scores.performance}% | PWA: ${metrics.scores.pwa}% | BP: ${metrics.scores.bestPractices}%\n`);
        
      } catch (error) {
        console.error(`❌ Error auditando ${url}:`, error.message);
      }
    }
    
    if (allMetrics.length > 0) {
      generateConsolidatedReport(allMetrics, outputDir);
    } else {
      console.error('❌ No se pudieron completar auditorías');
      process.exit(1);
    }
    
  } catch (error) {
    console.error('❌ Error general:', error);
    process.exit(1);
  }
}

// Ejecutar auditoría si se llama directamente
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { runLighthouse, extractMetrics, CONFIG };