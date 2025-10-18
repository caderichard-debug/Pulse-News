// Config - change to production URL when deploying
var FRONTEND_URL = 'http://localhost:3000'; // or 'https://pulsenews.app' for production

console.log('[Pulse Extension] Popup script loaded');

function showError(message, details) {
  console.error('[Pulse Extension] Error:', message, details);
  
  var loading = document.getElementById("loading");
  var error = document.getElementById("error");
  var errorMessage = document.getElementById("errorMessage");
  var errorDetails = document.getElementById("errorDetails");
  
  if (loading) loading.style.display = 'none';
  if (error) {
    error.style.display = 'flex';
    if (errorMessage) errorMessage.textContent = message;
    if (errorDetails && details) errorDetails.textContent = details;
  }
}

document.addEventListener("DOMContentLoaded", function () {
  console.log('[Pulse Extension] DOM loaded');
  
  var iframe = document.getElementById("analysisFrame");
  var loading = document.getElementById("loading");

  if (!iframe) {
    showError("Missing iframe element", "The popup HTML may be corrupted");
    return;
  }

  if (!loading) {
    showError("Missing loading element", "The popup HTML may be corrupted");
    return;
  }

  loading.style.display = 'flex';

  // Get current tab URL
  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    if (chrome.runtime.lastError) {
      showError(
        "Cannot access current tab", 
        chrome.runtime.lastError.message
      );
      return;
    }

    if (!tabs || !tabs[0]) {
      showError(
        "No active tab found",
        "Make sure you have a tab open"
      );
      return;
    }

    var currentUrl = tabs[0].url || '';
    console.log('[Pulse Extension] Current tab URL:', currentUrl);

    // Check if URL is valid (not a chrome:// or extension page)
    if (currentUrl.startsWith('chrome://') || currentUrl.startsWith('chrome-extension://')) {
      showError(
        "Cannot analyze this page",
        "Chrome internal pages cannot be analyzed. Please navigate to a news article."
      );
      return;
    }

    // Get saved URL from background
    chrome.runtime.sendMessage({ type: "getCurrentUrl" }, function (savedUrl) {
      if (chrome.runtime.lastError) {
        console.warn('[Pulse Extension] Background message error:', chrome.runtime.lastError);
        // Continue anyway with current URL
        savedUrl = '';
      }

      if (!savedUrl) savedUrl = '';

      // Update saved URL if different
      if (savedUrl !== currentUrl) {
        chrome.runtime.sendMessage({ type: "setCurrentUrl", url: currentUrl }, function(response) {
          if (chrome.runtime.lastError) {
            console.warn('[Pulse Extension] Failed to save URL:', chrome.runtime.lastError);
          }
        });
        savedUrl = currentUrl;
      }

      // Build iframe URL
      var iframeUrl = FRONTEND_URL + '/analyze?url=' + encodeURIComponent(savedUrl);
      console.log('[Pulse Extension] Loading iframe:', iframeUrl);

      // Set up iframe load handlers
      var loadTimeout = setTimeout(function() {
        showError(
          "Frontend took too long to load",
          "Make sure " + FRONTEND_URL + " is accessible. Check if your local dev server is running."
        );
      }, 15000); // 15 second timeout

      iframe.onload = function () {
        console.log('[Pulse Extension] Iframe loaded successfully');
        clearTimeout(loadTimeout);
        loading.style.display = 'none';
        iframe.classList.add('loaded');
      };

      iframe.onerror = function(e) {
        console.error('[Pulse Extension] Iframe error:', e);
        clearTimeout(loadTimeout);
        showError(
          "Failed to load Pulse frontend",
          "Cannot connect to " + FRONTEND_URL + ". Make sure the server is running."
        );
      };

      // Load the iframe
      try {
        iframe.src = iframeUrl;
      } catch (e) {
        clearTimeout(loadTimeout);
        showError(
          "Failed to set iframe URL",
          e.message
        );
      }
    });
  });
});
