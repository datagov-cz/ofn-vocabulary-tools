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

function downloadBlob(blob, disposition, explicitFilename) {
  const match = disposition?.match(/filename\*?=(?:UTF-8''|["']?)([^"';]+)/i);
  const filename = explicitFilename || (match ? decodeURIComponent(match[1].replace(/["']/g, '')) : 'download');
  const url = URL.createObjectURL(blob);
  const link = Object.assign(document.createElement('a'), { href: url, download: filename });
  document.body.appendChild(link); link.click(); link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 60_000);
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

function showConverterReport(container, body) {
  container.replaceChildren();
  const groups = body.validationResults?.severityGroups || [];
  const validation = body.validationReport?.validation || {};
  const rows = [];
  for (const [concept, entry] of Object.entries(validation)) {
    for (const [rule, finding] of Object.entries(entry?.violations || {})) {
      rows.push([entry.conceptIri || concept, finding.name || rule,
        finding.severity || finding.level || '', finding.description || finding.value || '']);
    }
  }
  const heading = document.createElement('h4');
  heading.textContent = 'Zpráva validátoru slovníku';
  container.append(heading);
  if (!groups.length && !rows.length) {
    const empty = document.createElement('p');
    empty.textContent = 'Validátor nevrátil žádná zjištění.';
    container.append(empty);
    container.hidden = false;
    return;
  }
  const table = document.createElement('table');
  const detailed = rows.length > 0;
  const columns = detailed ? ['Pojem', "Pravidlo", 'Závažnost', 'Popis']
    : ['Závažnost', 'Počet', 'Popis'];
  const head = document.createElement('thead');
  const headingRow = document.createElement('tr');
  columns.forEach((column) => {
    const cell = document.createElement('th'); cell.textContent = column; headingRow.append(cell);
  });
  head.append(headingRow); table.append(head);
  const tbody = document.createElement('tbody');
  (detailed ? rows : groups.map((group) =>
    [group.severity || '', group.count ?? '', group.description || '']))
    .forEach((row) => {
      const tr = document.createElement('tr');
      row.forEach((value) => {
        const cell = document.createElement('td'); cell.textContent = value; tr.append(cell);
      });
      tbody.append(tr);
    });
  table.append(tbody); container.append(table); container.hidden = false;
}

const datasetForm = document.querySelector('[data-dataset-form]');
datasetForm.addEventListener('submit', async (event) => {
  event.preventDefault();
  const button = datasetForm.querySelector('button[type="submit"]');
  const message = datasetForm.querySelector('.form-message');
  const report = datasetForm.querySelector('.validation-report');
  const downloads = datasetForm.querySelector('.dataset-downloads');
  downloads.replaceChildren(); downloads.hidden = true;
  const steps = [...datasetForm.querySelectorAll('[data-step]')];
  const setStep = (index, state) => { steps[index].dataset.state = state; };
  steps.forEach((step) => { delete step.dataset.state; });
  report.hidden = true; report.replaceChildren();
  message.textContent = ''; message.className = 'form-message';
  button.disabled = true; button.classList.add('loading');
  let active = 0;
  setStep(active, 'active');
  try {
    const formData = new FormData(datasetForm);
    const prepared = await fetch('/api/dataset/vocabulary', { method: 'POST', body: formData });
    const body = await prepared.json().catch(() => ({}));
    showConverterReport(report, body);
    if (!prepared.ok) throw new Error(body.error || `Konvertor selhal (${prepared.status}).`);
    setStep(active, 'done'); active = 1; setStep(active, 'active');
    const conversionData = new FormData();
    conversionData.set('file', formData.get('file'));
    conversionData.set('vocabulary_file',
      new Blob([body.vocabulary], { type: 'application/ld+json' }), 'vocabulary.jsonld');
    conversionData.set('conversion_token', body.conversionToken);
    const mode = formData.get('download_mode');
    conversionData.set('download_mode', mode);
    const converted = await fetch(datasetForm.action, { method: 'POST', body: conversionData });
    if (!converted.ok) {
      const failure = await converted.json().catch(() => ({}));
      const error = new Error(failure.error || `Převod selhal (${converted.status}).`);
      error.details = failure.errors;
      throw error;
    }
    setStep(active, 'done'); active = 2; setStep(active, 'active');
    if (mode === 'files') {
      const result = await converted.json();
      for (const file of result.files) {
        const link = document.createElement('button');
        link.type = 'button';
        link.className = 'download-file';
        link.textContent = `Stáhnout ${file.name}`;
        link.addEventListener('click', () => {
          const bytes = Uint8Array.from(atob(file.content), (character) => character.charCodeAt(0));
          const type = file.name.endsWith('.xml') ? 'application/xml' : 'application/ld+json';
          downloadBlob(new Blob([bytes], { type }), null, file.name);
        });
        downloads.append(link);
      }
      downloads.hidden = false;
      message.textContent = 'Hotovo – vyberte soubory ke stažení.';
    } else {
      downloadBlob(await converted.blob(), converted.headers.get('Content-Disposition'));
      message.textContent = 'Hotovo – ZIP obsahuje metadata, model s IRI a slovník OFN.';
    }
    setStep(active, 'done');
    message.classList.add('success');
  } catch (error) {
    setStep(active, 'error');
    showErrors(message, error.message, error.details);
  } finally {
    button.disabled = false; button.classList.remove('loading');
  }
});

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
