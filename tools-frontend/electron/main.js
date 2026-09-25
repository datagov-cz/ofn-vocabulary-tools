const { app, BrowserWindow, dialog } = require('electron');
const { spawn } = require('child_process');
const http = require('http');
const path = require('path');

let backend;
const port = process.env.OFN_PORT || '5127';
const root = path.resolve(__dirname, '..');

function pythonExecutable() {
  if (process.env.OFN_PYTHON) return process.env.OFN_PYTHON;
  return process.platform === 'win32'
    ? path.join(root, '.venv', 'Scripts', 'python.exe')
    : path.join(root, '.venv', 'bin', 'python');
}

function waitForServer(attempt = 0) {
  return new Promise((resolve, reject) => {
    http.get(`http://127.0.0.1:${port}/api/health`, (response) => {
      response.resume(); resolve();
    }).on('error', () => {
      if (attempt > 100) return reject(new Error('The local service did not start.'));
      setTimeout(() => waitForServer(attempt + 1).then(resolve, reject), 100);
    });
  });
}

async function launch() {
  backend = spawn(pythonExecutable(), [path.join(root, 'app.py')], {
    cwd: root,
    env: { ...process.env, PORT: port, HOST: '127.0.0.1', PYTHONUNBUFFERED: '1' },
    windowsHide: true,
  });
  backend.stderr.on('data', (data) => process.stderr.write(data));
  try { await waitForServer(); }
  catch (error) { dialog.showErrorBox('OFN Workbench', error.message); app.quit(); return; }
  const window = new BrowserWindow({ width: 1240, height: 850, minWidth: 850, minHeight: 650,
    backgroundColor: '#f4f1e9', autoHideMenuBar: true,
    webPreferences: { contextIsolation: true, sandbox: true } });
  await window.loadURL(`http://127.0.0.1:${port}`);
}

app.whenReady().then(launch);
app.on('window-all-closed', () => app.quit());
app.on('before-quit', () => { if (backend) backend.kill(); });
