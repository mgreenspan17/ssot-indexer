/* Assumptions: file browser entries are path/status pairs. */
/* Boundaries: this module only formats display rows. */
/* Integration notes: live file browser data should come from a placeholder API first. */
export function renderFileBrowserPanel(data) {
  const items = (data.files || []).map((item) => `<li class="item"><span>${item.path}</span><strong>${item.status}</strong></li>`).join('');
  return `<h2>File Browser</h2><ul class="list">${items}</ul>`;
}
