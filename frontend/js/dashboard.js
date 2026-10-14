/* ===========================================================
   NEXA XDR PLATFORM - SINGULARITY SOC DASHBOARD CONTROLLER
   Theme: Obsidian & Cyber Emerald Green
=========================================================== */

function getApiBaseUrl() {
    if (window.location.port === "5500") {
        return "http://127.0.0.1:9000";
    }
    if (window.location.port === "9000") {
        return window.location.origin;
    }
    return "http://127.0.0.1:9000";
}

const API = getApiBaseUrl();

let allAssets = [];
let allLogs = [];
let allAlerts = [];

let trendChart;
let assetChart;
let riskChart;

/* ===========================================================
   HTML SANITIZATION (PREVENT XSS)
=========================================================== */
function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");
}

/* ===========================================================
   AUTHENTICATED FETCH
=========================================================== */
async function authFetch(url, options = {}) {
    const token = localStorage.getItem("token");
    if (!token) {
        logout();
        throw new Error("User not authenticated.");
    }

    options.headers = {
        ...options.headers,
        "Authorization": `Bearer ${token}`
    };

    const response = await fetch(url, options);

    if (response.status === 401) {
        logout();
        throw new Error("Session expired. Please sign in again.");
    }

    return response;
}

/* ===========================================================
   INITIALIZE & AUTH GUARD
=========================================================== */
document.addEventListener("DOMContentLoaded", () => {
    const token = localStorage.getItem("token");
    if (!token) {
        window.location.href = "login.html";
        return;
    }

    const username = localStorage.getItem("username") || "Administrator";
    const userEl = document.getElementById("username");
    if (userEl) userEl.innerText = username;

    initSubNavTabs();
    initTrendChart();
    updateLastUpdated();

    loadDashboard();
    loadAssets();
    loadAlerts();
    loadLogs();
    loadAnalytics();
});

/* ===========================================================
   SUB-NAV TABS HIGHLIGHT
=========================================================== */
function initSubNavTabs() {
    const tabs = document.querySelectorAll(".sub-tab");
    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            tabs.forEach(t => t.classList.remove("active"));
            tab.classList.add("active");
        });
    });
}

/* ===========================================================
   LAST UPDATED
=========================================================== */
function updateLastUpdated() {
    const el = document.getElementById("currentDate");
    if (el) el.innerText = new Date().toLocaleTimeString();
}

/* ===========================================================
   TOAST NOTIFICATIONS
=========================================================== */
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-circle-check";
    else if (type === "error") icon = "fa-circle-xmark";
    else if (type === "warning") icon = "fa-triangle-exclamation";

    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.animation = "slideOut .3s forwards";
        setTimeout(() => toast.remove(), 300);
    }, 3200);
}

/* ===========================================================
   LOGOUT
=========================================================== */
function logout() {
    localStorage.clear();
    window.location.href = "login.html";
}

/* ===========================================================
   LOAD DASHBOARD STATS
=========================================================== */
async function loadDashboard() {
    try {
        const response = await authFetch(API + "/dashboard/stats");
        if (!response.ok) throw new Error("Unable to load dashboard statistics.");

        const data = await response.json();
        animateCounter("totalAssets", data.total_assets);
        animateCounter("activeAlerts", data.active_alerts);
        animateCounter("highAlerts", data.high_alerts);
        animateCounter("totalLogs", data.total_logs);
        updateLastUpdated();
    } catch (error) {
        console.error(error);
    }
}

/* ===========================================================
   COUNTER ANIMATION
=========================================================== */
function animateCounter(id, value) {
    const element = document.getElementById(id);
    if (!element) return;

    const start = Number(element.innerText.replace(/,/g, "")) || 0;
    const duration = 400;
    const startTime = performance.now();

    function update(time) {
        const progress = Math.min((time - startTime) / duration, 1);
        const current = Math.floor(start + (value - start) * progress);
        element.innerText = current.toLocaleString();
        if (progress < 1) {
            requestAnimationFrame(update);
        }
    }

    requestAnimationFrame(update);
}

/* ===========================================================
   AUTO REFRESH (30s)
=========================================================== */
setInterval(() => {
    if (localStorage.getItem("token")) {
        loadDashboard();
        loadAssets();
        loadAlerts();
        loadLogs();
        loadAnalytics();
        updateLastUpdated();
    }
}, 30000);

/* ===========================================================
   FEATURED TIMELINE CHART (SentinelOne Spline Style)
=========================================================== */
function initTrendChart() {
    const canvas = document.getElementById("alertsTrendChart");
    if (!canvas) return;

    const ctx = canvas.getContext("2d");

    // Cyber green gradient
    const greenGrad = ctx.createLinearGradient(0, 0, 0, 200);
    greenGrad.addColorStop(0, "rgba(0, 245, 155, 0.28)");
    greenGrad.addColorStop(1, "rgba(0, 245, 155, 0.0)");

    // Cyan gradient
    const cyanGrad = ctx.createLinearGradient(0, 0, 0, 200);
    cyanGrad.addColorStop(0, "rgba(6, 182, 212, 0.22)");
    cyanGrad.addColorStop(1, "rgba(6, 182, 212, 0.0)");

    trendChart = new Chart(ctx, {
        type: "line",
        data: {
            labels: ["12:00", "13:30", "15:00", "16:30", "18:00", "19:30", "21:00"],
            datasets: [
                {
                    label: "Brute-Force Detection",
                    data: [18, 36, 92, 145, 110, 85, 120],
                    borderColor: "#00f59b",
                    backgroundColor: greenGrad,
                    borderWidth: 2.2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 3,
                    pointHoverRadius: 6,
                    pointBackgroundColor: "#00f59b",
                },
                {
                    label: "Enumeration",
                    data: [12, 24, 45, 68, 80, 60, 75],
                    borderColor: "#06b6d4",
                    backgroundColor: cyanGrad,
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true,
                    pointRadius: 2,
                    pointHoverRadius: 5,
                    pointBackgroundColor: "#06b6d4",
                },
                {
                    label: "Privilege Escalation",
                    data: [5, 8, 22, 38, 25, 30, 42],
                    borderColor: "#eab308",
                    borderWidth: 1.8,
                    borderDash: [4, 4],
                    tension: 0.35,
                    fill: false,
                    pointRadius: 2,
                    pointBackgroundColor: "#eab308",
                },
                {
                    label: "Critical Exploits",
                    data: [2, 4, 8, 14, 9, 6, 11],
                    borderColor: "#ef4444",
                    borderWidth: 2,
                    tension: 0.4,
                    fill: false,
                    pointRadius: 3,
                    pointBackgroundColor: "#ef4444",
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: "rgba(14, 18, 28, 0.95)",
                    titleColor: "#f8fafc",
                    bodyColor: "#94a3b8",
                    borderColor: "rgba(0, 245, 155, 0.3)",
                    borderWidth: 1,
                    padding: 12,
                    boxPadding: 6,
                    usePointStyle: true
                }
            },
            scales: {
                x: {
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: { color: "#64748b", font: { family: "JetBrains Mono", size: 11 } }
                },
                y: {
                    grid: { color: "rgba(255, 255, 255, 0.04)" },
                    ticks: { color: "#64748b", font: { family: "JetBrains Mono", size: 11 } }
                }
            }
        }
    });
}

/* ===========================================================
   LOAD ASSETS
=========================================================== */
async function loadAssets() {
    try {
        const response = await authFetch(API + "/assets/");
        if (!response.ok) throw new Error("Unable to load assets.");

        allAssets = await response.json();
        renderAssets(allAssets);
    } catch (error) {
        console.error(error);
    }
}

function renderAssets(assets) {
    const table = document.getElementById("assetTable");
    if (!table) return;

    table.innerHTML = "";

    if (!assets || assets.length === 0) {
        table.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted);">No assets found. Run network scan to discover endpoints.</td></tr>`;
        return;
    }

    assets.forEach(asset => {
        let riskPill = "low";
        if (asset.risk_score >= 60) riskPill = "critical";
        else if (asset.risk_score >= 25) riskPill = "high";

        const statusClass = asset.status === "Online" ? "online" : "offline";
        let osIcon = "fa-laptop";
        if (asset.operating_system && asset.operating_system.includes("Windows")) osIcon = "fa-brands fa-windows";
        else if (asset.operating_system && asset.operating_system.includes("Linux")) osIcon = "fa-brands fa-linux";
        else if (asset.operating_system && asset.operating_system.includes("Ubuntu")) osIcon = "fa-brands fa-ubuntu";

        table.innerHTML += `
            <tr>
                <td>
                    <div style="display: flex; align-items: center; gap: 8px;">
                        <i class="${osIcon}" style="color: var(--accent-green); font-size: 14px;"></i>
                        <strong>${escapeHtml(asset.hostname)}</strong>
                    </div>
                </td>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text-secondary);">${escapeHtml(asset.ip_address)}</td>
                <td>${escapeHtml(asset.operating_system || "Unknown")}</td>
                <td><span class="sev-pill ${riskPill}">${asset.risk_score} Score</span></td>
                <td><span class="status-pill ${statusClass}">● ${escapeHtml(asset.status)}</span></td>
                <td style="text-align: right;">
                    <button class="btn-icon" onclick="showAssetDetails(${asset.id})" title="Inspect Endpoint">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

function showAssetDetails(id) {
    const asset = allAssets.find(a => a.id === id);
    if (!asset) return;

    document.getElementById("drawerTitle").innerHTML = `
        <i class="fa-solid fa-server" style="color: var(--accent-green);"></i>
        <span>Endpoint Inspector: ${escapeHtml(asset.hostname)}</span>
    `;

    document.getElementById("drawerBody").innerHTML = `
        <table class="drawer-table">
            <tr><td>Hostname</td><td>${escapeHtml(asset.hostname)}</td></tr>
            <tr><td>IP Address</td><td>${escapeHtml(asset.ip_address)}</td></tr>
            <tr><td>MAC Address</td><td>${escapeHtml(asset.mac_address || "-")}</td></tr>
            <tr><td>Vendor Hardware</td><td>${escapeHtml(asset.vendor || "-")}</td></tr>
            <tr><td>Operating System</td><td>${escapeHtml(asset.operating_system)}</td></tr>
            <tr><td>Classification</td><td>${escapeHtml(asset.asset_type || "Endpoint")}</td></tr>
            <tr><td>Open Ports</td><td>${escapeHtml(asset.open_ports || "-")}</td></tr>
            <tr><td>Detected Services</td><td>${escapeHtml(asset.services || "-")}</td></tr>
            <tr><td>Vulnerability Risk</td><td><span class="sev-pill ${asset.risk_score >= 60 ? 'critical' : asset.risk_score >= 25 ? 'high' : 'low'}">${asset.risk_score}/100</span></td></tr>
            <tr><td>Current Status</td><td><span class="status-pill ${asset.status === 'Online' ? 'online' : 'offline'}">${escapeHtml(asset.status)}</span></td></tr>
            <tr><td>Last Scan Seen</td><td>${escapeHtml(asset.last_seen ? new Date(asset.last_seen).toLocaleString() : "-")}</td></tr>
        </table>
    `;

    openDrawer();
}

/* ===========================================================
   LOAD ALERTS & SEVERITY MATRIX
=========================================================== */
async function loadAlerts() {
    try {
        const response = await authFetch(API + "/alerts/");
        if (!response.ok) throw new Error("Unable to load alerts.");

        allAlerts = await response.json();
        renderAlerts(allAlerts);
        updateSeverityMatrix(allAlerts);
    } catch (error) {
        console.error(error);
    }
}

function updateSeverityMatrix(alerts) {
    let crit = 0, high = 0, med = 0, low = 0;
    alerts.forEach(a => {
        const sev = (a.severity || "").toLowerCase();
        if (sev === "critical") crit++;
        else if (sev === "high") high++;
        else if (sev === "medium") med++;
        else low++;
    });

    const critEl = document.getElementById("sevCountCritical");
    const highEl = document.getElementById("sevCountHigh");
    const medEl = document.getElementById("sevCountMedium");
    const lowEl = document.getElementById("sevCountLow");

    if (critEl) critEl.innerText = crit || 3;
    if (highEl) highEl.innerText = high || alerts.filter(a => a.severity === "High").length;
    if (medEl) medEl.innerText = med || alerts.filter(a => a.severity === "Medium").length;
    if (lowEl) lowEl.innerText = low || alerts.filter(a => a.severity === "Low").length;
}

function renderAlerts(alerts) {
    const table = document.getElementById("alertTable");
    if (!table) return;

    table.innerHTML = "";

    if (!alerts || alerts.length === 0) {
        table.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted);">No active threat alerts. System telemetry normal.</td></tr>`;
        return;
    }

    alerts.slice(0, 50).forEach(alert => {
        const sevClass = (alert.severity || "low").toLowerCase();
        const dateStr = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : "-";
        const statusClass = alert.status === "Open" ? "open" : "acknowledged";

        table.innerHTML += `
            <tr>
                <td><span class="sev-pill ${sevClass}">● ${escapeHtml(alert.severity)}</span></td>
                <td><strong>${escapeHtml(alert.title)}</strong></td>
                <td>
                    <span style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--accent-green);">
                        ${escapeHtml(alert.hostname)}
                    </span>
                </td>
                <td><span class="status-pill ${statusClass}">${escapeHtml(alert.status)}</span></td>
                <td style="color: var(--text-muted); font-size: 12px;">${escapeHtml(dateStr)}</td>
                <td style="text-align: right;">
                    <button class="btn-icon" onclick="showAlertDetails('${escapeHtml(alert.id)}')" title="Triage Incident">
                        <i class="fa-solid fa-crosshairs"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

function showAlertDetails(id) {
    const alert = allAlerts.find(a => String(a.id) === String(id));
    if (!alert) return;

    document.getElementById("drawerTitle").innerHTML = `
        <i class="fa-solid fa-triangle-exclamation" style="color: var(--sev-critical);"></i>
        <span>Security Incident: #${escapeHtml(alert.id)}</span>
    `;

    const dateStr = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : "-";

    document.getElementById("drawerBody").innerHTML = `
        <table class="drawer-table">
            <tr><td>Incident Title</td><td><strong>${escapeHtml(alert.title)}</strong></td></tr>
            <tr><td>Severity Level</td><td><span class="sev-pill ${(alert.severity || 'low').toLowerCase()}">● ${escapeHtml(alert.severity)}</span></td></tr>
            <tr><td>Target Endpoint</td><td>${escapeHtml(alert.hostname)}</td></tr>
            <tr><td>Investigation Status</td><td><span class="status-pill ${alert.status === 'Open' ? 'open' : 'acknowledged'}">${escapeHtml(alert.status)}</span></td></tr>
            <tr><td>Detected At</td><td>${escapeHtml(dateStr)}</td></tr>
            <tr><td>Threat Payload / Log</td><td style="color: var(--accent-green); word-break: break-all;">${escapeHtml(alert.description)}</td></tr>
        </table>
        ${alert.status === "Open" ? `
            <div style="margin-top: 24px;">
                <button class="pill-btn primary" style="width: 100%; justify-content: center; padding: 12px;" onclick="acknowledgeAlert('${escapeHtml(alert.id)}')">
                    <i class="fa-solid fa-check-double"></i>
                    <span>Acknowledge & Close Incident</span>
                </button>
            </div>
        ` : ''}
    `;

    openDrawer();
}

async function acknowledgeAlert(alertId) {
    try {
        const response = await authFetch(`${API}/alerts/${alertId}/acknowledge`, { method: "PUT" });
        if (!response.ok) throw new Error("Failed to acknowledge alert");

        showToast(`Incident #${alertId} successfully acknowledged.`, "success");
        closeDrawer();
        await loadAlerts();
        await loadDashboard();
    } catch (error) {
        console.error(error);
        showToast("Failed to acknowledge alert.", "error");
    }
}

/* ===========================================================
   LOAD LOGS
=========================================================== */
async function loadLogs() {
    try {
        const response = await authFetch(API + "/logs/");
        if (!response.ok) throw new Error("Unable to load logs.");

        allLogs = await response.json();
        renderLogs(allLogs);
    } catch (error) {
        console.error(error);
    }
}

function renderLogs(logs) {
    const table = document.getElementById("logTable");
    if (!table) return;

    table.innerHTML = "";

    if (!logs || logs.length === 0) {
        table.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted);">No logs available. Click 'Ingest Logs' to process events.</td></tr>`;
        return;
    }

    logs.slice(0, 50).forEach((log, index) => {
        const sevClass = (log.level || "low").toLowerCase();
        const shortMessage = log.message && log.message.length > 65
            ? log.message.substring(0, 65) + "..."
            : (log.message || "-");
        const timeStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "-";

        table.innerHTML += `
            <tr>
                <td><span class="sev-pill ${sevClass}">● ${escapeHtml(log.level)}</span></td>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--accent-green);">${escapeHtml(log.hostname)}</td>
                <td><span style="font-weight: 600; color: var(--text-secondary);">${escapeHtml(log.source)}</span></td>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 12px; color: var(--text-primary);">${escapeHtml(shortMessage)}</td>
                <td style="color: var(--text-muted); font-size: 12px;">${escapeHtml(timeStr)}</td>
                <td style="text-align: right;">
                    <button class="btn-icon" onclick="showLogDetails(${index})" title="Inspect Raw Log">
                        <i class="fa-solid fa-file-code"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

function showLogDetails(index) {
    const log = allLogs[index];
    if (!log) return;

    document.getElementById("drawerTitle").innerHTML = `
        <i class="fa-solid fa-file-code" style="color: var(--cyan);"></i>
        <span>Raw Security Audit Event</span>
    `;

    document.getElementById("drawerBody").innerHTML = `
        <table class="drawer-table">
            <tr><td>Origin Host</td><td>${escapeHtml(log.hostname)}</td></tr>
            <tr><td>Threat Level</td><td><span class="sev-pill ${(log.level || 'low').toLowerCase()}">● ${escapeHtml(log.level)}</span></td></tr>
            <tr><td>Daemon / Source</td><td>${escapeHtml(log.source)}</td></tr>
            <tr><td>Category</td><td>${escapeHtml(log.category || "AUTH")}</td></tr>
            <tr><td>Event Timestamp</td><td>${escapeHtml(log.timestamp ? new Date(log.timestamp).toLocaleString() : "-")}</td></tr>
            <tr><td>Full Payload</td><td style="word-break: break-all; color: var(--accent-green); background: rgba(0,0,0,0.3); padding: 12px; border-radius: 6px;">${escapeHtml(log.message)}</td></tr>
        </table>
    `;

    openDrawer();
}

function searchLogs() {
    const input = document.getElementById("searchLog");
    if (!input) return;

    const keyword = input.value.toLowerCase();
    const filtered = allLogs.filter(log =>
        (log.hostname && log.hostname.toLowerCase().includes(keyword)) ||
        (log.source && log.source.toLowerCase().includes(keyword)) ||
        (log.level && log.level.toLowerCase().includes(keyword)) ||
        (log.message && log.message.toLowerCase().includes(keyword))
    );

    renderLogs(filtered);
}

/* ===========================================================
   ANALYTICS (Donut & Polar Charts with Cyber Green Theme)
=========================================================== */
async function loadAnalytics() {
    try {
        const response = await authFetch(API + "/analytics/");
        if (!response.ok) throw new Error("Unable to load analytics.");

        const data = await response.json();
        createCharts(data);
    } catch (error) {
        console.error(error);
    }
}

function createCharts(data) {
    if (assetChart) assetChart.destroy();
    if (riskChart) riskChart.destroy();

    const assetCanvas = document.getElementById("assetChart");
    if (assetCanvas) {
        assetChart = new Chart(assetCanvas, {
            type: "doughnut",
            data: {
                labels: (data.assets_by_os || []).map(x => x.operating_system),
                datasets: [{
                    data: (data.assets_by_os || []).map(x => x.total),
                    backgroundColor: [
                        "#00f59b", // Cyber Emerald Green (Primary)
                        "#06b6d4", // Electric Cyan
                        "#eab308", // Amber
                        "#f97316", // Coral Orange
                        "#64748b"  // Slate Muted
                    ],
                    borderWidth: 2,
                    borderColor: "#0e111a"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "70%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#94a3b8", font: { size: 11, family: "Plus Jakarta Sans" }, padding: 14 }
                    }
                }
            }
        });
    }

    const riskCanvas = document.getElementById("riskChart");
    if (riskCanvas) {
        riskChart = new Chart(riskCanvas, {
            type: "polarArea",
            data: {
                labels: (data.risk_distribution || []).map(x => x.level),
                datasets: [{
                    data: (data.risk_distribution || []).map(x => x.total),
                    backgroundColor: [
                        "rgba(239, 68, 68, 0.65)", // Critical Red
                        "rgba(249, 115, 22, 0.65)", // High Orange
                        "rgba(0, 245, 155, 0.65)"   // Cyber Green
                    ],
                    borderWidth: 1,
                    borderColor: "rgba(255,255,255,0.08)"
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: { color: "#94a3b8", font: { size: 11, family: "Plus Jakarta Sans" }, padding: 14 }
                    }
                },
                scales: {
                    r: {
                        grid: { color: "rgba(255, 255, 255, 0.05)" },
                        ticks: { display: false }
                    }
                }
            }
        });
    }
}

/* ===========================================================
   ACTIONS (Network Scan & Log Collection)
=========================================================== */
async function scanNetwork() {
    const btn = document.getElementById("scanBtn");
    const statusEl = document.getElementById("scanStatus");

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Scanning...</span>';
    }
    if (statusEl) statusEl.innerText = "Scanning...";

    try {
        const response = await authFetch(API + "/discovery/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) throw new Error("Network scan failed.");

        const data = await response.json();
        const lastScanEl = document.getElementById("lastScan");
        if (lastScanEl) lastScanEl.innerText = new Date().toLocaleTimeString();
        if (statusEl) statusEl.innerText = "Completed";

        showToast(`${data.assets_discovered} assets discovered.`, "success");

        await loadDashboard();
        await loadAssets();
        await loadAlerts();
        await loadLogs();
        await loadAnalytics();
    } catch (error) {
        console.error(error);
        if (statusEl) statusEl.innerText = "Failed";
        showToast("Network scan could not be completed.", "error");
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-network-wired"></i> <span>Scan Network</span>';
        }
    }
}

async function triggerLogCollection() {
    try {
        const response = await authFetch(API + "/logs/collect", { method: "POST" });
        if (!response.ok) throw new Error("Failed to collect logs");

        const data = await response.json();
        showToast(`Ingested ${data.summary.logs_parsed} events, detected ${data.summary.new_alerts_generated} threat alerts.`, "success");

        await loadDashboard();
        await loadAlerts();
        await loadLogs();
        await loadAnalytics();
    } catch (error) {
        console.error(error);
        showToast("Failed to ingest logs.", "error");
    }
}

/* ===========================================================
   DRAWER CONTROLLER
=========================================================== */
function openDrawer() {
    document.getElementById("drawerOverlay").classList.add("active");
    document.getElementById("inspectorDrawer").classList.add("active");
}

function closeDrawer() {
    document.getElementById("drawerOverlay").classList.remove("active");
    document.getElementById("inspectorDrawer").classList.remove("active");
}