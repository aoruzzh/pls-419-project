export const messages = JSON.parse(document.getElementById('site-messages').textContent);

export function text(key, values = {}) {
  return messages[key].replace(/\{(\w+)\}/g, (_, name) => values[name] ?? '');
}
