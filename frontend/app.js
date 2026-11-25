const button = document.getElementById('refresh');
const status = document.getElementById('status');
const list = document.getElementById('items');
async function loadItems() {
  button.disabled = true;
  status.textContent = 'Загрузка…';
  try {
    const response = await fetch('/api/items', {cache: 'no-store'});
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const items = await response.json();
    list.replaceChildren();
    for (const item of items) {
      const row = document.createElement('li');
      row.textContent = `${item.id}. ${item.name}`;
      list.append(row);
    }
    status.textContent = `Получено записей: ${items.length}`;
  } catch (error) {
    status.textContent = `Не удалось загрузить данные: ${error.message}`;
  } finally { button.disabled = false; }
}
button.addEventListener('click', loadItems);
loadItems();
