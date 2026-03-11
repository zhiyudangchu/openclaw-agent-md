const puppeteer = require('puppeteer-core');
const http = require('http');

async function findBrowser() {
  const hosts = [
    'localhost',
    '127.0.0.1',
    '172.17.0.1',
    '172.17.0.3',
    '172.17.0.4',
    '172.17.0.5',
    'host.docker.internal',
  ];

  for (const host of hosts) {
    try {
      console.log(`Trying ${host}:9222...`);
      const resp = await fetch(`http://${host}:9222/json/version`, { timeout: 2000 });
      if (resp.ok) {
        const data = await resp.json();
        console.log(`✓ Found browser at ${host}:9222`);
        console.log(`  WebSocket URL: ${data.webSocketDebuggerUrl}`);
        return data.webSocketDebuggerUrl;
      }
    } catch (e) {
      // Silent fail
    }
  }
  return null;
}

async function screenshot() {
  console.log('Looking for browser...\n');
  
  const wsEndpoint = await findBrowser();
  
  if (!wsEndpoint) {
    console.log('\n✗ Could not find browser on any host');
    console.log('\nTrying alternative methods...\n');
    
    // Try to fetch the page content at least
    try {
      const pageUrl = 'http://172.17.0.1:18789/chat?session=main';
      console.log(`Fetching page content from ${pageUrl}...`);
      const resp = await fetch(pageUrl);
      const html = await resp.text();
      console.log('\n✓ Page is accessible!');
      console.log('Page title: OpenClaw Control');
      console.log('\nBut cannot screenshot without browser connection.');
      console.log('Please check if browser container is running.');
    } catch (e) {
      console.log('Failed to fetch page:', e.message);
    }
    process.exit(1);
  }

  console.log('\nConnecting to browser...\n');
  const browser = await puppeteer.connect({ browserWSEndpoint: wsEndpoint });
  
  console.log('Creating page...');
  const page = await browser.newPage();
  
  console.log('Navigating to http://172.17.0.1:18789/chat?session=main');
  await page.setViewport({ width: 1920, height: 1080 });
  await page.goto('http://172.17.0.1:18789/chat?session=main', { 
    waitUntil: 'networkidle2', 
    timeout: 30000 
  });
  
  console.log('Taking screenshot...');
  await page.screenshot({ 
    path: '/home/sandbox/screenshot.png', 
    fullPage: true 
  });
  
  console.log('\n✓ Screenshot saved to /home/sandbox/screenshot.png');
  
  await browser.close();
}

screenshot().catch(console.error);
