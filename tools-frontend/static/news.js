(() => {
  const STORAGE_KEY = 'ofn-workbench.news-state';
  const lists = [...document.querySelectorAll('[data-news-list]')];
  if (!lists.length && !document.querySelector('[data-news-count]')) return;

  function loadSeen() {
    try {
      const state = JSON.parse(localStorage.getItem(STORAGE_KEY));
      return new Set(state?.version === 1 && Array.isArray(state.seenIds) ? state.seenIds : []);
    } catch (_) {
      return new Set();
    }
  }

  function saveSeen(seen) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify({ version: 1, seenIds: [...seen] }));
    } catch (_) { /* Reading news still works when storage is unavailable. */ }
  }

  function formatDate(value) {
    const [year, month, day] = value.split('-').map(Number);
    return new Intl.DateTimeFormat('cs-CZ', { dateStyle: 'long' }).format(new Date(year, month - 1, day));
  }

  function makeItem(item, seen, onRead) {
    const article = document.createElement('article');
    article.className = `news-item${seen.has(item.id) ? '' : ' unread'}`;
    article.dataset.newsId = item.id;

    const meta = document.createElement('div');
    meta.className = 'news-meta';
    const time = document.createElement('time');
    time.dateTime = item.publishedAt;
    time.textContent = formatDate(item.publishedAt);
    meta.append(time);
    if (!seen.has(item.id)) {
      const badge = document.createElement('span');
      badge.className = 'new-badge'; badge.textContent = 'Nové';
      meta.append(badge);
    }

    const title = document.createElement('h3'); title.textContent = item.title;
    const summary = document.createElement('p'); summary.textContent = item.summary;
    article.append(meta, title, summary);

    if (item.details.length) {
      const details = document.createElement('ul');
      item.details.forEach((text) => {
        const row = document.createElement('li'); row.textContent = text; details.append(row);
      });
      article.append(details);
    }

    if (!seen.has(item.id)) {
      const button = document.createElement('button');
      button.className = 'text-button'; button.type = 'button'; button.textContent = 'Označit jako přečtené';
      button.addEventListener('click', () => onRead(item.id));
      article.append(button);
    }
    return article;
  }

  fetch('/api/news')
    .then((response) => {
      if (!response.ok) throw new Error('Novinky se nepodařilo načíst.');
      return response.json();
    })
    .then(({ items }) => {
      const validIds = new Set(items.map((item) => item.id));
      const seen = new Set([...loadSeen()].filter((id) => validIds.has(id)));

      function render() {
        const unread = items.filter((item) => !seen.has(item.id));
        document.querySelectorAll('[data-news-count]').forEach((count) => {
          count.textContent = unread.length; count.hidden = unread.length === 0;
        });
        const home = document.querySelector('[data-home-news]');
        if (home) home.hidden = unread.length === 0;

        lists.forEach((list) => {
          const shown = list.hasAttribute('data-show-all') ? items : unread;
          list.replaceChildren();
          if (!shown.length && list.hasAttribute('data-show-all')) {
            const empty = document.createElement('p'); empty.className = 'news-empty'; empty.textContent = 'Zatím nebyly zveřejněny žádné novinky.';
            list.append(empty);
          } else {
            shown.forEach((item) => list.append(makeItem(item, seen, markRead)));
          }
        });
      }

      function markRead(id) { seen.add(id); saveSeen(seen); render(); }
      document.querySelector('[data-mark-all]')?.addEventListener('click', () => {
        items.forEach((item) => seen.add(item.id)); saveSeen(seen); render();
      });
      render();
    })
    .catch((error) => {
      lists.forEach((list) => {
        list.replaceChildren();
        const message = document.createElement('p'); message.className = 'news-error'; message.textContent = error.message; list.append(message);
      });
    });
})();
