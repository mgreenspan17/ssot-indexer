/* Assumptions: governance version is a simple string until the registry mirror is live. */
/* Boundaries: render-only component with no policy mutation. */
/* Integration notes: replace the version string with registry metadata later. */
export function renderGovernanceVersionPanel(data) {
  return `
    <h2>Governance Version</h2>
    <div class="badge badge--ok">SSOT governance ${data.governanceVersion}</div>
    <p class="lede">Canonical file and registry mirror are the authoritative policy sources.</p>
  `;
}
