/* Assumptions: crawl progress is represented as completed fraction and queued count. */
/* Boundaries: render-only component with placeholder progress allowed. */
/* Integration notes: bind to the crawl progress API when Warp crawl output is available. */
export function renderCrawlProgressPanel(data) {
  const progress = data.crawlProgress || { stage: 'placeholder', completed: 0, queued: 0 };
  const width = Math.round((progress.completed || 0) * 100);
  return `
    <h2>Crawl Progress</h2>
    <div class="badge badge--warn">${progress.stage}</div>
    <p>Queued items: <strong>${progress.queued}</strong></p>
    <div style="background: rgba(255,255,255,0.06); border-radius: 999px; overflow: hidden; height: 10px;">
      <div style="width: ${width}%; height: 10px; background: linear-gradient(90deg, var(--accent), var(--accent-2));"></div>
    </div>
  `;
}
