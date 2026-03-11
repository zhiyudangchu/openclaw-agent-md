const net = require('net');

async function scanPort(ip, port, timeout = 500) {
  return new Promise((resolve) => {
    const socket = new net.Socket();
    let found = false;
    
    socket.setTimeout(timeout);
    
    socket.on('connect', () => {
      found = true;
      socket.destroy();
      resolve(true);
    });
    
    socket.on('timeout', () => {
      socket.destroy();
      resolve(false);
    });
    
    socket.on('error', () => {
      resolve(false);
    });
    
    socket.connect(port, ip);
  });
}

async function scan() {
  console.log('Scanning for CDP port 9222...\n');
  
  // Scan common Docker bridge IPs
  const targets = [
    '172.17.0.1',  // Docker gateway
    '172.17.0.3',
    '172.17.0.4',
    '172.17.0.5',
    '172.17.0.6',
    '172.17.0.7',
    '172.17.0.8',
    '172.17.0.9',
    '172.17.0.10',
  ];
  
  for (const ip of targets) {
    const found = await scanPort(ip, 9222, 300);
    if (found) {
      console.log(`✓ Found CDP at ${ip}:9222`);
      return ip;
    }
    console.log(`✗ ${ip}:9222 - closed`);
  }
  
  console.log('\nNo CDP found on scanned IPs');
  return null;
}

scan().then(ip => {
  if (ip) {
    console.log(`\nBrowser found at ${ip}:9222`);
  }
});
