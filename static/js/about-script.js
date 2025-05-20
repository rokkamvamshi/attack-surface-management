// Delays animation until element is in view
const elements = document.querySelectorAll('.fade-in, .slide-up, .zoom-in');

const observer = new IntersectionObserver(entries => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.classList.add('animate');
            observer.unobserve(entry.target);
        }
    });
}, {
    threshold: 0.1,
});

elements.forEach(element => observer.observe(element));

