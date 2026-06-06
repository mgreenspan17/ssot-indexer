/* Assumptions: system health items are small name/status records. */
/* Boundaries: render-only component with placeholder healthy state allowed. */
/* Integration notes: bind to diagnostics_loop.py and dashboard_api.py later. */
export function renderSystemHealthPanel(data) {
  const items = (data.health || []).map((item) => `<li class="item"><span>${item.name}</span><strong>${item.status}</strong></li>`).join('');
  return `<h2>System Health</h2><ul class="list">${items}</ul>`;
}