(() => {
  const input = document.getElementById('q');
  const btn = document.getElementById('btn');
  const msg = document.getElementById('msg');
  const table = document.getElementById('table');
  const tbody = document.getElementById('tbody');

  function escapeHtml(s) {
    return String(s ?? '')
      .replaceAll('&', '&amp;')
      .replaceAll('<', '&lt;')
      .replaceAll('>', '&gt;')
      .replaceAll('"', '&quot;')
      .replaceAll("'", '&#039;');
  }

  function formatPrice(value) {
    if (value === null || value === undefined) return '—';
    const n = Number(value);
    if (!Number.isFinite(n)) return String(value);
    return n.toLocaleString('ru-RU') + ' ₽';
  }

  function setMessage(text) {
    msg.textContent = text || '';
  }

  function clearTable() {
    tbody.innerHTML = '';
    table.hidden = true;
  }

  function renderRows(items) {
    clearTable();
    const rows = items.map((it) => {
      const shop = escapeHtml(it.shop);
      const title = escapeHtml(it.title);
      const price = formatPrice(it.price);
      const url = String(it.url ?? '').trim();

      const link = url
        ? `<a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer">Открыть</a>`
        : '—';

      return `
        <tr>
          <td>${shop || '—'}</td>
          <td>${title || '—'}</td>
          <td>${escapeHtml(price)}</td>
          <td>${link}</td>
        </tr>
      `;
    }).join('');

    tbody.innerHTML = rows;
    table.hidden = items.length === 0;
  }

  async function doSearch() {
    const q = (input.value || '').trim();
    if (q.length < 2) {
      clearTable();
      setMessage('Введите минимум 2 символа для поиска.');
      return;
    }

    clearTable();
    setMessage('Ищем…');
    btn.disabled = true;
    input.disabled = true;

    try {
      const resp = await fetch(`/search?q=${encodeURIComponent(q)}`, {
        headers: { 'Accept': 'application/json' },
      });

      if (!resp.ok) {
        throw new Error(`HTTP ${resp.status}`);
      }

      const data = await resp.json();

      if (!Array.isArray(data)) {
        setMessage('Неожиданный формат ответа.');
        return;
      }

      if (data.length && typeof data[0] === 'object' && data[0] && data[0].type) {
        clearTable();
        setMessage(data[0].message || 'Нет данных.');
        return;
      }

      data.sort((a, b) => {
        const pa = Number(a?.price);
        const pb = Number(b?.price);
        if (!Number.isFinite(pa) && !Number.isFinite(pb)) return 0;
        if (!Number.isFinite(pa)) return 1;
        if (!Number.isFinite(pb)) return -1;
        return pa - pb;
      });

      renderRows(data);
      setMessage(data.length ? `Найдено: ${data.length}` : 'Ничего не найдено');
    } catch (e) {
      clearTable();
      setMessage(`Ошибка запроса: ${e?.message || e}`);
    } finally {
      btn.disabled = false;
      input.disabled = false;
      input.focus();
    }
  }

  btn.addEventListener('click', doSearch);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') doSearch();
  });

  input.focus();
})();
