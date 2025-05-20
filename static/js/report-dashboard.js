/**
 * Report Dashboard JavaScript
 * This file contains functions for rendering the security dashboard and
 * handling data fetching from the server API.
 */

// Function to render executive summary based on report data
function renderExecutiveSummary(reportData) {
    console.log('Rendering executive summary with data:', reportData);
    const summary = reportData.summary;
    
    // Create risk level badge class based on risk level
    const riskLevelClass = `risk-${summary.risk_level.toLowerCase()}`;
    
    // Build the summary HTML
    let summaryHtml = `
        <div class="fade-in">
            <div class="alert alert-primary d-flex justify-content-between align-items-center mb-4">
                <div>
                    <h4 class="alert-heading">Security Report: ${summary.domain || 'All Domains'}</h4>
                    <p class="mb-0">Generated on ${new Date().toLocaleDateString()}</p>
                </div>
                <div class="text-end">
                    <span class="risk-badge ${riskLevelClass}">
                        Risk Level: ${summary.risk_level}
                    </span>
                    <div class="small mt-1">Risk Score: ${summary.risk_score}</div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-4 mb-3">
                    <div class="stat-card">
                        <div class="stat-label">Scanned Subdomains</div>
                        <div class="stat-value">${summary.subdomains_count}</div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="stat-card">
                        <div class="stat-label">Total Vulnerabilities</div>
                        <div class="stat-value">${summary.total_vulnerabilities}</div>
                    </div>
                </div>
                <div class="col-md-4 mb-3">
                    <div class="stat-card">
                        <div class="stat-label">Critical Issues</div>
                        <div class="stat-value text-danger">${summary.critical_count}</div>
                    </div>
                    </div>
                </div>
            </div>
            
            <div class="row mb-4">
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <i class="fas fa-exclamation-triangle me-2"></i>Top Vulnerabilities
                        </div>
                        <div class="card-body">
                            <ul class="list-group list-group-flush">
    `;
    
    // Add top vulnerability items
    if (summary.top_vulnerabilities && summary.top_vulnerabilities.length > 0) {
        summary.top_vulnerabilities.forEach(vuln => {
            summaryHtml += `
                <li class="list-group-item d-flex align-items-center border-0 px-0">
                    <span class="badge bg-primary rounded-pill me-2">
                        <i class="fas fa-bug"></i>
                    </span>
                    ${vuln}
                </li>
            `;
        });
    } else {
        summaryHtml += `<li class="list-group-item border-0 px-0">No vulnerabilities found</li>`;
    }
    
    summaryHtml += `
                            </ul>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <i class="fas fa-sitemap me-2"></i>Most Vulnerable Subdomains
                        </div>
                        <div class="card-body">
                            <ul class="list-group list-group-flush">
    `;
    
    // Add vulnerable subdomain items
    if (summary.top_vulnerable_subdomains && summary.top_vulnerable_subdomains.length > 0) {
        summary.top_vulnerable_subdomains.forEach(subdomain => {
            summaryHtml += `
                <li class="list-group-item d-flex align-items-center border-0 px-0">
                    <span class="badge bg-danger rounded-pill me-2">
                        <i class="fas fa-globe"></i>
                    </span>
                    ${subdomain}
                </li>
            `;
        });
    } else {
        summaryHtml += `<li class="list-group-item border-0 px-0">No vulnerable subdomains found</li>`;
    }
    
    summaryHtml += `
                            </ul>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <i class="fas fa-tasks me-2"></i>Recommendations
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <h5 class="text-danger">Critical Priority</h5>
                        <p>${summary.critical_count > 0 
                            ? "Immediately address all critical vulnerabilities identified in this report."
                            : "No critical vulnerabilities were identified."}</p>
                    </div>
                    
                    <div class="mb-3">
                        <h5 class="text-warning">High Priority</h5>
                        <p>${summary.high_count > 0 
                            ? "Address high severity vulnerabilities within the next two weeks."
                            : "No high severity vulnerabilities were identified."}</p>
                    </div>
                    
                    <div>
                        <h5 class="text-primary">Next Steps</h5>
                        <p>Generate a detailed PDF report to view comprehensive findings and specific remediation recommendations.</p>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insert the HTML into the summary tab
    document.getElementById('summary').innerHTML = summaryHtml;
}

// Function to render visualizations based on report data
function renderVisualizations(reportData) {
    console.log('Rendering visualizations with data:', reportData);
    const charts = reportData.charts;
    
    // Filter out the "Info" category from severity distribution
    const filteredSeverityDistribution = charts.severity_distribution.filter(item => 
        item.name.toLowerCase() !== 'info'
    );
    
    // Build the visualizations HTML
    let visualizationsHtml = `
        <div class="fade-in">
            <div class="row mb-4">
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <i class="fas fa-chart-pie me-2"></i>Severity Distribution
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="severityChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="col-md-6 mb-3">
                    <div class="card h-100">
                        <div class="card-header">
                            <i class="fas fa-chart-bar me-2"></i>Top Vulnerabilities
                        </div>
                        <div class="card-body">
                            <div class="chart-container">
                                <canvas id="vulnerabilityChart"></canvas>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="card mb-4">
                <div class="card-header">
                    <i class="fas fa-chart-bar me-2"></i>Most Vulnerable Subdomains
                </div>
                <div class="card-body">
                    <div class="chart-container">
                        <canvas id="subdomainChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insert the HTML into the visualization tab
    document.getElementById('visualization').innerHTML = visualizationsHtml;
    
    // Define color constants
    const COLORS = {
        critical: '#e63946',
        high: '#f94144',
        medium: '#f8961e',
        low: '#90be6d'
    };
    
    // Render the severity distribution chart
    const severityCtx = document.getElementById('severityChart').getContext('2d');
    new Chart(severityCtx, {
        type: 'doughnut',
        data: {
            labels: filteredSeverityDistribution.map(item => item.name),
            datasets: [{
                data: filteredSeverityDistribution.map(item => item.value),
                backgroundColor: [
                    COLORS.critical,
                    COLORS.high,
                    COLORS.medium,
                    COLORS.low
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const value = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = Math.round((value / total) * 100);
                            return `${context.label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            },
            cutout: '60%'
        }
    });
    
    // Render the top vulnerabilities chart
    const vulnCtx = document.getElementById('vulnerabilityChart').getContext('2d');
    new Chart(vulnCtx, {
        type: 'bar',
        data: {
            labels: charts.top_vulnerabilities.map(item => item.name),
            datasets: [{
                label: 'Count',
                data: charts.top_vulnerabilities.map(item => item.value),
                backgroundColor: 'rgba(67, 97, 238, 0.7)',
                borderColor: 'rgba(67, 97, 238, 1)',
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            indexAxis: 'y',
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                x: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Count'
                    }
                }
            }
        }
    });
    
    // Render the vulnerable subdomains chart
    const subdomainCtx = document.getElementById('subdomainChart').getContext('2d');
    new Chart(subdomainCtx, {
        type: 'bar',
        data: {
            labels: charts.top_vulnerable_subdomains.map(item => item.name),
            datasets: [
                {
                    label: 'Critical',
                    data: charts.top_vulnerable_subdomains.map(item => item.critical),
                    backgroundColor: COLORS.critical,
                    stack: 'Stack 0'
                },
                {
                    label: 'High',
                    data: charts.top_vulnerable_subdomains.map(item => item.high),
                    backgroundColor: COLORS.high,
                    stack: 'Stack 0'
                },
                {
                    label: 'Medium',
                    data: charts.top_vulnerable_subdomains.map(item => item.medium),
                    backgroundColor: COLORS.medium,
                    stack: 'Stack 0'
                },
                {
                    label: 'Low',
                    data: charts.top_vulnerable_subdomains.map(item => item.low),
                    backgroundColor: COLORS.low,
                    stack: 'Stack 0'
                }
                // Info category removed
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                }
            },
            scales: {
                x: {
                    stacked: true,
                },
                y: {
                    stacked: true,
                    beginAtZero: true
                }
            }
        }
    });
}

// Function to render export options based on report data
function renderExportOptions(reportData) {
    console.log('Rendering export options with data:', reportData);
    // Build base URL with filters
    const baseExportUrl = '/reports/generate/';
    const domain = document.getElementById('domainSelect').value;
    const dateRange = document.getElementById('dateRange').value;
    
    // Build query parameters
    const params = new URLSearchParams();
    if (domain) params.append('domain', domain);
    if (dateRange) params.append('date_range', dateRange);
    
    // Build URLs for different formats
    const pdfUrl = `${baseExportUrl}?${params.toString()}&type=pdf`;
    const csvUrl = `${baseExportUrl}?${params.toString()}&type=csv`;
    const jsonUrl = `${baseExportUrl}?${params.toString()}&type=json`;
    
    // Build the export options HTML
    let exportHtml = `
        <div class="fade-in p-3">
            <div class="alert alert-info mb-4">
                <i class="fas fa-info-circle me-2"></i>
                Generate comprehensive security reports in various formats to share with stakeholders.
            </div>
            
            <div class="row">
                <div class="col-md-4 mb-4">
                    <div class="export-card">
                        <div class="export-icon text-danger">
                            <i class="fas fa-file-pdf"></i>
                        </div>
                        <h4>PDF Report</h4>
                        <p class="text-muted mb-4">Complete report with executive summary, visuals, and technical details</p>
                        <a href="${pdfUrl}" target="_blank" class="btn btn-danger">
                            <i class="fas fa-download me-2"></i>Export as PDF
                        </a>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="export-card">
                        <div class="export-icon text-success">
                            <i class="fas fa-file-csv"></i>
                        </div>
                        <h4>CSV Export</h4>
                        <p class="text-muted mb-4">Detailed findings in spreadsheet format for further analysis</p>
                        <a href="${csvUrl}" target="_blank" class="btn btn-success">
                            <i class="fas fa-download me-2"></i>Export as CSV
                        </a>
                    </div>
                </div>
                
                <div class="col-md-4 mb-4">
                    <div class="export-card">
                        <div class="export-icon text-primary">
                            <i class="fas fa-file-code"></i>
                        </div>
                        <h4>JSON Data</h4>
                        <p class="text-muted mb-4">Raw report data for integration with other security tools</p>
                        <a href="${jsonUrl}" target="_blank" class="btn btn-primary">
                            <i class="fas fa-download me-2"></i>Export as JSON
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="card mt-4">
                <div class="card-header">
                    <i class="fas fa-cog me-2"></i>Advanced Export Options
                </div>
                <div class="card-body">
                    <form id="customExportForm" class="row g-3">
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="includeScreenshots" value="true">
                                <label class="form-check-label" for="includeScreenshots">
                                    Include screenshots of vulnerable pages
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="includeRecommendations" value="true" checked>
                                <label class="form-check-label" for="includeRecommendations">
                                    Include detailed recommendations
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="includeExecutiveSummary" value="true" checked>
                                <label class="form-check-label" for="includeExecutiveSummary">
                                    Include executive summary
                                </label>
                            </div>
                        </div>
                        <div class="col-md-6">
                            <div class="form-check">
                                <input class="form-check-input" type="checkbox" id="includeCharts" value="true" checked>
                                <label class="form-check-label" for="includeCharts">
                                    Include charts and visualizations
                                </label>
                            </div>
                        </div>
                        <div class="col-12 mt-4">
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-cogs me-2"></i>Generate Custom Report
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    `;
    
    // Insert the HTML into the export tab
    document.getElementById('export').innerHTML = exportHtml;
    
    // Set up custom export form handler
    document.getElementById('customExportForm').addEventListener('submit', function(e) {
        e.preventDefault();
        
        // Build custom export URL with options
        const customParams = new URLSearchParams(params);
        customParams.append('type', 'pdf');  // Default to PDF for custom exports
        
        // Add custom options
        if (document.getElementById('includeScreenshots').checked)
            customParams.append('screenshots', 'true');
        if (document.getElementById('includeRecommendations').checked)
            customParams.append('recommendations', 'true');
        if (document.getElementById('includeExecutiveSummary').checked)
            customParams.append('summary', 'true');
        if (document.getElementById('includeCharts').checked)
            customParams.append('charts', 'true');
        
        // Navigate to the custom export URL
        window.open(`${baseExportUrl}?${customParams.toString()}`, '_blank');
    });
}

// Function to fetch report data from API
function fetchReportData() {
    console.log('Fetching report data...');
    
    // Show loading indicator
    document.getElementById('initialState').style.display = 'none';
    document.getElementById('loadingIndicator').style.display = 'block';
    document.getElementById('dashboardContent').style.display = 'none';
    
    // Get filter values
    const domain = document.getElementById('domainSelect').value || '';
    const dateRange = document.getElementById('dateRange').value || '';
    
    // Debug the filter values
    console.log('Fetching report data with filters:', { domain, dateRange });
    
    // Build API URL with current page path
    const params = new URLSearchParams();
    params.append('data', 'json'); // Request JSON data
    if (domain) params.append('domain', domain);
    if (dateRange) params.append('date_range', dateRange);
    params.append('hide_info', 'true'); // Add parameter to hide info counts
    
    const fullUrl = `${window.location.pathname}?${params.toString()}`;
    console.log('API Request URL:', fullUrl);
    
    // Add a timestamp to prevent caching issues
    const cacheBuster = new Date().getTime();
    const urlWithCacheBuster = `${fullUrl}&_=${cacheBuster}`;
    
    // Fetch data from API with detailed error handling
    fetch(urlWithCacheBuster, {
        method: 'GET',
        headers: {
            'Accept': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
        },
        credentials: 'same-origin'
    })
    .then(response => {
        console.log('API Response Status:', response.status);
        if (!response.ok) {
            return response.text().then(text => {
                console.error('Error response text:', text);
                throw new Error(`HTTP error: ${response.status} - ${response.statusText}`);
            });
        }
        return response.json();
    })
    .then(data => {
        console.log('API Response Data:', data);
        
        // Hide loading indicator
        document.getElementById('loadingIndicator').style.display = 'none';
        
        // If error in response
        if (data.error) {
            console.error('API error:', data.error);
            alert(`Error: ${data.error}`);
            document.getElementById('initialState').style.display = 'block';
            return;
        }
        
        // If no data, show message
        if (!data || !data.summary) {
            console.error('API response missing summary data');
            document.getElementById('initialState').style.display = 'block';
            alert('No report data found for the selected filters.');
            return;
        }
        
        // Process the data to remove info counts if they exist
        if (data.summary) {
            // Remove info_count if it exists
            if ('info_count' in data.summary) {
                delete data.summary.info_count;
            }
        }
        
        if (data.charts && data.charts.severity_distribution) {
            // Filter out 'Info' from severity distribution
            data.charts.severity_distribution = data.charts.severity_distribution.filter(
                item => item.name.toLowerCase() !== 'info'
            );
        }
        
        if (data.charts && data.charts.top_vulnerable_subdomains) {
            // Remove 'info' property from each subdomain entry
            data.charts.top_vulnerable_subdomains.forEach(subdomain => {
                if ('info' in subdomain) {
                    delete subdomain.info;
                }
            });
        }
        
        // Show dashboard content
        document.getElementById('dashboardContent').style.display = 'block';
        
        // Render all components
        renderExecutiveSummary(data);
        renderVisualizations(data);
        renderExportOptions(data);
        
        // Show first tab
        const summaryTab = document.getElementById('summary-tab');
        const summaryTabInstance = bootstrap.Tab.getInstance(summaryTab) || new bootstrap.Tab(summaryTab);
        summaryTabInstance.show();
    })
    .catch(error => {
        console.error('Error fetching report data:', error);
        console.error('Error message:', error.message);
        console.error('Error stack:', error.stack);
        
        document.getElementById('loadingIndicator').style.display = 'none';
        document.getElementById('initialState').style.display = 'block';
        
        alert(`Error fetching report data: ${error.message}. Please check the console for more details.`);
    });
}

// Initialize dashboard on document load
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM loaded - setting up event listeners');
    
    // Initialize Bootstrap Tab components
    const tabList = document.querySelectorAll('#reportTabs button');
    tabList.forEach(function(tabEl) {
        const tab = new bootstrap.Tab(tabEl);
        tabEl.addEventListener('click', function() {
            tab.show();
        });
    });
    
    // Initialize date range picker
    if ($.fn.daterangepicker) {
        $('#dateRange').daterangepicker({
            opens: 'left',
            autoUpdateInput: false,
            locale: {
                cancelLabel: 'Clear',
                format: 'YYYY-MM-DD'
            }
        });
        
        $('#dateRange').on('apply.daterangepicker', function(ev, picker) {
            $(this).val(picker.startDate.format('YYYY-MM-DD') + ' - ' + picker.endDate.format('YYYY-MM-DD'));
        });
        
        $('#dateRange').on('cancel.daterangepicker', function(ev, picker) {
            $(this).val('');
        });
    } else {
        console.warn('daterangepicker not found, using standard date input');
        // Fallback to standard date input if daterangepicker not available
        const dateRange = document.getElementById('dateRange');
        if (dateRange) {
            dateRange.type = 'text';
            dateRange.placeholder = 'YYYY-MM-DD - YYYY-MM-DD';
        }
    }
    
    // Generate Dashboard button click handler
    const generateButton = document.getElementById('generateDashboard');
    if (generateButton) {
        console.log('Found generate button, attaching event listener');
        generateButton.addEventListener('click', function() {
            console.log('Generate button clicked');
            fetchReportData();
        });
    } else {
        console.error('Generate Dashboard button not found');
    }
});