const puppeteer = require('puppeteer-core');

async function screenshot() {
  const targets = [
    'http://localhost:9222',
    'http://127.0.0.1:9222',
    'http://172.17.0.1:9222',
    'http://172.17.0.3:9222',
    'http://172.17.0.4:9222',
    'http://172.17.0.5:9222',
  ];

  let browser;
  let wsEndpoint = null;

  // Try to find the browser
  for (const target of targets) {
    try {
      console.log(`Trying ${target}...`);
      const resp = await fetch(`${target}/json/version`);
      if (resp.ok) {
        const data = await resp.json();
        wsEndpoint = data.webSocketDebuggerUrl;
        console.log(`Found browser at ${target}, WS: ${wsEndpoint}`);
        break;
      }
    } catch (e) {
      console.log(`Failed ${target}: ${e.message}`);
    }
  }

  if (!wsEndpoint) {
    console.log('Could not find browser. Trying direct connect...');
    // Try to connect directly
    try {
      browser = await puppeteer.connect({
        browserURL: 'http://localhost:9222',
      });
    } catch (e) {
      console.log('Direct connect failed:', e.message);
      process.exit(1);
    }
  } else {
    browser = await puppeteer.connect({ browserWSEndpoint: wsEndpoint });
  }

  const page = await browser.newPage();
  await page.goto('http://127.0.0.1:18789/chat?session=main', { waitUntil: 'networkidle2', timeout: 30000 });
  await page.screenshot({ path: '/home/sandbox/screenshot.png', fullPage: true });
  console.log('Screenshot saved to /home/sandbox/screenshot.png');
  
  await browser.close();
}

screenshot().catch(console.error);
