// Hardcoded credentials (for demonstration only; replace with backend authentication in production)
const correctEmail = "user@example.com";
const correctPassword = "password123";

document.getElementById("login-form").addEventListener("submit", function(event) {
    event.preventDefault(); // Prevent form from submitting

    const email = document.getElementById("login-email").value;
    const password = document.getElementById("login-password").value;

    // Validate credentials
    if (email === correctEmail && password === correctPassword) {
        window.location.href = "dashboard.html"; // Redirect to dashboard
    } else {
        alert("Incorrect email or password. Please try again.");
    }
});

// Logout function
function logout() {
    window.location.href = "login.html"; // Redirect to login page on logout
}
