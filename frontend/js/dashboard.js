/* ===========================================================
   XDR Platform Dashboard
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

let assetChart;
let alertChart;
let logChart;
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

    updateLastUpdated();
    loadDashboard();
    loadAssets();
    loadAlerts();
    loadLogs();
    loadAnalytics();
});

/* ===========================================================
   LAST UPDATED
=========================================================== */
function updateLastUpdated() {
    const el = document.getElementById("currentDate");
    if (el) el.innerText = new Date().toLocaleString();
}

/* ===========================================================
   TOAST
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
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, 3000);
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

    const start = Number(element.innerText) || 0;
    const duration = 400;
    const startTime = performance.now();

    function update(time) {
        const progress = Math.min((time - startTime) / duration, 1);
        element.innerText = Math.floor(start + (value - start) * progress);
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

/* ===========================================================
   RENDER ASSETS
=========================================================== */
function renderAssets(assets) {
    const table = document.getElementById("assetTable");
    if (!table) return;

    table.innerHTML = "";

    if (!assets || assets.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center;">No assets found.</td>
            </tr>
        `;
        return;
    }

    assets.forEach(asset => {
        let riskClass = "low";
        let riskText = "Low";
        if (asset.risk_score >= 60) {
            riskClass = "high";
            riskText = "High";
        } else if (asset.risk_score >= 25) {
            riskClass = "medium";
            riskText = "Medium";
        }

        const statusClass = asset.status === "Online" ? "online" : "offline";
        let os = asset.operating_system || "Unknown";
        if (os.includes("Windows")) os = "Windows";
        else if (os.includes("Linux")) os = "Linux";
        else if (os.includes("Docker")) os = "Docker";
        else if (os.includes("PostgreSQL")) os = "PostgreSQL";

        table.innerHTML += `
            <tr>
                <td>${escapeHtml(asset.hostname)}</td>
                <td>${escapeHtml(asset.ip_address)}</td>
                <td>${escapeHtml(os)}</td>
                <td><span class="risk ${riskClass}">${riskText}</span></td>
                <td><span class="${statusClass}">${escapeHtml(asset.status)}</span></td>
                <td>
                    <button class="action-btn" onclick="showAssetDetails(${asset.id})">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

/* ===========================================================
   ASSET DETAILS DRAWER
=========================================================== */
function showAssetDetails(id) {
    const asset = allAssets.find(a => a.id === id);
    if (!asset) return;

    document.getElementById("drawerOverlay").classList.add("active");
    document.getElementById("assetDrawer").classList.add("active");

    document.getElementById("assetDetails").innerHTML = `
        <table class="drawer-table">
            <tr><td>Hostname</td><td>${escapeHtml(asset.hostname)}</td></tr>
            <tr><td>IP Address</td><td>${escapeHtml(asset.ip_address)}</td></tr>
            <tr><td>MAC Address</td><td>${escapeHtml(asset.mac_address || "-")}</td></tr>
            <tr><td>Vendor</td><td>${escapeHtml(asset.vendor || "-")}</td></tr>
            <tr><td>Operating System</td><td>${escapeHtml(asset.operating_system)}</td></tr>
            <tr><td>Asset Type</td><td>${escapeHtml(asset.asset_type || "Unknown")}</td></tr>
            <tr><td>Open Ports</td><td>${escapeHtml(asset.open_ports || "-")}</td></tr>
            <tr><td>Services</td><td>${escapeHtml(asset.services || "-")}</td></tr>
            <tr><td>Risk Score</td><td>${escapeHtml(asset.risk_score)}</td></tr>
            <tr><td>Status</td><td>${escapeHtml(asset.status)}</td></tr>
            <tr><td>Last Seen</td><td>${escapeHtml(asset.last_seen ? new Date(asset.last_seen).toLocaleString() : "-")}</td></tr>
        </table>
    `;
}

function closeDrawer() {
    const overlay = document.getElementById("drawerOverlay");
    const assetDrawer = document.getElementById("assetDrawer");
    const logDrawer = document.getElementById("logDrawer");
    if (overlay) overlay.classList.remove("active");
    if (assetDrawer) assetDrawer.classList.remove("active");
    if (logDrawer) logDrawer.classList.remove("active");
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

/* ===========================================================
   RENDER ALERTS
=========================================================== */
function renderAlerts(alerts) {
    const table = document.getElementById("alertTable");
    if (!table) return;

    table.innerHTML = "";

    if (!alerts || alerts.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center;">No alerts available.</td>
            </tr>
        `;
        return;
    }

    alerts.forEach((alert, index) => {
        const severity = (alert.severity || "Low").toLowerCase();
        const status = alert.status === "Open" ? "online" : "offline";
        const dateStr = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : "-";

        table.innerHTML += `
            <tr>
                <td><span class="risk ${severity}">${escapeHtml(alert.severity)}</span></td>
                <td>${escapeHtml(alert.title)}</td>
                <td>${escapeHtml(alert.hostname)}</td>
                <td><span class="${status}">${escapeHtml(alert.status)}</span></td>
                <td>${escapeHtml(dateStr)}</td>
                <td>
                    <button class="action-btn" onclick="showAlertDetails('${escapeHtml(alert.id)}')">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

/* ===========================================================
   ALERT DETAILS DRAWER
=========================================================== */
function showAlertDetails(id) {
    const alert = allAlerts.find(a => String(a.id) === String(id));
    if (!alert) return;

    document.getElementById("drawerOverlay").classList.add("active");
    document.getElementById("logDrawer").classList.add("active");

    const dateStr = alert.timestamp ? new Date(alert.timestamp).toLocaleString() : "-";

    document.getElementById("logDetails").innerHTML = `
        <table class="drawer-table">
            <tr><td>Title</td><td>${escapeHtml(alert.title)}</td></tr>
            <tr><td>Hostname</td><td>${escapeHtml(alert.hostname)}</td></tr>
            <tr><td>Severity</td><td>${escapeHtml(alert.severity)}</td></tr>
            <tr><td>Status</td><td>${escapeHtml(alert.status)}</td></tr>
            <tr><td>Time</td><td>${escapeHtml(dateStr)}</td></tr>
            <tr><td>Description</td><td>${escapeHtml(alert.description)}</td></tr>
        </table>
        ${alert.status === "Open" ? `
            <div style="margin-top: 20px; text-align: right;">
                <button class="action-btn" style="padding: 10px 18px; border-radius: 6px; background: #22c55e; color: #fff; border: none; cursor: pointer;"
                        onclick="acknowledgeAlert('${escapeHtml(alert.id)}')">
                    <i class="fa-solid fa-check"></i> Acknowledge Alert
                </button>
            </div>
        ` : ''}
    `;
}

async function acknowledgeAlert(alertId) {
    try {
        const response = await authFetch(`${API}/alerts/${alertId}/acknowledge`, {
            method: "PUT"
        });
        if (!response.ok) throw new Error("Failed to acknowledge alert");

        showToast("Alert successfully marked as Acknowledged.", "success");
        closeDrawer();
        await loadAlerts();
        await loadDashboard();
    } catch (error) {
        console.error(error);
        showToast("Failed to acknowledge alert.", "error");
    }
}

function closeLogDrawer() {
    closeDrawer();
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

/* ===========================================================
   RENDER LOGS
=========================================================== */
function renderLogs(logs) {
    const table = document.getElementById("logTable");
    if (!table) return;

    table.innerHTML = "";

    if (!logs || logs.length === 0) {
        table.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center;">No logs available.</td>
            </tr>
        `;
        return;
    }

    logs.forEach((log, index) => {
        const badge = (log.level || "Low").toLowerCase();
        const shortMessage = log.message && log.message.length > 50
            ? log.message.substring(0, 50) + "..."
            : (log.message || "-");

        const timeStr = log.timestamp ? new Date(log.timestamp).toLocaleTimeString() : "-";

        table.innerHTML += `
            <tr>
                <td><span class="risk ${badge}">${escapeHtml(log.level)}</span></td>
                <td>${escapeHtml(log.hostname)}</td>
                <td>${escapeHtml(log.source)}</td>
                <td>${escapeHtml(shortMessage)}</td>
                <td>${escapeHtml(timeStr)}</td>
                <td>
                    <button class="action-btn" onclick="showLogDetails(${index})">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                </td>
            </tr>
        `;
    });
}

/* ===========================================================
   LOG DETAILS DRAWER
=========================================================== */
function showLogDetails(index) {
    const log = allLogs[index];
    if (!log) return;

    document.getElementById("drawerOverlay").classList.add("active");
    document.getElementById("logDrawer").classList.add("active");

    const dateStr = log.timestamp ? new Date(log.timestamp).toLocaleString() : "-";

    document.getElementById("logDetails").innerHTML = `
        <table class="drawer-table">
            <tr><td>Hostname</td><td>${escapeHtml(log.hostname)}</td></tr>
            <tr><td>Severity</td><td>${escapeHtml(log.level)}</td></tr>
            <tr><td>Category</td><td>${escapeHtml(log.category || "AUTH")}</td></tr>
            <tr><td>Source</td><td>${escapeHtml(log.source)}</td></tr>
            <tr><td>Time</td><td>${escapeHtml(dateStr)}</td></tr>
            <tr><td>Message</td><td style="word-break: break-all;">${escapeHtml(log.message)}</td></tr>
        </table>
    `;
}

/* ===========================================================
   SEARCH LOGS
=========================================================== */
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
   ANALYTICS & CHARTS
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
    if (alertChart) alertChart.destroy();
    if (logChart) logChart.destroy();
    if (riskChart) riskChart.destroy();

    const assetCanvas = document.getElementById("assetChart");
    if (assetCanvas) {
        assetChart = new Chart(assetCanvas, {
            type: "doughnut",
            data: {
                labels: (data.assets_by_os || []).map(x => x.operating_system),
                datasets: [{
                    data: (data.assets_by_os || []).map(x => x.total),
                    backgroundColor: ["#38bdf8", "#818cf8", "#34d399", "#fbbf24", "#f87171"]
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    const alertCanvas = document.getElementById("alertChart");
    if (alertCanvas) {
        alertChart = new Chart(alertCanvas, {
            type: "bar",
            data: {
                labels: (data.alerts_by_severity || []).map(x => x.severity),
                datasets: [{
                    label: "Alerts",
                    data: (data.alerts_by_severity || []).map(x => x.total),
                    backgroundColor: ["#f87171", "#fbbf24", "#38bdf8"]
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }

    const logCanvas = document.getElementById("logChart");
    if (logCanvas) {
        logChart = new Chart(logCanvas, {
            type: "pie",
            data: {
                labels: (data.logs_by_source || []).map(x => x.source),
                datasets: [{
                    data: (data.logs_by_source || []).map(x => x.total),
                    backgroundColor: ["#818cf8", "#38bdf8", "#34d399", "#fbbf24"]
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
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
                    backgroundColor: ["rgba(248, 113, 113, 0.7)", "rgba(251, 191, 36, 0.7)", "rgba(56, 189, 248, 0.7)"]
                }]
            },
            options: { responsive: true, maintainAspectRatio: false }
        });
    }
}

/* ===========================================================
   NETWORK SCAN
=========================================================== */
async function scanNetwork() {
    const button = document.getElementById("scanBtn");
    if (button) {
        button.disabled = true;
        button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';
    }

    const statusEl = document.getElementById("scanStatus");
    if (statusEl) statusEl.innerText = "Scanning...";

    try {
        const response = await authFetch(API + "/discovery/scan", {
            method: "POST",
            headers: { "Content-Type": "application/json" }
        });

        if (!response.ok) throw new Error("Scan request failed.");

        const data = await response.json();
        const lastScanEl = document.getElementById("lastScan");
        if (lastScanEl) lastScanEl.innerText = new Date().toLocaleString();
        if (statusEl) statusEl.innerText = "Completed";

        showToast(`${data.assets_discovered} assets discovered.`, "success");

        await loadDashboard();
        await loadAssets();
        await loadAlerts();
        await loadLogs();
        await loadAnalytics();
        updateLastUpdated();
    } catch (error) {
        console.error(error);
        if (statusEl) statusEl.innerText = "Failed";
        showToast("Network scan failed.", "error");
    } finally {
        if (button) {
            button.disabled = false;
            button.innerHTML = '<i class="fa-solid fa-network-wired"></i> Scan Network';
        }
    }
}

/* ===========================================================
   TRIGGER LOG COLLECTION
=========================================================== */
async function triggerLogCollection() {
    try {
        const response = await authFetch(API + "/logs/collect", {
            method: "POST"
        });
        if (!response.ok) throw new Error("Failed to collect logs");

        const data = await response.json();
        showToast(
            `Collected ${data.summary.logs_parsed} logs, ${data.summary.new_alerts_generated} new alerts detected.`,
            "success"
        );
        await loadDashboard();
        await loadAlerts();
        await loadLogs();
        await loadAnalytics();
    } catch (error) {
        console.error(error);
        showToast("Failed to collect logs.", "error");
    }
}

console.log(
    "%cXDR Platform Dashboard Initialized with JWT & XSS Guard",
    "color:#38bdf8;font-size:14px;font-weight:bold;"
);