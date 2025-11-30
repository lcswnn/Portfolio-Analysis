// Check regeneration status as early as possible
function checkRegenerationStatusEarly() {
    const isRegenerating = localStorage.getItem('isRegeneratingStockData');
    if (isRegenerating === 'true') {
        const startTime = parseInt(localStorage.getItem('regenerationStartTime'));
        const now = Date.now();
        const elapsedMs = now - startTime;

        // If more than 100 minutes have passed, assume the process is dead and clear the state
        if (elapsedMs > 100 * 60 * 1000) {
            localStorage.removeItem('isRegeneratingStockData');
            localStorage.removeItem('regenerationStartTime');
            return;
        }

        const regenerateBtn = document.getElementById('regenerate-btn');
        const regenerateBtnText = document.getElementById('regenerate-btn-text');
        const regenerateSpinner = document.getElementById('regenerate-spinner');

        if (regenerateBtn && regenerateBtnText && regenerateSpinner) {
            regenerateBtn.disabled = true;
            regenerateSpinner.style.display = 'inline-block';

            const elapsedMinutes = Math.floor(elapsedMs / 60000);
            regenerateBtnText.textContent = `Processing... (${elapsedMinutes} min elapsed)`;

            // Verify the task is actually still running on the backend
            verifyRegenerationTaskRunning();
        }
    }
}

// Verify that the regeneration task is actually running on the backend
function verifyRegenerationTaskRunning() {
    fetch('/api/regeneration-status')
        .then(response => response.json())
        .then(data => {
            if (!data.is_running) {
                // Task is not actually running, clear localStorage
                localStorage.removeItem('isRegeneratingStockData');
                localStorage.removeItem('regenerationStartTime');

                // Reset button UI
                const regenerateBtn = document.getElementById('regenerate-btn');
                const regenerateBtnText = document.getElementById('regenerate-btn-text');
                const regenerateSpinner = document.getElementById('regenerate-spinner');

                if (regenerateBtn && regenerateBtnText && regenerateSpinner) {
                    regenerateBtn.disabled = false;
                    regenerateBtnText.textContent = 'Regenerate Stock Data';
                    regenerateSpinner.style.display = 'none';
                }
            }
        })
        .catch(() => {
            // If the API call fails, assume the task might still be running
            // (server might be temporarily unavailable)
        });
}

// Try to check status immediately (elements may not exist yet, that's ok)
checkRegenerationStatusEarly();

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
  const format = element.getAttribute('data-format') || 'percent'; // Default to percent for backward compatibility

  const updateCounter = () => {
    const currentTime = Date.now();
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const currentValue = startValue + (targetValue - startValue) * progress;

    // Format based on data-format attribute
    if (format === 'percent') {
      element.textContent = currentValue.toFixed(1) + '%';
    } else if (format === 'number') {
      element.textContent = Math.round(currentValue);
    }

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
const counterContainers = document.querySelectorAll('[id*="port-health"], .port-stats-example, .stats-grid');
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

// Handle delete file button clicks
document.addEventListener('DOMContentLoaded', function() {
    const deleteButtons = document.querySelectorAll('.delete-file-btn');

    deleteButtons.forEach(button => {
        button.addEventListener('click', function() {
            const fileId = this.getAttribute('data-file-id');
            if (confirm('Are you sure you want to delete this file?')) {
                deleteFile(fileId);
            }
        });
    });
});

function deleteFile(fileId) {
    fetch(`/delete-file/${fileId}`, {
        method: 'DELETE'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Reload the page to refresh the graphs with updated data
            setTimeout(() => {
                location.reload();
            }, 500);
        } else {
            alert(`Error deleting file: ${data.message}`);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('Failed to delete file');
    });
}

// Refresh recommendations with latest data from stock_features.csv
function refreshRecommendations() {
    const refreshBtn = document.getElementById('refresh-btn');
    const refreshBtnText = document.getElementById('refresh-btn-text');
    const refreshSpinner = document.getElementById('refresh-spinner');
    const tableBody = document.querySelector('.recommendations-table tbody');

    // Disable button and show loading state
    refreshBtn.disabled = true;
    refreshBtnText.textContent = 'Updating...';
    refreshSpinner.style.display = 'inline-block';

    fetch('/api/refresh-recommendations', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Update the stats
            const stats = data.stats;

            // Update counter values (reset animation for smooth re-count)
            const counters = document.querySelectorAll('.counter');
            counters.forEach(counter => {
                counter.removeAttribute('data-animated');

                const statType = counter.getAttribute('data-stat');
                const newValue = stats[statType];
                counter.setAttribute('data-target', newValue);

                animateCounter(counter, parseFloat(newValue), 2000);
            });

            // Update the last updated date
            document.getElementById('last-updated-date').textContent = stats.last_updated;

            // Clear and rebuild the table with new recommendations
            tableBody.innerHTML = '';
            data.recommendations.forEach((stock, index) => {
                const row = document.createElement('tr');
                row.classList.add('fade-in-row');

                const positive = stock.momentum > 0 ? 'positive' : 'negative';
                const accelPositive = stock.momentum_accel > 0 ? 'positive' : 'negative';
                const highProb = stock.prob_beat_market > 0.55 ? 'high-prob' : '';

                row.innerHTML = `
                    <td>${index + 1}</td>
                    <td class="ticker">${stock.ticker}</td>
                    <td class="${highProb}">${(stock.prob_beat_market * 100).toFixed(1)}%</td>
                    <td>${stock.sharpe.toFixed(2)}</td>
                    <td class="${positive}">${(stock.momentum * 100).toFixed(1)}%</td>
                    <td class="${accelPositive}">${(stock.momentum_accel * 100).toFixed(1)}%</td>
                    <td>${(stock.volatility * 100).toFixed(1)}%</td>
                    <td>${(stock.dividend_yield * 100).toFixed(2)}%</td>
                    <td>${(stock.avg_correlation * 100).toFixed(1)}%</td>
                    <td>${(stock.market_correlation * 100).toFixed(1)}%</td>
                `;
                tableBody.appendChild(row);
            });

            // Re-enable button and hide loading state
            refreshBtn.disabled = false;
            refreshBtnText.textContent = 'Refresh Data';
            refreshSpinner.style.display = 'none';

            // Show success message
            showNotification('Recommendations updated successfully!', 'success');
        } else {
            throw new Error(data.error || 'Unknown error occurred');
        }
    })
    .catch(error => {
        console.error('Error:', error);

        // Re-enable button and hide loading state
        refreshBtn.disabled = false;
        refreshBtnText.textContent = 'Refresh Data';
        refreshSpinner.style.display = 'none';

        showNotification('Failed to refresh recommendations: ' + error.message, 'error');
    });
}

// Regenerate stock_features.csv from fresh yfinance data
function regenerateStockData() {
    const regenerateBtn = document.getElementById('regenerate-btn');
    const regenerateBtnText = document.getElementById('regenerate-btn-text');
    const regenerateSpinner = document.getElementById('regenerate-spinner');

    // Disable button and show loading state
    regenerateBtn.disabled = true;
    regenerateBtnText.textContent = 'Starting...';
    regenerateSpinner.style.display = 'inline-block';

    // Save regeneration state to localStorage
    localStorage.setItem('isRegeneratingStockData', 'true');
    localStorage.setItem('regenerationStartTime', Date.now().toString());

    fetch('/api/regenerate-stock-data', {
        method: 'POST'
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            regenerateBtnText.textContent = 'Processing... (10-20 min)';
            showNotification(data.message, 'info');

            // Poll for completion every 30 seconds and refresh recommendations when done
            let pollCount = 0;
            const maxPolls = 200; // ~100 minutes max
            const pollInterval = setInterval(() => {
                pollCount++;

                // Update status text with elapsed time estimate
                const elapsedMinutes = Math.floor((pollCount * 30) / 60);
                regenerateBtnText.textContent = `Processing... (${elapsedMinutes} min elapsed)`;

                // Check if we can load the new data by trying to refresh
                fetch('/api/refresh-recommendations', { method: 'POST' })
                    .then(response => response.json())
                    .then(pollData => {
                        if (pollData.success) {
                            // Data regeneration likely complete, show success
                            regenerateBtnText.textContent = 'Finalizing...';
                            showNotification('Stock data regeneration complete! Recommendations updated.', 'success');
                            clearInterval(pollInterval);

                            // Update recommendations on page
                            updateRecommendationsFromData(pollData);

                            // Reset button after a short delay and clear localStorage
                            setTimeout(() => {
                                regenerateBtn.disabled = false;
                                regenerateBtnText.textContent = 'Regenerate Stock Data';
                                regenerateSpinner.style.display = 'none';
                                localStorage.removeItem('isRegeneratingStockData');
                                localStorage.removeItem('regenerationStartTime');
                            }, 1000);
                        }
                    })
                    .catch(() => {
                        // Still generating, continue polling
                        if (pollCount >= maxPolls) {
                            clearInterval(pollInterval);
                            regenerateBtn.disabled = false;
                            regenerateBtnText.textContent = 'Regenerate Stock Data';
                            regenerateSpinner.style.display = 'none';
                            localStorage.removeItem('isRegeneratingStockData');
                            localStorage.removeItem('regenerationStartTime');
                            showNotification('Stock data regeneration may still be running. Please refresh the page manually.', 'info');
                        }
                    });
            }, 30000); // Poll every 30 seconds

        } else {
            regenerateBtn.disabled = false;
            regenerateBtnText.textContent = 'Regenerate Stock Data';
            regenerateSpinner.style.display = 'none';
            localStorage.removeItem('isRegeneratingStockData');
            localStorage.removeItem('regenerationStartTime');

            showNotification('Failed to start regeneration: ' + data.error, 'error');
        }
    })
    .catch(error => {
        console.error('Error:', error);

        regenerateBtn.disabled = false;
        regenerateBtnText.textContent = 'Regenerate Stock Data';
        regenerateSpinner.style.display = 'none';
        localStorage.removeItem('isRegeneratingStockData');
        localStorage.removeItem('regenerationStartTime');

        showNotification('Failed to start data regeneration: ' + error.message, 'error');
    });
}


// Set up polling when DOM is ready (button state already set by checkRegenerationStatusEarly)
document.addEventListener('DOMContentLoaded', function() {
    const isRegenerating = localStorage.getItem('isRegeneratingStockData');
    if (isRegenerating === 'true') {
        const startTime = parseInt(localStorage.getItem('regenerationStartTime'));
        const now = Date.now();
        const elapsedMs = now - startTime;

        // If more than 100 minutes have passed, assume the process is dead and clear the state
        if (elapsedMs > 100 * 60 * 1000) {
            localStorage.removeItem('isRegeneratingStockData');
            localStorage.removeItem('regenerationStartTime');
            return;
        }

        const regenerateBtn = document.getElementById('regenerate-btn');
        const regenerateBtnText = document.getElementById('regenerate-btn-text');
        const regenerateSpinner = document.getElementById('regenerate-spinner');

        // Resume polling for completion
        let elapsedMinutes = Math.floor(elapsedMs / 60000);
        let pollCount = Math.floor(elapsedMs / 30000);
        const maxPolls = 200;

        const pollInterval = setInterval(() => {
            pollCount++;
            const totalElapsedMinutes = elapsedMinutes + Math.floor((pollCount * 30000) / 60000);
            regenerateBtnText.textContent = `Processing... (${totalElapsedMinutes} min elapsed)`;

            fetch('/api/refresh-recommendations', { method: 'POST' })
                .then(response => response.json())
                .then(pollData => {
                    if (pollData.success) {
                        regenerateBtnText.textContent = 'Finalizing...';
                        showNotification('Stock data regeneration complete! Recommendations updated.', 'success');
                        clearInterval(pollInterval);
                        updateRecommendationsFromData(pollData);

                        setTimeout(() => {
                            regenerateBtn.disabled = false;
                            regenerateBtnText.textContent = 'Regenerate Stock Data';
                            regenerateSpinner.style.display = 'none';
                            localStorage.removeItem('isRegeneratingStockData');
                            localStorage.removeItem('regenerationStartTime');
                        }, 1000);
                    }
                })
                .catch(() => {
                    if (pollCount >= maxPolls) {
                        clearInterval(pollInterval);
                        regenerateBtn.disabled = false;
                        regenerateBtnText.textContent = 'Regenerate Stock Data';
                        regenerateSpinner.style.display = 'none';
                        localStorage.removeItem('isRegeneratingStockData');
                        localStorage.removeItem('regenerationStartTime');
                        showNotification('Stock data regeneration may still be running. Please refresh the page manually.', 'info');
                    }
                });
        }, 30000);
    }
});

// Helper function to update recommendations on the page
function updateRecommendationsFromData(data) {
    if (!data.success) return;

    const { stats } = data;
    const tableBody = document.querySelector('.recommendations-table tbody');

    // Update counter values (reset animation for smooth re-count)
    const counters = document.querySelectorAll('.counter');
    counters.forEach(counter => {
        counter.removeAttribute('data-animated');

        const statType = counter.getAttribute('data-stat');
        const newValue = stats[statType];
        counter.setAttribute('data-target', newValue);

        animateCounter(counter, parseFloat(newValue), 2000);
    });

    // Update the last updated date
    document.getElementById('last-updated-date').textContent = stats.last_updated;

    // Clear and rebuild the table with new recommendations
    tableBody.innerHTML = '';
    data.recommendations.forEach((stock, index) => {
        const row = document.createElement('tr');
        row.classList.add('fade-in-row');

        const positive = stock.momentum > 0 ? 'positive' : 'negative';
        const accelPositive = stock.momentum_accel > 0 ? 'positive' : 'negative';
        const highProb = stock.prob_beat_market > 0.55 ? 'high-prob' : '';

        row.innerHTML = `
            <td>${index + 1}</td>
            <td class="ticker">${stock.ticker}</td>
            <td class="${highProb}">${(stock.prob_beat_market * 100).toFixed(1)}%</td>
            <td>${stock.sharpe.toFixed(2)}</td>
            <td class="${positive}">${(stock.momentum * 100).toFixed(1)}%</td>
            <td class="${accelPositive}">${(stock.momentum_accel * 100).toFixed(1)}%</td>
            <td>${(stock.volatility * 100).toFixed(1)}%</td>
            <td>${(stock.dividend_yield * 100).toFixed(2)}%</td>
            <td>${(stock.avg_correlation * 100).toFixed(1)}%</td>
            <td>${(stock.market_correlation * 100).toFixed(1)}%</td>
        `;
        tableBody.appendChild(row);
    });
}

// Show notification message
function showNotification(message, type = 'info') {
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.textContent = message;
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 15px 20px;
        border-radius: 5px;
        z-index: 10000;
        animation: slideIn 0.3s ease-out;
        max-width: 400px;
        word-wrap: break-word;
    `;

    // Style based on type
    if (type === 'success') {
        notification.style.backgroundColor = '#4caf50';
        notification.style.color = 'white';
    } else if (type === 'error') {
        notification.style.backgroundColor = '#f44336';
        notification.style.color = 'white';
    } else {
        notification.style.backgroundColor = '#2196F3';
        notification.style.color = 'white';
    }

    document.body.appendChild(notification);

    // Auto-remove after 5 seconds (longer for info messages)
    const duration = type === 'info' ? 5000 : 3000;
    setTimeout(() => {
        notification.style.animation = 'slideOut 0.3s ease-in';
        setTimeout(() => {
            notification.remove();
        }, 300);
    }, duration);
}
