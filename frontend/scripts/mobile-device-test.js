/**
 * Script para testing móvil con simulación de dispositivos reales
 * Utiliza Playwright para testing cross-browser y dispositivos
 */
const { devices, test, expect } = require('@playwright/test');
const fs = require('fs').promises;
const path = require('path');

class MobileDeviceTest {
  constructor() {
    this.baseUrl = 'http://localhost:3000';
    this.devices = [
      // iOS Devices
      { name: 'iPhone 12', device: devices['iPhone 12'] },
      { name: 'iPhone 12 Pro', device: devices['iPhone 12 Pro'] },
      { name: 'iPhone SE', device: devices['iPhone SE'] },
      { name: 'iPad', device: devices['iPad'] },
      
      // Android Devices
      { name: 'Pixel 5', device: devices['Pixel 5'] },
      { name: 'Galaxy S21', device: devices['Galaxy S21+'] },
      { name: 'Galaxy Tab S4', device: devices['Galaxy Tab S4'] }
    ];
    
    this.pwaFeatures = [
      'Service Worker Registration',
      'Manifest Validation', 
      'Install Prompt',
      'Offline Functionality',
      'Push Notifications',
      'Background Sync'
    ];
    
    this.results = {};
  }

  async checkManifest() {
    const manifestUrl = `${this.baseUrl}/manifest.json`;
    try {
      const response = await fetch(manifestUrl);
      if (response.ok) {
        const manifest = await response.json();
        return {
          valid: true,
          data: manifest,
          errors: []
        };
      }
      return { valid: false, errors: [`HTTP ${response.status}`] };
    } catch (error) {
      return { valid: false, errors: [error.message] };
    }
  }

  async testDevice(deviceName, deviceConfig) {
    console.log(`\n🧪 Testing ${deviceName}...`);
    
    const { chromium } = require('playwright');
    const browser = await chromium.launch({ headless: true });
    const context = await browser.newContext(deviceConfig);
    const page = await context.newPage();

    const deviceResults = {
      device: deviceName,
      timestamp: new Date().toISOString(),
      tests: {}
    };

    try {
      // 1. Basic Navigation
      console.log(`  📱 Basic navigation...`);
      await page.goto(this.baseUrl);
      await page.waitForLoadState('networkidle');
      
      deviceResults.tests.navigation = {
        passed: await page.locator('body').isVisible(),
        loadTime: await this.measureLoadTime(page)
      };

      // 2. Service Worker Check
      console.log(`  ⚙️  Service Worker check...`);
      const swRegistered = await page.evaluate(() => {
        return 'serviceWorker' in navigator;
      });
      
      const swActive = await page.evaluate(async () => {
        if ('serviceWorker' in navigator) {
          const registration = await navigator.serviceWorker.getRegistration();
          return registration && registration.active;
        }
        return false;
      });

      deviceResults.tests.serviceWorker = {
        supported: swRegistered,
        active: swActive
      };

      // 3. PWA Installation Check
      console.log(`  📲 PWA installation check...`);
      const installable = await this.checkPWAInstallable(page);
      deviceResults.tests.installation = installable;

      // 4. Offline Functionality
      console.log(`  🔌 Offline functionality...`);
      await context.setOffline(true);
      await page.reload();
      const offlineWorks = await page.locator('body').isVisible({ timeout: 5000 }).catch(() => false);
      await context.setOffline(false);
      
      deviceResults.tests.offline = { works: offlineWorks };

      // 5. Touch Interactions
      console.log(`  👆 Touch interactions...`);
      const touchTest = await this.testTouchInteractions(page);
      deviceResults.tests.touch = touchTest;

      // 6. Responsive Design
      console.log(`  📐 Responsive design...`);
      const responsive = await this.testResponsiveDesign(page, deviceConfig);
      deviceResults.tests.responsive = responsive;

      // 7. Performance Metrics
      console.log(`  🏃 Performance metrics...`);
      const performance = await this.getPerformanceMetrics(page);
      deviceResults.tests.performance = performance;

    } catch (error) {
      deviceResults.error = error.message;
      console.log(`  ❌ Error: ${error.message}`);
    } finally {
      await browser.close();
    }

    return deviceResults;
  }

  async checkPWAInstallable(page) {
    return await page.evaluate(async () => {
      // Check manifest
      const manifestLink = document.querySelector('link[rel="manifest"]');
      if (!manifestLink) return { installable: false, reason: 'No manifest link' };

      // Check service worker
      if (!('serviceWorker' in navigator)) {
        return { installable: false, reason: 'No service worker support' };
      }

      // Check if criteria are met
      const criteria = {
        manifest: !!manifestLink,
        serviceWorker: 'serviceWorker' in navigator,
        httpsOrLocalhost: location.protocol === 'https:' || location.hostname === 'localhost'
      };

      const allMet = Object.values(criteria).every(Boolean);
      
      return {
        installable: allMet,
        criteria,
        reason: allMet ? 'PWA installable' : 'Missing criteria'
      };
    });
  }

  async testTouchInteractions(page) {
    try { 
      // Find interactive elements
      const buttons = await page.locator('button').count();
      const links = await page.locator('a').count();
      
      if (buttons > 0) {
        const buttonBox = await page.locator('button').first().boundingBox();
        if (buttonBox) {
          // Test touch target size (minimum 44px recommended)
          const minSize = Math.min(buttonBox.width, buttonBox.height);
          const sizeGood = minSize >= 44;
          
          // Test touch interaction
          await page.locator('button').first().tap();
          
          return {
            touchTargetsFound: buttons + links,
            touchTargetSize: { 
              minimum: minSize, 
              acceptable: sizeGood 
            },
            tapWorking: true
          };
        }
      }
      
      return { touchTargetsFound: 0, accessible: false };
    } catch (error) {
      return { error: error.message };
    }
  }

  async testResponsiveDesign(page, deviceConfig) {
    const viewport = deviceConfig.viewport;
    
    try {
      // Test different orientations if mobile
      const tests = { portrait: null, landscape: null };
      
      if (viewport.width < viewport.height) {
        // Portrait test
        await page.setViewportSize({ 
          width: viewport.width, 
          height: viewport.height 
        });
        tests.portrait = await this.checkLayout(page);
        
        // Landscape test  
        await page.setViewportSize({ 
          width: viewport.height, 
          height: viewport.width 
        });
        tests.landscape = await this.checkLayout(page);
      } else {
        tests.landscape = await this.checkLayout(page);
      }
      
      return tests;
    } catch (error) {
      return { error: error.message };
    }
  }

  async checkLayout(page) {
    // Check if layout elements are visible and properly positioned
    const layout = await page.evaluate(() => {
      const header = document.querySelector('header, .header, nav');
      const main = document.querySelector('main, #root, .main-content');
      
      return {
        hasHeader: !!header,
        hasMain: !!main,
        headerVisible: header ? !!(header.offsetWidth || header.offsetHeight) : false,
        mainVisible: main ? !!(main.offsetWidth || main.offsetHeight) : false,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      };
    });
    
    return layout;
  }

  async measureLoadTime(page) {
    return await page.evaluate(() => {
      return performance.timing.loadEventEnd - performance.timing.navigationStart;
    });
  }

  async getPerformanceMetrics(page) {
    return await page.evaluate(() => {
      const navigation = performance.getEntriesByType('navigation')[0];
      const paint = performance.getEntriesByType('paint');
      
      return {
        loadTime: navigation?.loadEventEnd - navigation?.loadEventStart || 0,
        domContentLoaded: navigation?.domContentLoadedEventEnd - navigation?.domContentLoadedEventStart || 0,
        firstPaint: paint.find(p => p.name === 'first-paint')?.startTime || 0,
        firstContentfulPaint: paint.find(p => p.name === 'first-contentful-paint')?.startTime || 0
      };
    });
  }

  async runAllTests() {
    console.log('🚀 Starting Mobile Device PWA Testing...\n');
    
    // Check manifest first
    console.log('📄 Checking PWA Manifest...');
    const manifestCheck = await this.checkManifest();
    this.results.manifest = manifestCheck;
    
    if (!manifestCheck.valid) {
      console.log('❌ Manifest invalid, some tests may fail');
      console.log('Errors:', manifestCheck.errors);
    } else {
      console.log('✅ Manifest valid');
    }

    // Test each device
    for (const { name, device } of this.devices) {
      try {
        const result = await this.testDevice(name, device);
        this.results[name] = result;
        
        // Display summary for this device
        console.log(`\n📊 Results for ${name}:`);
        this.displayDeviceResults(result);
        
      } catch (error) {
        console.log(`❌ Failed testing ${name}: ${error.message}`);
        this.results[name] = { error: error.message };
      }
    }

    // Generate report
    await this.generateReport();
    console.log('\n✅ Mobile testing completed! Check mobile-test-report.html for details.');
  }

  displayDeviceResults(result) {
    const tests = result.tests || {};
    
    Object.entries(tests).forEach(([testName, testResult]) => {
      const status = this.getTestStatus(testResult);
      console.log(`  ${status} ${testName}`);
    });
  }

  getTestStatus(testResult) {
    if (testResult.error) return '❌';
    if (testResult.passed === false) return '❌';
    if (testResult.works === false) return '❌';
    if (testResult.active === false && testResult.supported === true) return '⚠️';
    return '✅';
  }

  async generateReport() {
    const reportHtml = this.generateHTMLReport();
    await fs.writeFile('mobile-test-report.html', reportHtml);
    
    const reportJson = JSON.stringify(this.results, null, 2);
    await fs.writeFile('mobile-test-report.json', reportJson);
  }

  generateHTMLReport() {
    let html = `
<!DOCTYPE html>
<html>
<head>
    <title>Mobile PWA Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .device { border: 1px solid #ddd; margin: 20px 0; padding: 20px; border-radius: 8px; }
        .device h2 { color: #2563eb; margin-top: 0; }
        .test { margin: 10px 0; padding: 8px; border-radius: 4px; }
        .test.pass { background: #d1fae5; border-left: 4px solid #10b981; }
        .test.fail { background: #fee2e2; border-left: 4px solid #ef4444; }
        .test.warn { background: #fef3c7; border-left: 4px solid #f59e0b; }
        .summary { background: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0; }
        pre { background: #f1f5f9; padding: 10px; border-radius: 4px; overflow-x: auto; }
    </style>
</head>
<body>
    <h1>📱 Mobile PWA Test Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p>Generated: ${new Date().toLocaleString()}</p>
        <p>Total Devices Tested: ${Object.keys(this.results).length - 1}</p>
    </div>
`;

    Object.entries(this.results).forEach(([deviceName, result]) => {
      if (deviceName === 'manifest') return;
      
      html += `
    <div class="device">
        <h2>${deviceName}</h2>
        <p>Tested: ${new Date(result.timestamp).toLocaleString()}</p>
`;

      if (result.error) {
        html += `<div class="test fail">Error: ${result.error}</div>`;
      } else if (result.tests) {
        Object.entries(result.tests).forEach(([testName, testResult]) => {
          const status = this.getTestStatus(testResult) === '✅' ? 'pass' : 
                        this.getTestStatus(testResult) === '⚠️' ? 'warn' : 'fail';
          
          html += `<div class="test ${status}">
            <strong>${testName}</strong>
            <pre>${JSON.stringify(testResult, null, 2)}</pre>
          </div>`;
        });
      }

      html += `</div>`;
    });

    html += `
</body>
</html>`;
    
    return html;
  }
}

// Export for use
module.exports = MobileDeviceTest;

// Run if called directly
if (require.main === module) {
  (async () => {
    const tester = new MobileDeviceTest();
    await tester.runAllTests();
  })().catch(console.error);
}