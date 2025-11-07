// Auto-play the animation when the page loads
window.addEventListener('load', function() {
  setTimeout(function() {
    const playButton = document.querySelector('.modebar-btn[data-title="Play"]');
    if (playButton) {
      playButton.click();
    }
  }, 500);
});

// Lazy load content sections with fade-in effect when scrolled into view
const contentSections = document.querySelectorAll('#content-section-left, #content-section-right');

if (contentSections.length > 0) {
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

  // Initially hide the content and start observing each section
  contentSections.forEach(section => {
    section.style.opacity = '0';
    section.style.transform = 'translateY(30px)';
    observer.observe(section);
  });
}

// Scroll-triggered animations for fadeInUp elements
const animatedElements = document.querySelectorAll('.fadeInUp-animation, .fadeInUp-animation2, .fadeInUpLowOpacity2, .fadeInUpLowOpacity3, .fadeInUpLowOpacity4');

const animationObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      if (entry.target.classList.contains('fadeInUpLowOpacity2')) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, 200); //0.2s delay
      } else if (entry.target.classList.contains('fadeInUpLowOpacity3')) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, 500); // 0.5s delay
      } else if (entry.target.classList.contains('fadeInUpLowOpacity4')) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, 900); // 0.9s delay
      } else {
        entry.target.classList.add('visible');
      }
      // Stop observing after animation triggers once
      animationObserver.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.0, // Trigger when 10% of the element is visible
  rootMargin: '0px 0px -30px 0px' // Start animation slightly before element comes into view
});

// Observe all animated elements
animatedElements.forEach(element => {
  animationObserver.observe(element);
});

// Example using a placeholder array for demonstration
const stockData = [
  { symbol: "▲ AAPL", change: "+0.5%" },
  { symbol: "▼ GOOGL", change: "-1.2%" },
  { symbol: "▲ MSFT", change: "+0.8%" },
  { symbol: "▲ AMZN", change: "+2.1%" },
  { symbol: "▼ TSLA", change: "-0.4%" },
  { symbol: "▲ NFLX", change: "+1.5%" },
  { symbol: "▼ FB", change: "-0.9%" },
  { symbol: "▲ NVDA", change: "+3.0%" },
  { symbol: "▼ BABA", change: "-1.5%" },
  { symbol: "▲ JPM", change: "+0.7%" },
  { symbol: "▼ V", change: "-0.3%" },
  { symbol: "▲ DIS", change: "+1.0%" },
  { symbol: "▼ MA", change: "-0.6%" },
  { symbol: "▲ PYPL", change: "+2.4%" },
  { symbol: "▼ INTC", change: "-1.1%" }
];

// Initialize stock ticker immediately when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
  const stockTicker = document.querySelector('.stock-ticker');

  if (stockTicker) {
    // Create the stock items twice for seamless infinite scroll
    for (let i = 0; i < 2; i++) {
      stockData.forEach(stock => {
        const span = document.createElement('span');
        span.textContent = `${stock.symbol} ${stock.change}`;
        stockTicker.appendChild(span);
      });
    }

    // Calculate the width of one set of items for proper animation
    // We need to wait for the next frame to ensure the DOM has rendered
    requestAnimationFrame(() => {
      const tickerWidth = stockTicker.scrollWidth;
      const halfWidth = tickerWidth / 2;

      // Create a dynamic keyframe animation with the exact pixel distance
      const styleSheet = document.styleSheets[0];
      const keyframes = `
        @keyframes scroll-left-dynamic {
          0% { transform: translateX(0px); }
          100% { transform: translateX(-${halfWidth}px); }
        }
      `;

      // Remove old animation and add the new one
      styleSheet.insertRule(keyframes, styleSheet.cssRules.length);
      stockTicker.style.animation = 'scroll-left-dynamic 39s linear infinite';
    });
  }
});
