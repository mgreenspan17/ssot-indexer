/* Assumptions: DOM nodes exist for all panels and placeholder data is acceptable. */
/* Boundaries: this file renders only; it does not fetch or mutate live systems. */
/* Integration notes: future data sources should come from dashboard_api.py. */
import { renderAgentStatusPanel } from './components/agent_status_panel.js';
import { renderCrawlProgressPanel } from './components/crawl_progress_panel.js';
import { renderFileBrowserPanel } from './components/file_browser_panel.js';
import { renderGovernanceVersionPanel } from './components/governance_version_panel.js';
import { renderSystemHealthPanel } from './components/system_health_panel.js';

const placeholderData = {
  governanceVersion: '1.0.0',
  agentStatus: [
    { name: 'Warp', status: 'ready', detail: 'Execution lane available' },
    { name: 'Cody', status: 'ready', detail: 'Artifact generation lane available' },
    { name: 'Copilot', status: 'ready', detail: 'Coordination lane available' },
  ],
  crawlProgress: { stage: 'placeholder', completed: 0.34, queued: 12 },
  files: [
    { path: '/srv/data/ssot-ingestion/sample.json', status: 'placeholder' },
    { path: '/srv/data/ssot-graph/graph.json', status: 'placeholder' },
  ],
  health: [
    { name: 'Governance', status: 'ok' },
    { name: 'Registry', status: 'ok' },
    { name: 'Filesystem', status: 'ok' },
  ],
};

document.getElementById('governance-version-panel').innerHTML = renderGovernanceVersionPanel(placeholderData);
document.getElementById('agent-status-panel').innerHTML = renderAgentStatusPanel(placeholderData);
document.getElementById('crawl-progress-panel').innerHTML = renderCrawlProgressPanel(placeholderData);
document.getElementById('file-browser-panel').innerHTML = renderFileBrowserPanel(placeholderData);
document.getElementById('system-health-panel').innerHTML = renderSystemHealthPanel(placeholderData);
