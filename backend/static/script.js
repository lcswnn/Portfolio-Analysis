// Auto-play the animation when the page loads
window.addEventListener('load', function() {
  setTimeout(function() {
    const playButton = document.querySelector('.modebar-btn[data-title="Play"]');
    if (playButton) {
      playButton.click();
    }
  }, 500);
});

// Lazy load content section with fade-in effect when scrolled into view
const contentSection = document.getElementById('content-section');

if (contentSection) {
  // Initially hide the content
  contentSection.style.opacity = '0';
  contentSection.style.transform = 'translateY(30px)';

  // Create an Intersection Observer
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        // Add the fade-in class when element is visible
        entry.target.classList.add('fade-in-visible');
        // Optional: stop observing after animation triggers once
        observer.unobserve(entry.target);
      }
    });
  }, {
    threshold: 0.2, // Trigger when 20% of the element is visible
    rootMargin: '0px 0px -50px 0px' // Start slightly before it comes into view
  });

  // Start observing the content section
  observer.observe(contentSection);
}

// Scroll-triggered animations for fadeInUp elements
const animatedElements = document.querySelectorAll('.fadeInUp-animation, .fadeInUp-animation2');

const animationObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Add the 'visible' class to trigger animation
      entry.target.classList.add('visible');
      // Stop observing after animation triggers once
      animationObserver.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.1, // Trigger when 10% of the element is visible
  rootMargin: '0px 0px -30px 0px' // Start animation slightly before element comes into view
});

// Observe all animated elements
animatedElements.forEach(element => {
  animationObserver.observe(element);
});
