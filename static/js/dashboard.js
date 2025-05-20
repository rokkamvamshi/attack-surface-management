document.getElementById('domain-form').onsubmit = function(e) {
    e.preventDefault();
    const domain = e.target[0].value;
    displayScanResults(domain);
    savePreviousScan(domain);
    e.target.reset();
};

document.getElementById('logout').onclick = function() {
    alert("Logged out successfully!");
    window.location.href = "index.html";  // Redirect to the landing page or login page
};

// Function to display scan results (Mock data)
function displayScanResults(domain) {
    const resultsContent = document.querySelector('.results-content');
    resultsContent.innerHTML = `
        <div><strong>Domain:</strong> ${domain}</div>
        <div><strong>Subdomains:</strong></div>
        <div>sub1.${domain} - <span class="result-severity-low">Alive</span></div>
        <div>sub2.${domain} - <span class="result-severity-critical">Dead</span></div>
        <div><strong>Detected Vulnerabilities:</strong></div>
        <div class="result-severity-critical">SQL Injection (Critical)</div>
        <div class="result-severity-medium">XSS (Medium)</div>
    `;
}

// Function to save previous scans
function savePreviousScan(domain) {
    const previousScansContent = document.querySelector('.previous-scans-content');
    const scanEntry = document.createElement('div');
    scanEntry.innerHTML = `<div>${new Date().toLocaleString()} - ${domain} <button onclick="viewDetails('${domain}')">View Details</button></div>`;
    previousScansContent.prepend(scanEntry);  // Add the new scan at the top
}

// Mock function to view details of a scan (can be expanded)
function viewDetails(domain) {
    alert(`Displaying details for ${domain}`);
}
