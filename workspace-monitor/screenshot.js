const puppeteer = require('puppeteer');

(async () => {
  const browser = await puppeteer.launch({
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
  });
  
  const page = await browser.newPage();
  await page.setViewport({ width: 1920, height: 1080 });
  
  const searchUrl = 'https://search.eastmoney.com/search.html?keyword=中国石油';
  console.log('Opening:', searchUrl);
  
  await page.goto(searchUrl, { waitUntil: 'networkidle2', timeout: 30000 });
  await page.waitForTimeout(3000);
  
  await page.screenshot({ path: '/home/sandbox/中国石油_东方财富.png', fullPage: true });
  console.log('Screenshot saved to /home/sandbox/中国石油_东方财富.png');
  
  await browser.close();
})();
