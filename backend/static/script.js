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
    threshold: 0.12, // Trigger when 12% of the element is visible
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
        }, 150); //0.2s delay
      } else if (entry.target.classList.contains('fadeInUpLowOpacity3')) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, 430); // 0.5s delay
      } else if (entry.target.classList.contains('fadeInUpLowOpacity4')) {
        setTimeout(() => {
          entry.target.classList.add('visible');
        }, 810); // 0.9s delay
      } else {
        entry.target.classList.add('visible');
      }
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

// Early trigger observer for roadmap - triggers much sooner with positive rootMargin
const roadmapEarlyTrigger = document.querySelectorAll('.roadmap-early-trigger');
const earlyTriggerObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      entry.target.classList.add('visible');
      earlyTriggerObserver.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.0,
  rootMargin: '200px 0px 0px 0px' // Trigger when element is 200px below the viewport
});

// Observe roadmap elements
roadmapEarlyTrigger.forEach(element => {
  earlyTriggerObserver.observe(element);
});

// Counter animation for the portfolio health number using JavaScript
const animateCounter = (element, targetValue, duration = 3000) => {
  if (element.hasAttribute('data-animated')) return;

  element.setAttribute('data-animated', 'true');
  const startValue = 0;
  const startTime = Date.now();

  const updateCounter = () => {
    const currentTime = Date.now();
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const currentValue = startValue + (targetValue - startValue) * progress;

    // Update the text content directly
    element.textContent = currentValue.toFixed(1) + '%';

    if (progress < 1) {
      requestAnimationFrame(updateCounter);
    }
  };

  updateCounter();
};

// Observer for the parent container of counters (to detect when they come into view)
const counterParentObserver = new IntersectionObserver((entries) => {
  entries.forEach(entry => {
    if (entry.isIntersecting) {
      // Find all counter elements within this parent
      const counters = entry.target.querySelectorAll('.counter');
      counters.forEach(counter => {
        const targetValue = parseFloat(counter.getAttribute('data-target'));
        // Add a small delay to let the parent fade in first (150ms matches fadeInUpLowOpacity2 delay)
        setTimeout(() => {
          animateCounter(counter, targetValue, 3000);
        }, 150);
      });
      counterParentObserver.unobserve(entry.target);
    }
  });
}, {
  threshold: 0.0,
  rootMargin: '0px 0px -30px 0px'
});

// Observe parent containers that have counters
const counterContainers = document.querySelectorAll('[id*="port-health"], .port-stats-example');
counterContainers.forEach(container => {
  counterParentObserver.observe(container);
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


const dropZone = document.getElementById('drop-zone');
const fileInput = document.getElementById('file-input');
const fileList = document.getElementById('file-list');

// Prevent default drag behaviors
['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, preventDefaults, false);
    document.body.addEventListener(eventName, preventDefaults, false); // For global prevention
});

function preventDefaults(e) {
    e.preventDefault();
    e.stopPropagation();
}

// Highlight drop zone on dragenter/dragover
['dragenter', 'dragover'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.add('hover'), false);
});

// Remove highlight on dragleave/drop
['dragleave', 'drop'].forEach(eventName => {
    dropZone.addEventListener(eventName, () => dropZone.classList.remove('hover'), false);
});

// Handle dropped files
dropZone.addEventListener('drop', handleDrop, false);

function handleDrop(e) {
    const dt = e.dataTransfer;
    const {files} = dt;
    handleFiles(files);
}

// Handle file input selection
dropZone.addEventListener('click', () => fileInput.click());
fileInput.addEventListener('change', (e) => handleFiles(e.target.files));

function handleFiles(files) {
    for (const file of files) {
        uploadFile(file);
    }
}

function uploadFile(file) {
    const formData = new FormData();
    formData.append('file', file);

    fetch('/profile', { // Flask upload endpoint
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            const listItem = document.createElement('div');
            listItem.classList.add('file-item');
            listItem.textContent = `Uploaded: ${file.name}`;
            fileList.appendChild(listItem);
            // Reload the page to refresh the graph with new data
            setTimeout(() => {
                location.reload();
            }, 1000);
        } else {
            alert(`Error uploading ${file.name}: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert(`Failed to upload ${file.name}`);
    });
}
