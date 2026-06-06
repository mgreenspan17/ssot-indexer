/* Assumptions: agent rows are small structured objects. */
/* Boundaries: render-only component with no side effects. */
/* Integration notes: replace placeholder rows with live agent status records later. */
export function renderAgentStatusPanel(data) {
  const items = (data.agentStatus || []).map((item) => `<li class="item"><span>${item.name}</span><strong>${item.status}</strong></li>`).join('');
  return `<h2>Agent Status</h2><ul class="list">${items}</ul>`;
}
