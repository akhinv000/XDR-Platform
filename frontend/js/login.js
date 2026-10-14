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

function showToast(message, type = "info") {
    const toast = document.createElement("div");
    toast.className = `toast ${type}`;
    toast.innerText = message;
    document.body.appendChild(toast);

    setTimeout(() => {
        toast.remove();
    }, 3000);
}

async function login() {
    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();
    const message = document.getElementById("message");
    const button = document.querySelector("button");

    if (username === "" || password === "") {
        message.style.color = "#ff5c5c";
        message.innerText = "Please enter your username and password.";
        return;
    }

    button.disabled = true;
    button.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Signing In...';

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
            message.style.color = "#22c55e";
            message.innerText = "Authentication successful.";

            // Store JWT access token and user metadata
            localStorage.setItem("token", data.access_token);
            localStorage.setItem("username", data.username);

            setTimeout(() => {
                window.location.href = "dashboard.html";
            }, 800);
        } else {
            message.style.color = "#ff5c5c";
            message.innerText = data.detail || "Invalid username or password.";
        }
    } catch (error) {
        console.error("Login Error:", error);
        message.style.color = "#ff5c5c";
        message.innerText = "Connection failed. Please ensure the backend server is running.";
    } finally {
        button.disabled = false;
        button.innerHTML = '<i class="fa-solid fa-right-to-bracket"></i> Sign In';
    }
}