/**
 * Test inicial para verificar que Playwright funciona
 */
const { devices } = require('@playwright/test');

async function testPlaywrightSetup() {
  console.log('🧪 Testing Playwright setup...\n');
  
  try {
    const { chromium } = require('playwright');
    console.log('✅ Playwright imported successfully');
    
    // Test browser launch
    const browser = await chromium.launch({ headless: true });
    console.log('✅ Chrome browser launched');
    
    // Test device context
    const iPhone = devices['iPhone 12'];
    const context = await browser.newContext(iPhone);
    console.log('✅ iPhone 12 device context created');
    
    const page = await context.newPage();
    console.log('✅ New page created');
    
    // Test navigation
    await page.goto('https://www.google.com');
    const title = await page.title();
    console.log(`✅ Navigation successful: ${title}`);
    
    await browser.close();
    console.log('✅ Browser closed');
    
    console.log('\n🎉 Playwright setup is working correctly!');
    console.log('💡 You can now run: npm run test:mobile');
    
  } catch (error) {
    console.log('❌ Playwright test failed:', error.message);
    console.log('💡 Try running: npx playwright install');
  }
}

if (require.main === module) {
  testPlaywrightSetup();
}

module.exports = testPlaywrightSetup;