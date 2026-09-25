const tabs = [...document.querySelectorAll('[role="tab"]')];
const panels = [...document.querySelectorAll('[role="tabpanel"]')];

function activateTab(name, updateHash = true) {
  tabs.forEach((tab) => tab.setAttribute('aria-selected', String(tab.dataset.tab === name)));
  panels.forEach((panel) => {
    const active = panel.id === name;
    panel.hidden = !active;
    panel.classList.toggle('active', active);
  });
  if (updateHash) history.replaceState(null, '', `#${name}`);
}

tabs.forEach((tab, index) => {
  tab.addEventListener('click', () => activateTab(tab.dataset.tab));
  tab.addEventListener('keydown', (event) => {
    if (!['ArrowLeft', 'ArrowRight'].includes(event.key)) return;
    const offset = event.key === 'ArrowRight' ? 1 : -1;
    const next = tabs[(index + offset + tabs.length) % tabs.length];
    next.focus(); activateTab(next.dataset.tab);
  });
});

document.querySelectorAll('input[type="file"]').forEach((input) => {
  input.addEventListener('change', () => {
    input.closest('.dropzone').querySelector('.filename').textContent = input.files[0]?.name || '';
  });
});

const converter = document.querySelector('#converter');
converter.addEventListener('change', () => {
  const option = converter.selectedOptions[0];
  const input = converter.closest('form').querySelector('input[type="file"]');
  input.value = ''; input.accept = option.dataset.accept;
  converter.closest('form').querySelector('.filename').textContent = '';
  converter.closest('form').querySelector('.accept-copy').textContent = option.dataset.accept.replaceAll('.', '').toUpperCase();
  converter.closest('form').querySelector('.with-view').hidden = converter.value !== 'table-to-archi';
});

function downloadBlob(blob, disposition) {
  const match = disposition?.match(/filename\*?=(?:UTF-8''|["']?)([^"';]+)/i);
  const filename = match ? decodeURIComponent(match[1].replace(/["']/g, '')) : 'download';
  const url = URL.createObjectURL(blob);
  const link = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
}

document.querySelectorAll('[data-download-form]').forEach((form) => {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    const message = form.querySelector('.form-message');
    button.disabled = true; button.classList.add('loading'); message.textContent = 'Processing…'; message.className = 'form-message';
    try {
      const response = await fetch(form.action, { method: 'POST', body: new FormData(form) });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        throw new Error(body.error || `Request failed (${response.status})`);
      }
      downloadBlob(await response.blob(), response.headers.get('Content-Disposition'));
      message.textContent = 'Complete — your download is ready.'; message.classList.add('success');
    } catch (error) {
      message.textContent = error.message; message.classList.add('error');
    } finally {
      button.disabled = false; button.classList.remove('loading');
    }
  });
});

const initial = location.hash.slice(1);
if (panels.some((panel) => panel.id === initial)) activateTab(initial, false);
