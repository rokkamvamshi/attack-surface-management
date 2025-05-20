document.getElementById('signup-form').onsubmit = function(e) {
    e.preventDefault();
    alert('Sign-up successful! Please log in.');
    document.getElementById('signup').style.display = 'none';
    document.getElementById('login').style.display = 'block';
};

document.getElementById('login-form').onsubmit = function(e) {
    e.preventDefault();
    document.getElementById('login').style.display = 'none';
    document.getElementById('dashboard').style.display = 'block';
};

document.getElementById('logout').onclick = function() {
    document.getElementById('dashboard').style.display = 'none';
    document.getElementById('login').style.display = 'block';
};

// Example: Domain Scan and Results
document.getElementById('domain-form').onsubmit = function(e) {
    e.preventDefault();
    const domainInput = e.target[0].value;
    // Here you can implement the scanning functionality
    // For now, let's just display dummy results
    const resultsSection = document.querySelector('.results-section');
    resultsSection.innerHTML = `
        <div>Subdomains for ${domainInput}:</div>
        <div>sub1.${domainInput} - <span style="color: green;">Alive</span></div>
        <div>sub2.${domainInput} - <span style="color: red;">Dead</span></div>
        <div>Detected Vulnerabilities:</div>
        <div style="color: red;">SQL Injection (Critical)</div>
        <div style="color: yellow;">XSS (Medium)</div>
    `;
    e.target.reset();
};
