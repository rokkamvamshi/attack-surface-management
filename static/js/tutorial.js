/**
 * Interactive Tutorial System
 * 
 * This script creates step-by-step interactive tutorials for the ASM platform
 * It guides users through common workflows with tooltips and highlights
 */

class InteractiveTutorial {
    constructor(options = {}) {
        this.options = Object.assign({
            tutorialId: null,
            steps: [],
            onComplete: () => {},
            highlightClass: 'tutorial-highlight',
            zIndex: 9999,
            primaryColor: '#4361ee',
            textColor: '#ffffff',
        }, options);

        this.currentStep = 0;
        this.popover = null;
        this.overlay = null;
        this.highlight = null;
        this.isActive = false;
        
        // Initialize tutorial if an ID is provided
        if (this.options.tutorialId) {
            this.initTutorial(this.options.tutorialId);
        }
    }

    /**
     * Initialize a tutorial by ID
     * @param {string} tutorialId - The ID of the tutorial to load
     */
    initTutorial(tutorialId) {
        // Find tutorial by ID
        const tutorial = this.getTutorialByID(tutorialId);
        
        if (!tutorial) {
            console.error(`Tutorial with ID '${tutorialId}' not found`);
            return;
        }
        
        // Set tutorial steps and start
        this.options.steps = tutorial.steps;
        this.options.tutorialId = tutorialId;
        this.options.title = tutorial.title;
        
        // Create overlay and start tutorial
        this.createElements();
        this.start();
    }
    
    /**
     * Create necessary DOM elements for the tutorial
     */
    createElements() {
        // Create overlay
        this.overlay = document.createElement('div');
        this.overlay.className = 'tutorial-overlay';
        this.overlay.style.position = 'fixed';
        this.overlay.style.top = '0';
        this.overlay.style.left = '0';
        this.overlay.style.width = '100%';
        this.overlay.style.height = '100%';
        this.overlay.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
        this.overlay.style.zIndex = (this.options.zIndex - 1).toString();
        this.overlay.style.display = 'none';
        
        // Create highlight element
        this.highlight = document.createElement('div');
        this.highlight.className = this.options.highlightClass;
        this.highlight.style.position = 'absolute';
        this.highlight.style.boxShadow = '0 0 0 9999px rgba(0, 0, 0, 0.7)';
        this.highlight.style.borderRadius = '4px';
        this.highlight.style.zIndex = this.options.zIndex.toString();
        this.highlight.style.pointerEvents = 'none';
        this.highlight.style.display = 'none';
        
        // Create popover
        this.popover = document.createElement('div');
        this.popover.className = 'tutorial-popover';
        this.popover.style.position = 'absolute';
        this.popover.style.zIndex = (this.options.zIndex + 1).toString();
        this.popover.style.backgroundColor = 'white';
        this.popover.style.borderRadius = '8px';
        this.popover.style.boxShadow = '0 5px 15px rgba(0, 0, 0, 0.15)';
        this.popover.style.padding = '20px';
        this.popover.style.width = '300px';
        this.popover.style.display = 'none';
        
        // Add elements to the DOM
        document.body.appendChild(this.overlay);
        document.body.appendChild(this.highlight);
        document.body.appendChild(this.popover);
    }
    
    /**
     * Start the tutorial
     */
    start() {
        if (this.options.steps.length === 0) {
            console.error('No tutorial steps defined');
            return;
        }
        
        this.isActive = true;
        this.currentStep = 0;
        
        // Show intro dialog
        this.showIntroDialog();
    }
    
    /**
     * Show the intro dialog
     */
    showIntroDialog() {
        // Create intro dialog
        const introDialog = document.createElement('div');
        introDialog.className = 'tutorial-intro-dialog';
        introDialog.style.position = 'fixed';
        introDialog.style.top = '50%';
        introDialog.style.left = '50%';
        introDialog.style.transform = 'translate(-50%, -50%)';
        introDialog.style.backgroundColor = 'white';
        introDialog.style.borderRadius = '16px';
        introDialog.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
        introDialog.style.padding = '30px';
        introDialog.style.maxWidth = '500px';
        introDialog.style.width = '90%';
        introDialog.style.zIndex = (this.options.zIndex + 2).toString();
        introDialog.style.textAlign = 'center';
        
        // Add content
        introDialog.innerHTML = `
            <div style="font-size: 3rem; color: ${this.options.primaryColor}; margin-bottom: 20px;">
                <i class="fas fa-graduation-cap"></i>
            </div>
            <h2 style="margin-bottom: 15px; color: #212529;">${this.options.title}</h2>
            <p style="margin-bottom: 25px; color: #6c757d;">This tutorial will guide you through the process step by step. Ready to begin?</p>
            <div style="display: flex; justify-content: center; gap: 15px;">
                <button id="tutorial-start-btn" style="background: linear-gradient(to right, ${this.options.primaryColor}, #3f37c9); color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; cursor: pointer;">Start Tutorial</button>
                <button id="tutorial-cancel-btn" style="background: none; border: 1px solid #ced4da; border-radius: 8px; padding: 10px 20px; cursor: pointer;">Cancel</button>
            </div>
        `;
        
        // Add to DOM
        document.body.appendChild(introDialog);
        
        // Add event listeners
        document.getElementById('tutorial-start-btn').addEventListener('click', () => {
            document.body.removeChild(introDialog);
            this.overlay.style.display = 'block';
            this.showStep(this.currentStep);
        });
        
        document.getElementById('tutorial-cancel-btn').addEventListener('click', () => {
            document.body.removeChild(introDialog);
            this.end();
        });
    }
    
    /**
     * Show a specific tutorial step
     * @param {number} stepIndex - The index of the step to show
     */
    showStep(stepIndex) {
        if (stepIndex >= this.options.steps.length) {
            this.complete();
            return;
        }
        
        const step = this.options.steps[stepIndex];
        const targetEl = document.querySelector(step.selector);
        
        if (!targetEl) {
            console.error(`Element with selector '${step.selector}' not found`);
            this.nextStep();
            return;
        }
        
        // Position highlight over the target element
        const targetRect = targetEl.getBoundingClientRect();
        const padding = step.padding || 5;
        
        this.highlight.style.display = 'block';
        this.highlight.style.top = (targetRect.top - padding + window.scrollY) + 'px';
        this.highlight.style.left = (targetRect.left - padding + window.scrollX) + 'px';
        this.highlight.style.width = (targetRect.width + padding * 2) + 'px';
        this.highlight.style.height = (targetRect.height + padding * 2) + 'px';
        
        // Position popover
        const popoverContent = `
            <div class="tutorial-step-count" style="color: ${this.options.primaryColor}; margin-bottom: 10px; font-size: 0.9rem; font-weight: 600;">
                Step ${stepIndex + 1} of ${this.options.steps.length}
            </div>
            <h4 style="margin-top: 0; margin-bottom: 10px; color: #212529;">${step.title}</h4>
            <p style="margin-bottom: 20px; color: #6c757d;">${step.content}</p>
            <div class="tutorial-buttons" style="display: flex; justify-content: space-between;">
                ${stepIndex > 0 ? `<button class="tutorial-prev-btn" style="background: none; border: 1px solid #ced4da; border-radius: 8px; padding: 7px 15px; cursor: pointer;">Previous</button>` : `<div></div>`}
                <button class="tutorial-next-btn" style="background: ${this.options.primaryColor}; color: white; border: none; border-radius: 8px; padding: 7px 15px; font-weight: 600; cursor: pointer;">
                    ${stepIndex === this.options.steps.length - 1 ? 'Finish' : 'Next'}
                </button>
            </div>
        `;
        
        this.popover.innerHTML = popoverContent;
        this.popover.style.display = 'block';
        
        // Calculate the popover position based on the target element's position
        this.positionPopover(targetRect, step.position || 'bottom');
        
        // Add event listeners to buttons
        const nextBtn = this.popover.querySelector('.tutorial-next-btn');
        if (nextBtn) {
            nextBtn.addEventListener('click', () => this.nextStep());
        }
        
        const prevBtn = this.popover.querySelector('.tutorial-prev-btn');
        if (prevBtn) {
            prevBtn.addEventListener('click', () => this.prevStep());
        }
        
        // Add click event to the target if it's a button and clickable is true
        if (step.clickable && (targetEl.tagName === 'BUTTON' || targetEl.tagName === 'A' || targetEl.type === 'submit')) {
            // Add a special highlight effect
            targetEl.style.position = 'relative';
            targetEl.style.zIndex = this.options.zIndex.toString();
            targetEl.style.animation = 'tutorial-pulse 1.5s infinite';
            
            // Create and add a style for the animation if it doesn't exist
            if (!document.getElementById('tutorial-animation-style')) {
                const style = document.createElement('style');
                style.id = 'tutorial-animation-style';
                style.innerHTML = `
                    @keyframes tutorial-pulse {
                        0% { box-shadow: 0 0 0 0 rgba(67, 97, 238, 0.4); }
                        70% { box-shadow: 0 0 0 10px rgba(67, 97, 238, 0); }
                        100% { box-shadow: 0 0 0 0 rgba(67, 97, 238, 0); }
                    }
                `;
                document.head.appendChild(style);
            }
            
            // Auto-advance to next step if target is clicked
            targetEl.addEventListener('click', () => {
                // Slight delay to allow for any UI updates
                setTimeout(() => this.nextStep(), 500);
            }, { once: true });
        }
        
        // Scroll to the element if needed
        if (step.scroll !== false) {
            targetEl.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
    }
    
    /**
     * Position the popover relative to the target element
     * @param {DOMRect} targetRect - The target element's bounding rectangle
     * @param {string} position - Where to position the popover (top, right, bottom, left)
     */
    positionPopover(targetRect, position) {
        const popoverRect = this.popover.getBoundingClientRect();
        const spacing = 15; // Space between target and popover
        
        let top, left;
        
        switch (position) {
            case 'top':
                top = targetRect.top - popoverRect.height - spacing + window.scrollY;
                left = targetRect.left + (targetRect.width - popoverRect.width) / 2 + window.scrollX;
                break;
            case 'right':
                top = targetRect.top + (targetRect.height - popoverRect.height) / 2 + window.scrollY;
                left = targetRect.right + spacing + window.scrollX;
                break;
            case 'left':
                top = targetRect.top + (targetRect.height - popoverRect.height) / 2 + window.scrollY;
                left = targetRect.left - popoverRect.width - spacing + window.scrollX;
                break;
            case 'bottom':
            default:
                top = targetRect.bottom + spacing + window.scrollY;
                left = targetRect.left + (targetRect.width - popoverRect.width) / 2 + window.scrollX;
                break;
        }
        
        // Ensure the popover stays within the viewport
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;
        
        if (left < 10) left = 10;
        if (left + popoverRect.width > viewportWidth - 10) left = viewportWidth - popoverRect.width - 10;
        
        if (top < 10) top = 10;
        if (top + popoverRect.height > viewportHeight + window.scrollY - 10) {
            // If it would go off the bottom, try placing it above instead
            top = targetRect.top - popoverRect.height - spacing + window.scrollY;
            
            // If it would still go off the screen, just place it at the top of the viewport
            if (top < 10) top = 10;
        }
        
        this.popover.style.top = top + 'px';
        this.popover.style.left = left + 'px';
    }
    
    /**
     * Move to the next step
     */
    nextStep() {
        // Reset any click animations
        if (this.currentStep < this.options.steps.length) {
            const currentSelector = this.options.steps[this.currentStep].selector;
            const currentEl = document.querySelector(currentSelector);
            if (currentEl) {
                currentEl.style.animation = '';
                currentEl.style.zIndex = '';
            }
        }
        
        this.currentStep++;
        if (this.currentStep < this.options.steps.length) {
            this.showStep(this.currentStep);
        } else {
            this.complete();
        }
    }
    
    /**
     * Move to the previous step
     */
    prevStep() {
        // Reset any click animations
        if (this.currentStep < this.options.steps.length) {
            const currentSelector = this.options.steps[this.currentStep].selector;
            const currentEl = document.querySelector(currentSelector);
            if (currentEl) {
                currentEl.style.animation = '';
                currentEl.style.zIndex = '';
            }
        }
        
        this.currentStep--;
        if (this.currentStep >= 0) {
            this.showStep(this.currentStep);
        } else {
            this.currentStep = 0;
            this.showStep(this.currentStep);
        }
    }
    
    /**
     * Complete the tutorial
     */
    complete() {
        // Show completion dialog
        const completionDialog = document.createElement('div');
        completionDialog.className = 'tutorial-completion-dialog';
        completionDialog.style.position = 'fixed';
        completionDialog.style.top = '50%';
        completionDialog.style.left = '50%';
        completionDialog.style.transform = 'translate(-50%, -50%)';
        completionDialog.style.backgroundColor = 'white';
        completionDialog.style.borderRadius = '16px';
        completionDialog.style.boxShadow = '0 10px 30px rgba(0, 0, 0, 0.2)';
        completionDialog.style.padding = '30px';
        completionDialog.style.maxWidth = '500px';
        completionDialog.style.width = '90%';
        completionDialog.style.zIndex = (this.options.zIndex + 2).toString();
        completionDialog.style.textAlign = 'center';
        
        completionDialog.innerHTML = `
            <div style="font-size: 3rem; color: #4cc9f0; margin-bottom: 20px;">
                <i class="fas fa-check-circle"></i>
            </div>
            <h2 style="margin-bottom: 15px; color: #212529;">Tutorial Complete!</h2>
            <p style="margin-bottom: 25px; color: #6c757d;">You've successfully completed the ${this.options.title} tutorial.</p>
            <button id="tutorial-finish-btn" style="background: linear-gradient(to right, ${this.options.primaryColor}, #3f37c9); color: white; border: none; border-radius: 8px; padding: 10px 20px; font-weight: 600; cursor: pointer;">Got it!</button>
        `;
        
        // Add completion dialog to DOM
        document.body.appendChild(completionDialog);
        
        // Hide other tutorial elements
        this.highlight.style.display = 'none';
        this.popover.style.display = 'none';
        this.overlay.style.display = 'block';
        
        // Add event listener to finish button
        document.getElementById('tutorial-finish-btn').addEventListener('click', () => {
            document.body.removeChild(completionDialog);
            this.end();
        });
        
        // Run onComplete callback if defined
        if (typeof this.options.onComplete === 'function') {
            this.options.onComplete();
        }
        
        // Mark tutorial as completed in local storage
        if (this.options.tutorialId) {
            const completedTutorials = JSON.parse(localStorage.getItem('completedTutorials') || '[]');
            if (!completedTutorials.includes(this.options.tutorialId)) {
                completedTutorials.push(this.options.tutorialId);
                localStorage.setItem('completedTutorials', JSON.stringify(completedTutorials));
            }
        }
    }
    
    /**
     * End the tutorial and clean up
     */
    end() {
        // Reset any animations
        if (this.currentStep < this.options.steps.length) {
            const currentSelector = this.options.steps[this.currentStep]?.selector;
            if (currentSelector) {
                const currentEl = document.querySelector(currentSelector);
                if (currentEl) {
                    currentEl.style.animation = '';
                    currentEl.style.zIndex = '';
                }
            }
        }
        
        // Hide tutorial elements
        this.highlight.style.display = 'none';
        this.popover.style.display = 'none';
        this.overlay.style.display = 'none';
        this.isActive = false;
    }
    
    /**
     * Get a tutorial by ID
     * @param {string} id - The tutorial ID
     * @returns {object|null} The tutorial object or null if not found
     */
    getTutorialByID(id) {
        // Define available tutorials
        const tutorials = {
            'subdomain-discovery': {
                title: 'Subdomain Discovery Tutorial',
                steps: [
                    {
                        selector: '.navbar-brand',
                        title: 'Welcome to Subdomain Discovery',
                        content: 'This tutorial will guide you through discovering subdomains for a target domain.',
                        position: 'bottom'
                    },
                    {
                        selector: 'input[name="domain"]',
                        title: 'Enter a Domain',
                        content: 'Start by entering a domain you want to scan (e.g., example.com).',
                        position: 'bottom',
                        clickable: true
                    },
                    {
                        selector: 'button[type="submit"]',
                        title: 'Start the Scan',
                        content: 'Click the "Scan Now" button to begin discovering subdomains.',
                        position: 'bottom',
                        clickable: true
                    },
                    {
                        selector: '.list-group',
                        title: 'View Results',
                        content: 'After scanning completes, you\'ll see all discovered subdomains here.',
                        position: 'top'
                    },
                    {
                        selector: 'a[href="/scan"]',
                        title: 'Next Steps',
                        content: 'After finding subdomains, you can click here to scan them for vulnerabilities.',
                        position: 'bottom'
                    }
                ]
            },
            'vulnerability-scan': {
                title: 'Vulnerability Scanning Tutorial',
                steps: [
                    {
                        selector: '.navbar-brand',
                        title: 'Vulnerability Scanning',
                        content: 'Now you\'ll learn how to scan subdomains for security vulnerabilities.',
                        position: 'bottom'
                    },
                    {
                        selector: '#domain',
                        title: 'Select a Domain',
                        content: 'First, choose a domain from the dropdown menu.',
                        position: 'bottom',
                        clickable: true
                    },
                    {
                        selector: '#subdomain',
                        title: 'Select a Subdomain',
                        content: 'Next, select a specific subdomain to scan.',
                        position: 'bottom',
                        clickable: true
                    },
                    {
                        selector: '#bug_class',
                        title: 'Choose Vulnerability Types',
                        content: 'Select which types of vulnerabilities you want to scan for.',
                        position: 'right',
                        clickable: true
                    },
                    {
                        selector: '#scanBtn',
                        title: 'Start the Scan',
                        content: 'Click the "Start Scan" button to begin vulnerability scanning.',
                        position: 'top',
                        clickable: true
                    },
                    {
                        selector: 'a[href="/dashboard"]',
                        title: 'View Results',
                        content: 'After the scan completes, visit the Dashboard to see your results.',
                        position: 'bottom'
                    }
                ]
            },
            'dashboard-tutorial': {
                title: 'Dashboard Tutorial',
                steps: [
                    {
                        selector: '.navbar-brand',
                        title: 'Security Dashboard',
                        content: 'This dashboard gives you a complete overview of your security findings.',
                        position: 'bottom'
                    },
                    {
                        selector: '.stat-card:nth-child(1)',
                        title: 'Total Scans',
                        content: 'This shows the total number of scans you\'ve performed.',
                        position: 'bottom'
                    },
                    {
                        selector: '.stat-card:nth-child(2)',
                        title: 'Total Findings',
                        content: 'This shows the total number of vulnerabilities discovered.',
                        position: 'bottom'
                    },
                    {
                        selector: '.stat-card:nth-child(3)',
                        title: 'Critical Issues',
                        content: 'This shows high-priority vulnerabilities that need immediate attention.',
                        position: 'bottom'
                    },
                    {
                        selector: '.severity-summary',
                        title: 'Severity Distribution',
                        content: 'This shows a breakdown of vulnerabilities by severity level.',
                        position: 'bottom'
                    },
                    {
                        selector: '#severityChart',
                        title: 'Chart Visualization',
                        content: 'This chart provides a visual representation of your vulnerability distribution.',
                        position: 'right'
                    },
                    {
                        selector: '#domainSelect',
                        title: 'Filter Results',
                        content: 'You can filter results by domain to focus on specific assets.',
                        position: 'bottom',
                        clickable: true
                    },
                    {
                        selector: '.table',
                        title: 'Vulnerability List',
                        content: 'This table shows detailed information about each vulnerability found.',
                        position: 'top'
                    },
                    {
                        selector: '.btn-view:first-child',
                        title: 'View Details',
                        content: 'Click to see detailed information about a specific vulnerability.',
                        position: 'left',
                        clickable: true
                    }
                ]
            }
        };
        
        return tutorials[id] || null;
    }
    
    /**
     * Check if a tutorial has been completed
     * @param {string} tutorialId - The ID of the tutorial to check
     * @returns {boolean} Whether the tutorial has been completed
     */
    static isTutorialCompleted(tutorialId) {
        const completedTutorials = JSON.parse(localStorage.getItem('completedTutorials') || '[]');
        return completedTutorials.includes(tutorialId);
    }
    
    /**
     * Check if any tutorial is currently active
     * @returns {boolean} Whether a tutorial is active
     */
    static isAnyTutorialActive() {
        return document.querySelector('.tutorial-overlay') !== null &&
               document.querySelector('.tutorial-overlay').style.display !== 'none';
    }
}

// Add to window
window.InteractiveTutorial = InteractiveTutorial;

// Helper function to start a tutorial
function startTutorial(tutorialId) {
    if (InteractiveTutorial.isAnyTutorialActive()) {
        console.warn('A tutorial is already active');
        return;
    }
    
    if (InteractiveTutorial.isTutorialCompleted(tutorialId)) {
        // Ask if they want to see it again
        if (!confirm('You\'ve already completed this tutorial. Would you like to see it again?')) {
            return;
        }
    }
    
    new InteractiveTutorial({
        tutorialId: tutorialId
    });
}

// Add tutorial buttons to appropriate pages
document.addEventListener('DOMContentLoaded', function() {
    // Detect current page
    const path = window.location.pathname;
    let tutorialId = null;
    
    // Match page to tutorial
    if (path === '/view' || path === '/') {
        tutorialId = 'subdomain-discovery';
    } else if (path === '/scan') {
        tutorialId = 'vulnerability-scan';
    } else if (path === '/dashboard') {
        tutorialId = 'dashboard-tutorial';
    }
    
    // Add tutorial button if we have a relevant tutorial
    if (tutorialId) {
        const tutorialButton = document.createElement('button');
        tutorialButton.className = 'tutorial-button';
        tutorialButton.innerHTML = '<i class="fas fa-info-circle"></i> Tutorial';
        tutorialButton.style.position = 'fixed';
        tutorialButton.style.bottom = '80px';
        tutorialButton.style.right = '20px';
        tutorialButton.style.backgroundColor = '#4361ee';
        tutorialButton.style.color = 'white';
        tutorialButton.style.border = 'none';
        tutorialButton.style.borderRadius = '50px';
        tutorialButton.style.padding = '8px 15px';
        tutorialButton.style.boxShadow = '0 4px 6px rgba(0, 0, 0, 0.1)';
        tutorialButton.style.zIndex = '999';
        tutorialButton.style.cursor = 'pointer';
        
        // Add completed badge if tutorial is already completed
        if (InteractiveTutorial.isTutorialCompleted(tutorialId)) {
            const badge = document.createElement('span');
            badge.innerHTML = '<i class="fas fa-check"></i>';
            badge.style.position = 'absolute';
            badge.style.top = '-5px';
            badge.style.right = '-5px';
            badge.style.backgroundColor = '#4cc9f0';
            badge.style.color = 'white';
            badge.style.width = '18px';
            badge.style.height = '18px';
            badge.style.borderRadius = '50%';
            badge.style.display = 'flex';
            badge.style.alignItems = 'center';
            badge.style.justifyContent = 'center';
            badge.style.fontSize = '10px';
            
            tutorialButton.style.position = 'relative';
            tutorialButton.appendChild(badge);
        }
        
        // Add event listener
        tutorialButton.addEventListener('click', function() {
            startTutorial(tutorialId);
        });
        
        // Add to DOM
        document.body.appendChild(tutorialButton);
        
        // Show tutorial automatically for new users (who haven't completed any tutorials)
        const completedTutorials = JSON.parse(localStorage.getItem('completedTutorials') || '[]');
        if (completedTutorials.length === 0 && !InteractiveTutorial.isAnyTutorialActive()) {
            // Wait a bit for page to fully load
            setTimeout(() => {
                startTutorial(tutorialId);
            }, 1500);
        }
    }
});

