/* ═══════════════════════════════════════════════════
   SSOT OS — File Indexer Dashboard
   Self-contained vanilla JS — no frameworks, no imports
   ═══════════════════════════════════════════════════ */

(function () {
  "use strict";

  // ── Config ──────────────────────────────────────
  const API_URL = "/api/scan/state";
  const POLL_MS = 2000;
  const ANIM_DURATION = 800; // ms for counter animations

  // ── DOM refs ────────────────────────────────────
  const $ = (id) => document.getElementById(id);

  const dom = {
    statusBadge:    $("statusBadge"),
    statusDot:      $("statusDot"),
    statusText:     $("statusText"),
    clock:          $("clock"),

    filesIndexed:   $("filesIndexed"),
    filesTotal:     $("filesTotal"),
    bytesHashed:    $("bytesHashed"),
    bytesUnit:      $("bytesUnit"),
    filesPerSecond: $("filesPerSecond"),
    errorsCount:    $("errorsCount"),
    errorsCard:     $("errorsCard"),
    errorsModal:    $("errorsModal"),
    closeErrorsModal: $("closeErrorsModal"),
    errorsListView: $("errorsListView"),

    progressBar:    $("progressBar"),
    progressPercent:$("progressPercent"),
    elapsedTime:    $("elapsedTime"),
    etaTime:        $("etaTime"),
    currentRoot:    $("currentRoot"),
    rootProgress:   $("rootProgress"),

    feedList:       $("feedList"),
    feedWrapper:    $("feedWrapper"),
    feedDot:        $("feedDot"),

    currentFilePath:$("currentFilePath"),
    activitySpinner:$("activitySpinner"),
    rootsList:      $("rootsList"),
    avgSpeed:       $("avgSpeed"),
    peakSpeed:      $("peakSpeed"),

    sparklineCanvas:$("sparklineCanvas"),

    completionOverlay: $("completionOverlay"),
    completionSummary: $("completionSummary"),
  };

  // ── State ───────────────────────────────────────
  let prevState = null;
  let feedPaused = false;
  let knownFiles = new Set();
  let speedHistory = [];
  const MAX_SPEED_HISTORY = 30;
  let peakSpeedVal = 0;
  let latestErrorLog = [];

  // Animated counter targets
  let counterTargets = {
    filesIndexed: 0,
    filesTotal: 0,
    bytesHashed: 0,
    filesPerSecond: 0,
    errors: 0,
  };

  let counterCurrent = {
    filesIndexed: 0,
    filesTotal: 0,
    bytesHashed: 0,
    filesPerSecond: 0,
    errors: 0,
  };

  // ── Utility Functions ───────────────────────────

  function formatNumber(n) {
    return Math.round(n).toLocaleString("en-US");
  }

  function formatBytes(bytes) {
    if (bytes < 1024) return { value: bytes.toFixed(0), unit: "B" };
    if (bytes < 1024 ** 2) return { value: (bytes / 1024).toFixed(1), unit: "KB" };
    if (bytes < 1024 ** 3) return { value: (bytes / 1024 ** 2).toFixed(1), unit: "MB" };
    if (bytes < 1024 ** 4) return { value: (bytes / 1024 ** 3).toFixed(2), unit: "GB" };
    return { value: (bytes / 1024 ** 4).toFixed(3), unit: "TB" };
  }

  function formatDuration(totalSeconds) {
    if (totalSeconds == null || totalSeconds < 0) return "—";
    const h = Math.floor(totalSeconds / 3600);
    const m = Math.floor((totalSeconds % 3600) / 60);
    const s = Math.floor(totalSeconds % 60);
    return [
      String(h).padStart(2, "0"),
      String(m).padStart(2, "0"),
      String(s).padStart(2, "0"),
    ].join(":");
  }

  function formatETADateTime(etaSeconds) {
    if (etaSeconds == null || etaSeconds <= 0) return "—";
    const targetDate = new Date(Date.now() + etaSeconds * 1000);
    const options = {
      year: "numeric",
      month: "numeric",
      day: "numeric",
      hour: "numeric",
      minute: "2-digit",
      hour12: true
    };
    const absStr = targetDate.toLocaleString(undefined, options);
    
    const d = Math.floor(etaSeconds / 86400);
    const h = Math.floor((etaSeconds % 86400) / 3600);
    const m = Math.floor((etaSeconds % 3600) / 60);
    
    let relStr = "";
    if (d > 0) {
      relStr = `${d}d ${h}h ${m}m remaining`;
    } else if (h > 0) {
      relStr = `${h}h ${m}m remaining`;
    } else {
      relStr = `${m}m remaining`;
    }
    
    return `${absStr} (${relStr})`;
  }

  function extractFilename(filepath) {
    if (!filepath) return "";
    const parts = filepath.replace(/\\/g, "/").split("/");
    return parts[parts.length - 1] || filepath;
  }

  function extractDir(filepath) {
    if (!filepath) return "";
    const normalized = filepath.replace(/\\/g, "/");
    const lastSlash = normalized.lastIndexOf("/");
    return lastSlash > 0 ? normalized.substring(0, lastSlash) : "";
  }

  function truncatePath(path, maxLen) {
    if (!path || path.length <= maxLen) return path || "—";
    return "…" + path.slice(-(maxLen - 1));
  }

  // ── Clock ───────────────────────────────────────
  function updateClock() {
    const now = new Date();
    dom.clock.textContent = now.toLocaleTimeString("en-US", {
      hour12: false,
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  }
  setInterval(updateClock, 1000);
  updateClock();

  // ── Animated Counters ───────────────────────────
  let counterAnimFrame = null;
  let counterStartTime = null;

  function startCounterAnimation() {
    counterStartTime = performance.now();
    if (!counterAnimFrame) {
      counterAnimFrame = requestAnimationFrame(tickCounters);
    }
  }

  function tickCounters(now) {
    const elapsed = now - counterStartTime;
    const progress = Math.min(elapsed / ANIM_DURATION, 1);
    // ease-out cubic
    const ease = 1 - Math.pow(1 - progress, 3);

    for (const key of Object.keys(counterTargets)) {
      const start = counterCurrent[key];
      const target = counterTargets[key];
      const current = start + (target - start) * ease;

      if (key === "filesIndexed") {
        dom.filesIndexed.textContent = formatNumber(current);
      } else if (key === "filesTotal") {
        dom.filesTotal.textContent = formatNumber(current);
      } else if (key === "bytesHashed") {
        const fmt = formatBytes(current);
        dom.bytesHashed.textContent = fmt.value;
        dom.bytesUnit.textContent = fmt.unit;
      } else if (key === "filesPerSecond") {
        dom.filesPerSecond.textContent = current.toFixed(1);
      } else if (key === "errors") {
        dom.errorsCount.textContent = formatNumber(current);
      }
    }

    if (progress < 1) {
      counterAnimFrame = requestAnimationFrame(tickCounters);
    } else {
      // Snap to final values
      for (const key of Object.keys(counterTargets)) {
        counterCurrent[key] = counterTargets[key];
      }
      counterAnimFrame = null;
    }
  }

  function setCounterTarget(key, value) {
    counterCurrent[key] = counterCurrent[key] || 0;
    counterTargets[key] = value;
  }

  // ── Sparkline ───────────────────────────────────
  function drawSparkline() {
    const canvas = dom.sparklineCanvas;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    if (speedHistory.length < 2) return;

    const max = Math.max(...speedHistory, 1);
    const step = w / (MAX_SPEED_HISTORY - 1);

    // Fill gradient
    const grad = ctx.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, "rgba(122, 224, 195, 0.25)");
    grad.addColorStop(1, "rgba(122, 224, 195, 0)");

    ctx.beginPath();
    ctx.moveTo(0, h);

    for (let i = 0; i < speedHistory.length; i++) {
      const x = i * step;
      const y = h - (speedHistory[i] / max) * (h - 4) - 2;
      if (i === 0) ctx.lineTo(x, y);
      else ctx.lineTo(x, y);
    }

    ctx.lineTo((speedHistory.length - 1) * step, h);
    ctx.closePath();
    ctx.fillStyle = grad;
    ctx.fill();

    // Line
    ctx.beginPath();
    for (let i = 0; i < speedHistory.length; i++) {
      const x = i * step;
      const y = h - (speedHistory[i] / max) * (h - 4) - 2;
      if (i === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    }
    ctx.strokeStyle = "#7ae0c3";
    ctx.lineWidth = 1.5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // Dot at end
    const lastX = (speedHistory.length - 1) * step;
    const lastY = h - (speedHistory[speedHistory.length - 1] / max) * (h - 4) - 2;
    ctx.beginPath();
    ctx.arc(lastX, lastY, 3, 0, Math.PI * 2);
    ctx.fillStyle = "#7ae0c3";
    ctx.fill();
  }

  // ── Feed ────────────────────────────────────────
  dom.feedWrapper.addEventListener("mouseenter", () => { feedPaused = true; });
  dom.feedWrapper.addEventListener("mouseleave", () => { feedPaused = false; });

  function updateFeed(recentFiles) {
    if (feedPaused || !recentFiles || recentFiles.length === 0) return;

    // Find new files (maintain order)
    const newFiles = [];
    for (const f of recentFiles) {
      if (!knownFiles.has(f)) {
        newFiles.push(f);
        knownFiles.add(f);
      }
    }

    if (newFiles.length === 0 && dom.feedList.querySelector(".feed-empty")) {
      // First load — populate all
      dom.feedList.innerHTML = "";
      for (let i = recentFiles.length - 1; i >= 0; i--) {
        appendFeedItem(recentFiles[i], recentFiles.length - i, false);
        knownFiles.add(recentFiles[i]);
      }
      return;
    }

    if (newFiles.length === 0) return;

    // Remove empty message
    const empty = dom.feedList.querySelector(".feed-empty");
    if (empty) empty.remove();

    // Prepend new items
    for (const f of newFiles) {
      appendFeedItem(f, dom.feedList.children.length + 1, true);
    }

    // Trim to 40 items max
    while (dom.feedList.children.length > 40) {
      dom.feedList.removeChild(dom.feedList.lastChild);
    }

    // Auto-scroll to top
    if (!feedPaused) {
      dom.feedWrapper.scrollTop = 0;
    }
  }

  function appendFeedItem(filepath, idx, prepend) {
    const li = document.createElement("li");
    li.className = "feed-item";

    const filename = extractFilename(filepath);
    const dir = extractDir(filepath);

    li.innerHTML = `
      <span class="feed-idx">${idx}</span>
      <span class="feed-filename">${escapeHtml(filename)}</span>
      <span class="feed-path" title="${escapeHtml(filepath)}">${escapeHtml(dir)}</span>
    `;

    if (prepend) {
      dom.feedList.insertBefore(li, dom.feedList.firstChild);
    } else {
      dom.feedList.appendChild(li);
    }
  }

  function escapeHtml(str) {
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  }

  // ── Roots ───────────────────────────────────────
  const SOURCE_DETAILS = {
    "/srv/data": { name: "Server RAID Array (/srv/data)", desc: "Local server RAID data roots" },
    "/DATA": { name: "Primary SSD Storage (/DATA)", desc: "System appdata and docker roots" },
    "/home": { name: "User Home Directories (/home)", desc: "Local user home profiles" },
    "onedrive": { name: "OneDrive Cloud Storage", desc: "Microsoft OneDrive cloud folders" },
    "laptop": { name: "Operator Workstation (SSD)", desc: "Primary operator computer local disk" },
    "usb": { name: "Removable USB Drive", desc: "External USB backup drives" },
    "phone": { name: "Cell Phone (MTP)", desc: "Mobile storage connected via USB MTP" }
  };

  function updateRoots(roots, currentRootIndex, state) {
    if (!roots || roots.length === 0) {
      dom.rootsList.innerHTML = '<li class="root-empty">—</li>';
      return;
    }

    dom.rootsList.innerHTML = "";
    
    // 1. Process active scan roots
    roots.forEach((rootPath, idx) => {
      const li = document.createElement("li");
      const mapping = SOURCE_DETAILS[rootPath] || { name: rootPath, desc: "Local path source" };
      
      let statusClass = "pending-source";
      let checkboxHtml = `<input type="checkbox" disabled style="margin-right:8px; accent-color:#7ae0c3; cursor:default;">`;
      let statusLabel = `<span class="source-status status-waiting" style="color:var(--text-dim); font-size:0.68rem; font-weight:700;">WAITING</span>`;
      let dropdownHtml = "";
      
      if (idx < currentRootIndex) {
        statusClass = "completed-source";
        checkboxHtml = `<input type="checkbox" checked disabled style="margin-right:8px; accent-color:#7ae0c3; cursor:default;">`;
        statusLabel = `<span class="source-status status-done" style="color:#7ae0c3; font-size:0.68rem; font-weight:700;">✓ DONE</span>`;
      } else if (idx === currentRootIndex && state && state.status === "scanning") {
        statusClass = "active-source";
        checkboxHtml = `<span class="active-source-dot" style="display:inline-block; width:8px; height:8px; background:#7ae0c3; border-radius:50%; margin-right:8px; animation:pulse 1.8s ease-in-out infinite; box-shadow:0 0 6px #7ae0c3;"></span>`;
        statusLabel = `<span class="source-status status-scanning" style="color:#7ae0c3; font-size:0.68rem; font-weight:700; animation:pulse 1.8s ease-in-out infinite;">ACTIVE</span>`;
        
        // Detailed Dropdown info for currently active root
        const filePct = state.files_total_estimate > 0 
          ? ((state.files_indexed / state.files_total_estimate) * 100).toFixed(1) 
          : "—";
        const bytesFmt = formatBytes(state.bytes_hashed || 0);
        const etaText = formatETADateTime(state.eta_seconds);
        
        dropdownHtml = `
          <div class="source-details-dropdown" style="margin-top: 8px; padding: 10px 14px; background: rgba(122,224,195,0.03); border: 1px solid rgba(122,224,195,0.08); border-radius: 6px; font-size: 0.74rem; color: var(--text-muted); line-height: 1.5; font-family: var(--font-sans);">
            <div style="margin-bottom: 2px;"><strong>Progress:</strong> ${filePct}% (${formatNumber(state.files_indexed)} files)</div>
            <div style="margin-bottom: 2px;"><strong>Hashed:</strong> ${bytesFmt.value} ${bytesFmt.unit}</div>
            <div style="margin-bottom: 2px;"><strong>Current Speed:</strong> ${state.files_per_second || 0} files/s</div>
            <div><strong>Est. Completion:</strong> ${etaText}</div>
          </div>
        `;
      } else if (idx === currentRootIndex && state && state.status === "completed") {
        statusClass = "completed-source";
        checkboxHtml = `<input type="checkbox" checked disabled style="margin-right:8px; accent-color:#7ae0c3; cursor:default;">`;
        statusLabel = `<span class="source-status status-done" style="color:#7ae0c3; font-size:0.68rem; font-weight:700;">✓ DONE</span>`;
      }
      
      li.className = `source-item ${statusClass}`;
      li.style.display = "flex";
      li.style.flexDirection = "column";
      li.style.padding = "10px 14px";
      li.style.background = idx < currentRootIndex ? "rgba(255, 255, 255, 0.01)" : "rgba(255, 255, 255, 0.02)";
      li.style.borderRadius = "var(--radius-sm)";
      li.style.border = idx === currentRootIndex ? "1px solid rgba(122, 224, 195, 0.12)" : "1px solid rgba(255, 255, 255, 0.03)";
      li.style.transition = "all var(--transition)";
      
      if (idx < currentRootIndex) {
        li.style.textDecoration = "line-through";
        li.style.color = "var(--text-dim)";
      }
      
      li.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; width:100%;">
          <div style="display:flex; align-items:center;">
            ${checkboxHtml}
            <span style="font-weight:600; font-size:0.8rem; letter-spacing:0.01em;">${escapeHtml(mapping.name)}</span>
          </div>
          ${statusLabel}
        </div>
        <div style="font-size:0.68rem; color:var(--text-dim); margin-left: 18px; margin-top:2px; text-decoration:none !important; display:inline-block;">${escapeHtml(mapping.desc)}</div>
        ${dropdownHtml}
      `;
      dom.rootsList.appendChild(li);
    });
    
    // 2. Process external/network/cloud sources (future/disconnected)
    const futureSources = ["onedrive", "laptop", "usb", "phone"];
    futureSources.forEach(key => {
      const mapping = SOURCE_DETAILS[key];
      const li = document.createElement("li");
      
      li.className = "source-item future-source";
      li.style.display = "flex";
      li.style.flexDirection = "column";
      li.style.padding = "10px 14px";
      li.style.background = "rgba(255, 255, 255, 0.01)";
      li.style.opacity = "0.45";
      li.style.borderRadius = "var(--radius-sm)";
      li.style.border = "1px solid rgba(255, 255, 255, 0.02)";
      
      let prepDesc = "";
      if (key === "onedrive") prepDesc = "Requires Microsoft OAuth Auth Token (Human-in-the-loop validation).";
      if (key === "laptop") prepDesc = "Requires client-side Daemon / Agent background installation.";
      if (key === "usb") prepDesc = "Triggers automatically via udev when removable partition is mounted.";
      if (key === "phone") prepDesc = "Requires active USB MTP file sharing mode selection.";

      li.innerHTML = `
        <div style="display:flex; align-items:center; justify-content:space-between; width:100%;">
          <div style="display:flex; align-items:center;">
            <input type="checkbox" disabled style="margin-right:8px; opacity:0.3; cursor:default;">
            <span style="font-weight:600; font-size:0.8rem; color:var(--text-dim);">${escapeHtml(mapping.name)}</span>
          </div>
          <span class="source-status status-pending" style="font-size:0.65rem; color:var(--text-dim); font-weight:700; letter-spacing:0.04em;">OFFLINE</span>
        </div>
        <div style="font-size:0.68rem; color:var(--text-dim); margin-left: 18px; margin-top:2px; font-style:italic;">
          Prep: ${prepDesc}
        </div>
      `;
      dom.rootsList.appendChild(li);
    });
  }

  // ── Status Badge ────────────────────────────────
  function updateStatus(status) {
    const s = (status || "idle").toLowerCase();
    dom.statusBadge.setAttribute("data-status", s);

    const labels = {
      scanning: "SCANNING",
      completed: "COMPLETED",
      error: "ERROR",
      idle: "IDLE",
    };
    dom.statusText.textContent = labels[s] || s.toUpperCase();

    // Spinner
    if (s === "scanning") {
      dom.activitySpinner.classList.remove("stopped");
      dom.feedDot.style.display = "";
    } else {
      dom.activitySpinner.classList.add("stopped");
      dom.feedDot.style.display = "none";
    }

    // Progress bar completed state
    if (s === "completed") {
      dom.progressBar.classList.add("completed");
    } else {
      dom.progressBar.classList.remove("completed");
    }
  }

  // ── Completion Overlay ──────────────────────────
  let completionShown = false;

  function showCompletion(state) {
    if (completionShown) return;
    completionShown = true;

    const files = formatNumber(state.files_indexed || 0);
    const byteFmt = formatBytes(state.bytes_hashed || 0);
    const elapsed = formatDuration(state.elapsed_seconds);

    dom.completionSummary.textContent =
      `${files} files · ${byteFmt.value} ${byteFmt.unit} · ${elapsed}`;

    dom.completionOverlay.classList.add("visible");

    // Auto-dismiss after 8s
    setTimeout(() => {
      dom.completionOverlay.classList.remove("visible");
    }, 8000);
  }

  // ── Main Update ─────────────────────────────────
  function applyState(state) {
    latestErrorLog = state.error_log || [];
    // Status
    updateStatus(state.status);

    // Counter targets (animated)
    setCounterTarget("filesIndexed", state.files_indexed || 0);
    setCounterTarget("filesTotal", state.files_total_estimate || 0);
    setCounterTarget("bytesHashed", state.bytes_hashed || 0);
    setCounterTarget("filesPerSecond", state.files_per_second || 0);
    setCounterTarget("errors", state.errors || 0);
    startCounterAnimation();

    // Errors card style
    if ((state.errors || 0) > 0) {
      dom.errorsCard.classList.add("has-errors");
    } else {
      dom.errorsCard.classList.remove("has-errors");
    }

    // Progress bar
    const total = state.files_total_estimate || 1;
    const pct = Math.min(((state.files_indexed || 0) / total) * 100, 100);
    dom.progressBar.style.width = pct.toFixed(2) + "%";
    dom.progressPercent.textContent = pct.toFixed(1) + "%";

    // Timing
    dom.elapsedTime.textContent = formatDuration(state.elapsed_seconds);
    dom.etaTime.textContent = formatETADateTime(state.eta_seconds);

    // Root
    dom.currentRoot.textContent = truncatePath(state.current_root, 50);
    dom.currentRoot.title = state.current_root || "";

    const ri = (state.current_root_index != null ? state.current_root_index + 1 : "—");
    const rt = state.total_roots || "—";
    dom.rootProgress.textContent = `${ri} / ${rt}`;

    // Current file
    dom.currentFilePath.textContent = truncatePath(state.current_file, 60);
    dom.currentFilePath.title = state.current_file || "";

    // Feed
    updateFeed(state.recent_files);

    // Roots list
    updateRoots(state.roots, state.current_root_index, state);

    // Speed history + sparkline
    const speed = state.files_per_second || 0;
    speedHistory.push(speed);
    if (speedHistory.length > MAX_SPEED_HISTORY) speedHistory.shift();
    drawSparkline();

    // Peak / avg speed
    if (speed > peakSpeedVal) peakSpeedVal = speed;
    dom.peakSpeed.textContent = peakSpeedVal.toFixed(1) + " f/s";
    const avgSpd = speedHistory.reduce((a, b) => a + b, 0) / speedHistory.length;
    dom.avgSpeed.textContent = avgSpd.toFixed(1) + " f/s";

    // Completion
    if (state.status === "completed") {
      showCompletion(state);
    } else {
      completionShown = false;
      dom.completionOverlay.classList.remove("visible");
    }

    prevState = state;
  }

  // ── Polling ─────────────────────────────────────
  async function poll() {
    try {
      const res = await fetch(API_URL);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const state = await res.json();
      applyState(state);
    } catch (err) {
      console.warn("[Dashboard] Poll error:", err.message);
      dom.statusText.textContent = "OFFLINE";
      dom.statusBadge.setAttribute("data-status", "error");
    }
  }

  // Start
  poll();
  setInterval(poll, POLL_MS);

  // ── Click overlay to dismiss ────────────────────
  dom.completionOverlay.addEventListener("click", () => {
    dom.completionOverlay.classList.remove("visible");
  });

  // ── Errors Modal Interaction ───────────────────
  function populateErrors() {
    dom.errorsListView.innerHTML = "";
    if (latestErrorLog.length === 0) {
      dom.errorsListView.innerHTML = '<li class="error-empty">No errors recorded so far.</li>';
      return;
    }
    latestErrorLog.forEach(err => {
      const li = document.createElement("li");
      const isLockError = (err.path.toLowerCase().includes("lock") || err.error.toLowerCase().includes("lock")) && 
                          (err.error.includes("No such file") || err.error.includes("Errno 2"));
      const isHealed = err.status === "auto-healed" || err.status === "fixed" || isLockError;
      
      li.className = "error-item-view" + (isHealed ? " auto-healed" : "");
      
      const timestamp = err.timestamp ? new Date(err.timestamp).toLocaleTimeString() : "";
      const prefix = isHealed ? `<span class="error-badge-fixed">✓ FIXED</span> ` : "";
      
      let resolutionHtml = "";
      if (isHealed) {
        const action = err.resolution || (isLockError ? "Action: Detected transient browser lock file. Safely skipped and resolved." : "Action: Automatically resolved transient file/link.");
        resolutionHtml = `<div class="error-resolution-view">${action}</div>`;
      }
      
      li.innerHTML = `
        <span class="error-path-view" title="${err.path}">${err.path}</span>
        <span class="error-message-view">${prefix}${err.error}</span>
        ${resolutionHtml}
        <span class="error-time-view">${timestamp}</span>
      `;
      dom.errorsListView.appendChild(li);
    });
  }

  dom.errorsCard.addEventListener("click", () => {
    populateErrors();
    dom.errorsModal.classList.add("visible");
  });

  dom.closeErrorsModal.addEventListener("click", () => {
    dom.errorsModal.classList.remove("visible");
  });

  dom.errorsModal.addEventListener("click", (e) => {
    if (e.target === dom.errorsModal) {
      dom.errorsModal.classList.remove("visible");
    }
  });

})();
