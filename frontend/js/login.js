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

// Live UTC HUD Clock
function updateClock() {
    const clock = document.getElementById("hudClock");
    if (!clock) return;
    const now = new Date();
    clock.innerText = "UTC " + now.toUTCString().split(" ")[4];
}
setInterval(updateClock, 1000);
updateClock();

// Toggle Password Visibility
function togglePasswordVisibility() {
    const pw = document.getElementById("password");
    const icon = document.getElementById("pwToggleIcon");
    if (!pw || !icon) return;
    if (pw.type === "password") {
        pw.type = "text";
        icon.className = "fa-solid fa-eye-slash";
    } else {
        pw.type = "password";
        icon.className = "fa-solid fa-eye";
    }
}

// Quick Credentials Autofill
function fillQuickCreds() {
    const u = document.getElementById("username");
    const p = document.getElementById("password");
    if (u) u.value = "admin";
    if (p) p.value = "admin123";
    const msg = document.getElementById("message");
    if (msg) {
        msg.style.color = "#C084FC";
        msg.innerText = "Default credentials loaded. Press Authenticate to enter.";
    }
}

// Enter Key Submission Listener
document.addEventListener("keydown", (e) => {
    if (e.key === "Enter") {
        const u = document.getElementById("username");
        const p = document.getElementById("password");
        if (document.activeElement === u || document.activeElement === p || !document.activeElement) {
            login();
        }
    }
});

// Primary Login Authentication Function
async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const message = document.getElementById("message");
    const button = document.querySelector(".btn-authenticate") || document.querySelector("button");

    if (username === "" || password === "") {
        message.style.color = "#FF4438";
        message.innerText = "Please specify operator identity and passcode.";
        return;
    }

    button.disabled = true;
    const originalContent = button.innerHTML;
    button.innerHTML = '<i class="fa-solid fa-circle-notch fa-spin"></i> <span>Verifying Security Token...</span>';

    try {
        const response = await fetch(API + "/login", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                username,
                password
            })
        });

        const data = await response.json();

        if (response.ok) {
            message.style.color = "#00d27a";
            message.innerHTML = '<i class="fa-solid fa-check-circle"></i> Token verified. Granting SOC Access...';

            // Store JWT access token and user metadata
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("username", data.username);

            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 600);
        } else {
            message.style.color = "#FF4438";
            message.innerHTML = '<i class="fa-solid fa-triangle-exclamation"></i> ' + (data.detail || "Authentication rejected: Invalid credentials.");
        }
    } catch (error) {
        console.error("Login Error:", error);
        message.style.color = "#FF4438";
        message.innerHTML = '<i class="fa-solid fa-plug-circle-xmark"></i> Connection failed: Backend API (port 9000) unreachable.';
    } finally {
        button.disabled = false;
        button.innerHTML = originalContent;
    }
}