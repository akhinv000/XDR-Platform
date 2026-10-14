/* ===========================================================
   XDR Platform Dashboard
=========================================================== */

const API = "http://127.0.0.1:9000";

let allAssets = [];
let allLogs = [];
let allAlerts = [];

let assetChart;
let alertChart;
let logChart;
let riskChart;

/* ===========================================================
INITIALIZE
=========================================================== */

document.addEventListener("DOMContentLoaded", () => {

    const username =
        localStorage.getItem("username") || "Administrator";

    document.getElementById("username").innerText = username;

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

    document.getElementById("currentDate").innerText =
        new Date().toLocaleString();

}

/* ===========================================================
TOAST
=========================================================== */

function showToast(message, type = "info") {

    const container =
        document.getElementById("toastContainer");

    const toast =
        document.createElement("div");

    toast.className = `toast ${type}`;

    let icon = "fa-circle-info";

    if (type === "success")
        icon = "fa-circle-check";

    else if (type === "error")
        icon = "fa-circle-xmark";

    else if (type === "warning")
        icon = "fa-triangle-exclamation";

    toast.innerHTML = `

        <i class="fa-solid ${icon}"></i>

        <span>${message}</span>

    `;

    container.appendChild(toast);

    setTimeout(() => {

        toast.style.animation =
            "slideOut .3s forwards";

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
LOAD DASHBOARD
=========================================================== */

async function loadDashboard() {

    try {

        const response = await fetch(
            API + "/dashboard/stats"
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load dashboard statistics."
            );

        }

        const data = await response.json();

        animateCounter(
            "totalAssets",
            data.total_assets
        );

        animateCounter(
            "activeAlerts",
            data.active_alerts
        );

        animateCounter(
            "highAlerts",
            data.high_alerts
        );

        animateCounter(
            "totalLogs",
            data.total_logs
        );

        updateLastUpdated();

    }

    catch (error) {

        console.error(error);

        showToast(
            "Unable to load dashboard.",
            "error"
        );

    }

}

/* ===========================================================
COUNTER ANIMATION
=========================================================== */

function animateCounter(id, value) {

    const element =
        document.getElementById(id);

    const start =
        Number(element.innerText) || 0;

    const duration = 500;

    const startTime =
        performance.now();

    function update(time) {

        const progress =
            Math.min(
                (time - startTime) / duration,
                1
            );

        element.innerText =
            Math.floor(
                start +
                (value - start) * progress
            );

        if (progress < 1) {

            requestAnimationFrame(update);

        }

    }

    requestAnimationFrame(update);

}

/* ===========================================================
AUTO REFRESH
=========================================================== */

setInterval(() => {

    loadDashboard();

    loadAssets();

    loadAlerts();

    loadLogs();

    loadAnalytics();

    updateLastUpdated();

}, 30000);

/* ===========================================================
LOAD ASSETS
=========================================================== */

async function loadAssets() {

    try {

        const response = await fetch(
            API + "/assets/"
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load assets."
            );

        }

        allAssets =
            await response.json();

        renderAssets(allAssets);

    }

    catch (error) {

        console.error(error);

        showToast(
            "Unable to load assets.",
            "error"
        );

    }

}

/* ===========================================================
RENDER ASSETS
=========================================================== */

function renderAssets(assets) {

    const table =
        document.getElementById("assetTable");

    table.innerHTML = "";

    if (assets.length === 0) {

        table.innerHTML = `

        <tr>

            <td colspan="6"
                style="text-align:center;">

                No assets found.

            </td>

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

        }

        else if (asset.risk_score >= 25) {

            riskClass = "medium";
            riskText = "Medium";

        }

        let statusClass =
            asset.status === "Online"
            ? "online"
            : "offline";

        let os =
            asset.operating_system || "Unknown";

        if (os.includes("Windows"))
            os = "Windows";

        else if (os.includes("Linux"))
            os = "Linux";

        else if (os.includes("Docker"))
            os = "Docker";

        else if (os.includes("PostgreSQL"))
            os = "PostgreSQL";

        table.innerHTML += `

        <tr>

            <td>

                ${asset.hostname}

            </td>

            <td>

                ${asset.ip_address}

            </td>

            <td>

                ${os}

            </td>

            <td>

                <span class="risk ${riskClass}">

                    ${riskText}

                </span>

            </td>

            <td>

                <span class="${statusClass}">

                    ${asset.status}

                </span>

            </td>

            <td>

                <button
                    class="action-btn"
                    onclick="showAssetDetails(${asset.id})">

                    <i class="fa-solid fa-eye"></i>

                </button>

            </td>

        </tr>

        `;

    });

}

/* ===========================================================
ASSET DETAILS
=========================================================== */

function showAssetDetails(id) {

    const asset =
        allAssets.find(a => a.id === id);

    if (!asset)
        return;

    document
        .getElementById("drawerOverlay")
        .classList
        .add("active");

    document
        .getElementById("assetDrawer")
        .classList
        .add("active");

    document
        .getElementById("assetDetails")
        .innerHTML = `

        <table class="drawer-table">

            <tr>

                <td>Hostname</td>

                <td>${asset.hostname}</td>

            </tr>

            <tr>

                <td>IP Address</td>

                <td>${asset.ip_address}</td>

            </tr>

            <tr>

                <td>MAC Address</td>

                <td>${asset.mac_address || "-"}</td>

            </tr>

            <tr>

                <td>Operating System</td>

                <td>${asset.operating_system}</td>

            </tr>

            <tr>

                <td>Open Ports</td>

                <td>${asset.open_ports || "-"}</td>

            </tr>

            <tr>

                <td>Risk Score</td>

                <td>${asset.risk_score}</td>

            </tr>

            <tr>

                <td>Status</td>

                <td>${asset.status}</td>

            </tr>

        </table>

    `;

}

/* ===========================================================
CLOSE ASSET DRAWER
=========================================================== */

function closeDrawer() {

    document
        .getElementById("drawerOverlay")
        .classList
        .remove("active");

    document
        .getElementById("assetDrawer")
        .classList
        .remove("active");

    document
        .getElementById("logDrawer")
        .classList
        .remove("active");

}

/* ===========================================================
LOAD ALERTS
=========================================================== */

async function loadAlerts() {

    try {

        const response = await fetch(
            API + "/alerts/"
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load alerts."
            );

        }

        allAlerts =
            await response.json();

        renderAlerts(allAlerts);

    }

    catch (error) {

        console.error(error);

    }

}

/* ===========================================================
RENDER ALERTS
=========================================================== */

function renderAlerts(alerts) {

    const table =
        document.getElementById("alertTable");

    table.innerHTML = "";

    if (alerts.length === 0) {

        table.innerHTML = `

        <tr>

            <td colspan="6"
                style="text-align:center;">

                No alerts available.

            </td>

        </tr>

        `;

        return;

    }

    alerts.forEach(alert => {

        let severity = "low";

        if (alert.severity === "High")
            severity = "high";

        else if (alert.severity === "Medium")
            severity = "medium";

        let status = "offline";

        if (alert.status === "Open")
            status = "online";

        table.innerHTML += `

        <tr>

            <td>

                <span class="risk ${severity}">

                    ${alert.severity}

                </span>

            </td>

            <td>

                ${alert.title}

            </td>

            <td>

                ${alert.hostname}

            </td>

            <td>

                <span class="${status}">

                    ${alert.status}

                </span>

            </td>

            <td>

                ${new Date(alert.timestamp)
                    .toLocaleString()}

            </td>

            <td>

                <button
                    class="action-btn"
                    onclick="showAlertDetails(${alert.id})">

                    <i class="fa-solid fa-eye"></i>

                </button>

            </td>

        </tr>

        `;

    });

}

/* ===========================================================
ALERT DETAILS
=========================================================== */

function showAlertDetails(id) {

    const alert =
        allAlerts.find(a => a.id === id);

    if (!alert)
        return;

    document
        .getElementById("drawerOverlay")
        .classList
        .add("active");

    document
        .getElementById("logDrawer")
        .classList
        .add("active");

    document
        .getElementById("logDetails")
        .innerHTML = `

        <table class="drawer-table">

            <tr>

                <td>Title</td>

                <td>${alert.title}</td>

            </tr>

            <tr>

                <td>Hostname</td>

                <td>${alert.hostname}</td>

            </tr>

            <tr>

                <td>Severity</td>

                <td>${alert.severity}</td>

            </tr>

            <tr>

                <td>Status</td>

                <td>${alert.status}</td>

            </tr>

            <tr>

                <td>Time</td>

                <td>${new Date(alert.timestamp).toLocaleString()}</td>

            </tr>

            <tr>

                <td>Description</td>

                <td>${alert.description}</td>

            </tr>

        </table>

    `;

}

/* ===========================================================
CLOSE LOG DRAWER
=========================================================== */

function closeLogDrawer() {

    closeDrawer();

}

/* ===========================================================
LOAD LOGS
=========================================================== */

async function loadLogs() {

    try {

        const response = await fetch(
            API + "/logs/"
        );

        if (!response.ok) {

            throw new Error(
                "Unable to load logs."
            );

        }

        allLogs =
            await response.json();

        renderLogs(allLogs);

    }

    catch (error) {

        console.error(error);

    }

}

/* ===========================================================
RENDER LOGS
=========================================================== */

function renderLogs(logs) {

    const table = document.getElementById("logTable");

    table.innerHTML = "";

    if (logs.length === 0) {

        table.innerHTML = `
            <tr>
                <td colspan="6" style="text-align:center;">
                    No logs available.
                </td>
            </tr>
        `;

        return;

    }

    logs.forEach((log, index) => {

        // High / Medium / Low -> high / medium / low
        const badge = (log.level || "Low").toLowerCase();

        const shortMessage =
            log.message && log.message.length > 50
                ? log.message.substring(0, 50) + "..."
                : (log.message || "-");

        table.innerHTML += `

            <tr>

                <td>
                    <span class="risk ${badge}">
                        ${log.level}
                    </span>
                </td>

                <td>
                    ${log.hostname}
                </td>

                <td>
                    ${log.source}
                </td>

                <td>
                    ${shortMessage}
                </td>

                <td>
                    ${new Date(log.timestamp).toLocaleTimeString()}
                </td>

                <td>

                    <button
                        class="action-btn"
                        onclick="showLogDetails(${index})">

                        <i class="fa-solid fa-eye"></i>

                    </button>

                </td>

            </tr>

        `;

    });

}

/* ===========================================================
LOG DETAILS
=========================================================== */

function showLogDetails(index) {

    const log = allLogs[index];

    document
        .getElementById("drawerOverlay")
        .classList
        .add("active");

    document
        .getElementById("logDrawer")
        .classList
        .add("active");

    document
        .getElementById("logDetails")
        .innerHTML = `

        <table class="drawer-table">

            <tr>
                <td>Hostname</td>
                <td>${log.hostname}</td>
            </tr>

            <tr>
                <td>Severity</td>
                <td>${log.level}</td>
            </tr>

            <tr>
                <td>Category</td>
                <td>${log.category}</td>
            </tr>

            <tr>
                <td>Source</td>
                <td>${log.source}</td>
            </tr>

            <tr>
                <td>Time</td>
                <td>${new Date(log.timestamp).toLocaleString()}</td>
            </tr>

            <tr>
                <td>Message</td>
                <td>${log.message}</td>
            </tr>

        </table>

    `;

}

/* ===========================================================
SEARCH LOGS
=========================================================== */

function searchLogs() {

    const keyword =
        document
        .getElementById("searchLog")
        .value
        .toLowerCase();

    const filtered =

        allLogs.filter(log =>

            log.hostname
                .toLowerCase()
                .includes(keyword)

            ||

            log.source
                .toLowerCase()
                .includes(keyword)

            ||

            log.level
                .toLowerCase()
                .includes(keyword)

            ||

            log.message
                .toLowerCase()
                .includes(keyword)

        );

    renderLogs(filtered);

}

/* ===========================================================
ANALYTICS
=========================================================== */

async function loadAnalytics() {

    try {

        const response = await fetch(
            API + "/analytics/"
        );

        if (!response.ok) {

            throw new Error("Unable to load analytics.");

        }

        const data = await response.json();

        console.log(data);

        createCharts(data);

    }

    catch (error) {

        console.error(error);

    }

}

function createCharts(data) {

    if (assetChart) assetChart.destroy();
    if (alertChart) alertChart.destroy();
    if (logChart) logChart.destroy();
    if (riskChart) riskChart.destroy();

    assetChart = new Chart(
        document.getElementById("assetChart"),
        {
            type: "doughnut",
            data: {
                labels: data.assets_by_os.map(x => x.operating_system),
                datasets: [{
                    data: data.assets_by_os.map(x => x.total)
                }]
            }
        }
    );

    alertChart = new Chart(
        document.getElementById("alertChart"),
        {
            type: "bar",
            data: {
                labels: data.alerts_by_severity.map(x => x.severity),
                datasets: [{
                    label: "Alerts",
                    data: data.alerts_by_severity.map(x => x.total)
                }]
            }
        }
    );

    logChart = new Chart(
        document.getElementById("logChart"),
        {
            type: "pie",
            data: {
                labels: data.logs_by_source.map(x => x.source),
                datasets: [{
                    data: data.logs_by_source.map(x => x.total)
                }]
            }
        }
    );

    riskChart = new Chart(
        document.getElementById("riskChart"),
        {
            type: "polarArea",
            data: {
                labels: data.risk_distribution.map(x => x.level),
                datasets: [{
                    data: data.risk_distribution.map(x => x.total)
                }]
            }
        }
    );

}

/* ===========================================================
NETWORK SCAN
=========================================================== */

async function scanNetwork() {

    const button =
        document.getElementById("scanBtn");

    button.disabled = true;

    button.innerHTML =

        '<i class="fa-solid fa-spinner fa-spin"></i> Scanning...';

    document.getElementById("scanStatus").innerText =
        "Scanning...";

    try {

        const response = await fetch(

            API + "/discovery/scan",

            {

                method:"POST"

            }

        );

        if(!response.ok){

            throw new Error(
                "Scan failed."
            );

        }

        const data =
            await response.json();

        document.getElementById("lastScan").innerText =

            new Date().toLocaleString();

        document.getElementById("scanStatus").innerText =
            "Completed";

        showToast(

            `${data.assets_discovered} assets discovered.`,

            "success"

        );

        await loadDashboard();

        await loadAssets();

        await loadAlerts();

        await loadLogs();

        await loadAnalytics();

        updateLastUpdated();

    }

    catch(error){

        console.error(error);

        document.getElementById("scanStatus").innerText =
            "Failed";

        showToast(

            "Network scan failed.",

            "error"

        );

    }

    finally{

        button.disabled = false;

        button.innerHTML =

        '<i class="fa-solid fa-network-wired"></i> Scan Network';

    }

}

/* ===========================================================
CONSOLE
=========================================================== */

console.log(

"%cXDR Platform Dashboard Loaded",

"color:#38bdf8;font-size:15px;font-weight:bold;"

);