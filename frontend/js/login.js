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

    const API = "http://127.0.0.1:9000";

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

            localStorage.setItem("username", data.username);

            setTimeout(() => {

                window.location.href = "dashboard.html";

            }, 1000);

        }

        else {

            message.style.color = "#ff5c5c";
            message.innerText = data.detail || "Invalid username or password.";


        }

    }

    catch (error) {

    console.error("Login Error:", error);

    message.style.color = "#ff5c5c";
    message.innerText = error.message;

    }

    finally {

        button.disabled = false;

        button.innerHTML =
            '<i class="fa-solid fa-right-to-bracket"></i> Sign In';

    }

}