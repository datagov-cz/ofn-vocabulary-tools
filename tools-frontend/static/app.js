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
function updateVocabularyTool() {
  document.querySelectorAll('[data-converter-description]').forEach((description) => {
    description.hidden = description.dataset.converterDescription !== converter.value;
  });
  document.querySelectorAll('[data-converter-form]').forEach((form) => {
    form.hidden = form.dataset.converterForm !== converter.value;
  });
}
converter.addEventListener('change', updateVocabularyTool);
updateVocabularyTool();

function downloadBlob(blob, disposition) {
  const match = disposition?.match(/filename\*?=(?:UTF-8''|["']?)([^"';]+)/i);
  const filename = match ? decodeURIComponent(match[1].replace(/["']/g, '')) : 'download';
  const url = URL.createObjectURL(blob);
  const link = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(link); link.click(); link.remove(); URL.revokeObjectURL(url);
}

function sourceAttributeName(path, iri) {
  const parts = path.split('.').filter((part) => part && !/^\d+$/.test(part));
  const field = parts.at(-1);
  if (!field) return path;

  // Language and array positions describe JSON-LD structure, not source fields.
  if (['cs', 'en'].includes(field) && parts.length > 1) parts.pop();
  const sourceField = parts.at(-1);
  const parent = parts.at(-2);
  const sourceName = (value) => value.replaceAll('_', ' ');

  const serviceFields = ['přístupový_bod', 'popis_přístupového_bodu', 'právní_předpis', 'specifikace', 'dokumentace'];
  if (serviceFields.includes(sourceField)
      && (parent === 'přístupová_služba' || iri?.endsWith('/přístupová-služba'))) {
    return `přístupová služba - ${sourceName(sourceField)}`;
  }
  const usageFields = ['autorské_dílo', 'autor', 'databáze_jako_autorské_dílo', 'autor_databáze', 'databáze_chráněná_zvláštními_právy', 'osobní_údaje'];
  if (usageFields.includes(sourceField)
      && (parent === 'podmínky_užití' || iri?.endsWith('/specifikace-podmínek-užití'))) {
    return `podmínky užití - ${sourceName(sourceField)}`;
  }
  if (['jméno', 'e-mail'].includes(sourceField)) {
    const contactField = sourceField === 'e-mail' ? 'email' : sourceName(sourceField);
    return `kontaktní bod - ${contactField}`;
  }
  if (parent === 'časové_pokrytí' && ['začátek', 'konec'].includes(sourceField)) {
    return `časové pokrytí - ${sourceName(sourceField)}`;
  }
  return sourceName(sourceField);
}

function sourceValidationMessage(message) {
  const iri = message.match(/\bIRI '([^']+)'/)?.[1];
  const sourceIri = iri?.endsWith('/přístupová-služba')
    ? iri.slice(0, -'/přístupová-služba'.length)
    : iri;
  return message
    .replace(/^(Mandatory attribute|Attribute) '([^']+)'/, (_match, prefix, path) =>
      `${prefix} '${sourceAttributeName(path, iri)}'`)
    .replace(/\bIRI '([^']+)'/, (_match, originalIri) =>
      `IRI '${sourceIri || originalIri}'`);
}

function appendValidationMessage(item, message) {
  const boldParts = /(^\b(?:Mandatory attribute|Attribute) |\bentry with name )(['"])(.*?)\2/g;
  let cursor = 0;
  for (const match of message.matchAll(boldParts)) {
    const valueStart = match.index + match[1].length + match[2].length;
    item.append(message.slice(cursor, valueStart));
    const emphasized = document.createElement('strong');
    emphasized.textContent = match[3];
    item.append(emphasized);
    cursor = valueStart + match[3].length;
  }
  item.append(message.slice(cursor));
}

function showErrors(container, summary, errors) {
  container.replaceChildren();
  const heading = document.createElement('span');
  heading.textContent = summary;
  container.append(heading);
  if (errors?.length) {
    const list = document.createElement('ul');
    errors.forEach((error) => {
      const item = document.createElement('li');
      appendValidationMessage(item, sourceValidationMessage(error));
      list.append(item);
    });
    container.append(list);
  }
  container.classList.add('error');
}

document.querySelectorAll('[data-download-form]').forEach((form) => {
  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const button = form.querySelector('button[type="submit"]');
    const message = form.querySelector('.form-message');
    button.disabled = true; button.classList.add('loading'); message.textContent = 'Zpracovávání…'; message.className = 'form-message';
    try {
      const response = await fetch(form.action, { method: 'POST', body: new FormData(form) });
      if (!response.ok) {
        const body = await response.json().catch(() => ({}));
        const error = new Error(body.error || `Požadavek se nezdařil (${response.status})`);
        error.details = body.errors;
        throw error;
      }
      downloadBlob(await response.blob(), response.headers.get('Content-Disposition'));
      message.textContent = 'Hotovo – soubor je připraven ke stažení.'; message.classList.add('success');
    } catch (error) {
      showErrors(message, error.message, error.details);
    } finally {
      button.disabled = false; button.classList.remove('loading');
    }
  });
});

const initial = location.hash.slice(1);
if (panels.some((panel) => panel.id === initial)) activateTab(initial, false);
