/* ===========================================================
   NEXA XDR PLATFORM - SHARP CORNER GREENLIFY CONTROLLER
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

let barChartInstance;
let overviewChartInstance;

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

    initCharts();

    loadDashboard();
    loadAssets();
    loadAlerts();
    loadLogs();
});

/* ===========================================================
   CHARTS INITIALIZATION (Matching Reference Image)
=========================================================== */
function initCharts() {
    // 1. Bar Chart (Left)
    const barCanvas = document.getElementById("barChart");
    if (barCanvas) {
        const ctxBar = barCanvas.getContext("2d");
        barChartInstance = new Chart(ctxBar, {
            type: "bar",
            data: {
                labels: ["M", "T", "W", "T", "F", "S", "S", "M", "T"],
                datasets: [{
                    label: "Threat Ingestion",
                    data: [320, 240, 180, 290, 410, 360, 480, 390, 450],
                    backgroundColor: "#01b574",
                    borderRadius: 0,
                    barThickness: 6,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { color: "#718096", font: { size: 10, family: "Plus Jakarta Sans" } }
                    },
                    y: {
                        grid: { color: "rgba(255, 255, 255, 0.04)" },
                        ticks: { color: "#718096", font: { size: 10, family: "JetBrains Mono" } }
                    }
                }
            }
        });
    }

    // 2. Sales / Threat Overview Area Chart (Right, from image: dual green + white curves)
    const overviewCanvas = document.getElementById("overviewChart");
    if (overviewCanvas) {
        const ctxOver = overviewCanvas.getContext("2d");

        const greenGradient = ctxOver.createLinearGradient(0, 0, 0, 240);
        greenGradient.addColorStop(0, "rgba(1, 181, 116, 0.45)");
        greenGradient.addColorStop(1, "rgba(1, 181, 116, 0.0)");

        const whiteGradient = ctxOver.createLinearGradient(0, 0, 0, 240);
        whiteGradient.addColorStop(0, "rgba(255, 255, 255, 0.2)");
        whiteGradient.addColorStop(1, "rgba(255, 255, 255, 0.0)");

        overviewChartInstance = new Chart(ctxOver, {
            type: "line",
            data: {
                labels: ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
                datasets: [
                    {
                        label: "Active Detections",
                        data: [200, 230, 300, 350, 370, 420, 550, 400, 380, 500, 460, 520],
                        borderColor: "#01b574",
                        backgroundColor: greenGradient,
                        borderWidth: 3,
                        fill: true,
                        tension: 0.45,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        pointHoverBackgroundColor: "#01b574",
                    },
                    {
                        label: "Baseline Events",
                        data: [500, 340, 110, 300, 490, 350, 270, 130, 425, 300, 210, 450],
                        borderColor: "#ffffff",
                        backgroundColor: whiteGradient,
                        borderWidth: 2,
                        fill: true,
                        tension: 0.45,
                        pointRadius: 0,
                        pointHoverRadius: 4,
                        pointHoverBackgroundColor: "#ffffff",
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
                        backgroundColor: "#08100d",
                        titleColor: "#ffffff",
                        bodyColor: "#a0aec0",
                        borderColor: "#01b574",
                        borderWidth: 1,
                        padding: 10,
                        cornerRadius: 0,
                        usePointStyle: true
                    }
                },
                scales: {
                    x: {
                        grid: { color: "rgba(255, 255, 255, 0.04)" },
                        ticks: { color: "#718096", font: { size: 11, family: "Plus Jakarta Sans" } }
                    },
                    y: {
                        grid: { color: "rgba(255, 255, 255, 0.04)" },
                        ticks: { color: "#718096", font: { size: 11, family: "JetBrains Mono" } }
                    }
                }
            }
        });
    }
}

/* ===========================================================
   TOAST NOTIFICATIONS (Sharp Rectangles)
=========================================================== */
function showToast(message, type = "info") {
    const container = document.getElementById("toastContainer");
    if (!container) return;

    const toast = document.createElement("div");
    toast.className = `toast ${type}`;

    let icon = "fa-circle-info";
    if (type === "success") icon = "fa-check";
    else if (type === "error") icon = "fa-xmark";

    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.remove();
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
        if (!response.ok) throw new Error("Unable to load stats.");

        const data = await response.json();
        animateCounter("totalAssets", data.total_assets);
        animateCounter("activeAlerts", data.active_alerts);
        animateCounter("highAlerts", data.high_alerts);
        animateCounter("totalLogs", data.total_logs);

        // Update mini metrics
        const miniAssets = document.getElementById("miniAssets");
        if (miniAssets) miniAssets.innerText = data.total_assets;

        const miniThreats = document.getElementById("miniThreats");
        if (miniThreats) miniThreats.innerText = data.active_alerts;

        const miniLogs = document.getElementById("miniLogs");
        if (miniLogs) miniLogs.innerText = data.total_logs;
    } catch (error) {
        console.error(error);
    }
}

function animateCounter(id, value) {
    const element = document.getElementById(id);
    if (!element) return;

    const start = Number(element.innerText.replace(/,/g, "")) || 0;
    const duration = 350;
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
    }
}, 30000);

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
        table.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 20px;">No endpoints registered. Click 'Scan Network' to discover devices.</td></tr>`;
        return;
    }

    assets.forEach(asset => {
        let riskClass = "low";
        if (asset.risk_score >= 60) riskClass = "critical";
        else if (asset.risk_score >= 25) riskClass = "high";

        const statusClass = asset.status === "Online" ? "online" : "offline";

        table.innerHTML += `
            <tr>
                <td><strong>${escapeHtml(asset.hostname)}</strong></td>
                <td style="font-family: 'JetBrains Mono', monospace; color: var(--accent-green);">${escapeHtml(asset.ip_address)}</td>
                <td>${escapeHtml(asset.operating_system || "Unknown")}</td>
                <td><span class="sharp-badge ${riskClass}">${asset.risk_score} Risk</span></td>
                <td><span class="sharp-badge ${statusClass}">${escapeHtml(asset.status)}</span></td>
                <td style="text-align: right;">
                    <button class="sharp-btn-icon" onclick="showAssetDetails(${asset.id})" title="Inspect Device">
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
        <span>Endpoint: ${escapeHtml(asset.hostname)}</span>
    `;

    document.getElementById("drawerBody").innerHTML = `
        <table class="sharp-drawer-table">
            <tr><td>Hostname</td><td>${escapeHtml(asset.hostname)}</td></tr>
            <tr><td>IP Address</td><td>${escapeHtml(asset.ip_address)}</td></tr>
            <tr><td>MAC Address</td><td>${escapeHtml(asset.mac_address || "-")}</td></tr>
            <tr><td>Vendor Hardware</td><td>${escapeHtml(asset.vendor || "-")}</td></tr>
            <tr><td>Operating System</td><td>${escapeHtml(asset.operating_system)}</td></tr>
            <tr><td>Device Class</td><td>${escapeHtml(asset.asset_type || "Endpoint")}</td></tr>
            <tr><td>Open Ports</td><td>${escapeHtml(asset.open_ports || "-")}</td></tr>
            <tr><td>Detected Services</td><td>${escapeHtml(asset.services || "-")}</td></tr>
            <tr><td>Vulnerability Score</td><td><span class="sharp-badge ${asset.risk_score >= 60 ? 'critical' : asset.risk_score >= 25 ? 'high' : 'low'}">${asset.risk_score}/100</span></td></tr>
            <tr><td>Operational Status</td><td><span class="sharp-badge ${asset.status === 'Online' ? 'online' : 'offline'}">${escapeHtml(asset.status)}</span></td></tr>
            <tr><td>Last Scan Seen</td><td>${escapeHtml(asset.last_seen ? new Date(asset.last_seen).toLocaleString() : "-")}</td></tr>
        </table>
    `;

    openDrawer();
}

/* ===========================================================
   LOAD ALERTS
=========================================================== */
async function loadAlerts() {
    try {
        const response = await authFetch(API + "/alerts/");
        if (!response.ok) throw new Error("Unable to load alerts.");

        allAlerts = await response.json();
        renderAlerts(allAlerts);
    } catch (error) {
        console.error(error);
    }
}

function renderAlerts(alerts) {
    const table = document.getElementById("alertTable");
    if (!table) return;

    table.innerHTML = "";

    if (!alerts || alerts.length === 0) {
        table.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 20px;">No active security alerts detected.</td></tr>`;
        return;
    }

    alerts.slice(0, 50).forEach(alert => {
        const sevClass = (alert.severity || "low").toLowerCase();
        const dateStr = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : "-";
        const statusClass = alert.status === "Open" ? "open" : "acknowledged";

        table.innerHTML += `
            <tr>
                <td><span class="sharp-badge ${sevClass}">${escapeHtml(alert.severity)}</span></td>
                <td><strong>${escapeHtml(alert.title)}</strong></td>
                <td><span style="font-family: 'JetBrains Mono', monospace; color: var(--accent-green);">${escapeHtml(alert.hostname)}</span></td>
                <td><span class="sharp-badge ${statusClass}">${escapeHtml(alert.status)}</span></td>
                <td style="color: var(--text-muted); font-size: 11px;">${escapeHtml(dateStr)}</td>
                <td style="text-align: right;">
                    <button class="sharp-btn-icon" onclick="showAlertDetails('${escapeHtml(alert.id)}')" title="Triage Threat">
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
        <i class="fa-solid fa-triangle-exclamation" style="color: var(--status-critical);"></i>
        <span>Incident #${escapeHtml(alert.id)}</span>
    `;

    const dateStr = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : "-";

    document.getElementById("drawerBody").innerHTML = `
        <table class="sharp-drawer-table">
            <tr><td>Incident Title</td><td><strong>${escapeHtml(alert.title)}</strong></td></tr>
            <tr><td>Severity Level</td><td><span class="sharp-badge ${(alert.severity || 'low').toLowerCase()}">${escapeHtml(alert.severity)}</span></td></tr>
            <tr><td>Target Endpoint</td><td>${escapeHtml(alert.hostname)}</td></tr>
            <tr><td>Investigation Status</td><td><span class="sharp-badge ${alert.status === 'Open' ? 'open' : 'acknowledged'}">${escapeHtml(alert.status)}</span></td></tr>
            <tr><td>Detected Timestamp</td><td>${escapeHtml(dateStr)}</td></tr>
            <tr><td>Raw Payload / Log</td><td style="color: var(--accent-green); word-break: break-all;">${escapeHtml(alert.description)}</td></tr>
        </table>
        ${alert.status === "Open" ? `
            <div style="margin-top: 24px;">
                <button class="nav-action-btn green" style="width: 100%; justify-content: center; padding: 12px;" onclick="acknowledgeAlert('${escapeHtml(alert.id)}')">
                    <i class="fa-solid fa-check"></i>
                    <span>Acknowledge & Close Threat</span>
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

        showToast(`Incident #${alertId} acknowledged.`, "success");
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
        table.innerHTML = `<tr><td colspan="6" style="text-align:center; color: var(--text-muted); padding: 20px;">No logs available. Click 'Ingest' to process events.</td></tr>`;
        return;
    }

    logs.slice(0, 50).forEach((log, index) => {
        const sevClass = (log.level || "low").toLowerCase();
        const shortMessage = log.message && log.message.length > 70
            ? log.message.substring(0, 70) + "..."
            : (log.message || "-");
        const timeStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "-";

        table.innerHTML += `
            <tr>
                <td><span class="sharp-badge ${sevClass}">${escapeHtml(log.level)}</span></td>
                <td style="font-family: 'JetBrains Mono', monospace; color: var(--accent-green);">${escapeHtml(log.hostname)}</td>
                <td><strong>${escapeHtml(log.source)}</strong></td>
                <td style="font-family: 'JetBrains Mono', monospace; font-size: 11px;">${escapeHtml(shortMessage)}</td>
                <td style="color: var(--text-muted); font-size: 11px;">${escapeHtml(timeStr)}</td>
                <td style="text-align: right;">
                    <button class="sharp-btn-icon" onclick="showLogDetails(${index})" title="Inspect Raw Log">
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
        <i class="fa-solid fa-file-code" style="color: var(--accent-green);"></i>
        <span>Raw Security Audit Event</span>
    `;

    document.getElementById("drawerBody").innerHTML = `
        <table class="sharp-drawer-table">
            <tr><td>Host Name</td><td>${escapeHtml(log.hostname)}</td></tr>
            <tr><td>Threat Level</td><td><span class="sharp-badge ${(log.level || 'low').toLowerCase()}">${escapeHtml(log.level)}</span></td></tr>
            <tr><td>Log Source</td><td>${escapeHtml(log.source)}</td></tr>
            <tr><td>Category</td><td>${escapeHtml(log.category || "AUTH")}</td></tr>
            <tr><td>Timestamp</td><td>${escapeHtml(log.timestamp ? new Date(log.timestamp).toLocaleString() : "-")}</td></tr>
            <tr><td>Message Payload</td><td style="word-break: break-all; color: var(--accent-green);">${escapeHtml(log.message)}</td></tr>
        </table>
    `;

    openDrawer();
}

function searchLogs() {
    const input = document.getElementById("searchLog") || document.getElementById("globalSearch");
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
   ACTIONS (Network Scan & Log Ingestion)
=========================================================== */
async function scanNetwork() {
    const btn = document.getElementById("scanBtn");
    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> <span>Scanning...</span>';
    }

    try {
        const response = await authFetch(API + "/discovery/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) throw new Error("Network scan failed.");

        const data = await response.json();
        showToast(`${data.assets_discovered} assets discovered.`, "success");

        await loadDashboard();
        await loadAssets();
        await loadAlerts();
        await loadLogs();
    } catch (error) {
        console.error(error);
        showToast("Network scan failed.", "error");
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
    } catch (error) {
        console.error(error);
        showToast("Failed to ingest logs.", "error");
    }
}

/* ===========================================================
   DRAWER CONTROLLER
=========================================================== */
function openDrawer() {
    const overlay = document.getElementById("drawerOverlay");
    const drawer = document.getElementById("sharpDrawer");
    if (overlay) overlay.classList.add("active");
    if (drawer) drawer.classList.add("active");
}

function closeDrawer() {
    const overlay = document.getElementById("drawerOverlay");
    const drawer = document.getElementById("sharpDrawer");
    if (overlay) overlay.classList.remove("active");
    if (drawer) drawer.classList.remove("active");
}