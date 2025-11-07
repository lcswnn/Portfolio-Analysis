// Auto-play the animation when the page loads
window.addEventListener('load', function() {
  setTimeout(function() {
    const playButton = document.querySelector('.modebar-btn[data-title="Play"]');
    if (playButton) {
      playButton.click();
    }
  }, 500);
});
