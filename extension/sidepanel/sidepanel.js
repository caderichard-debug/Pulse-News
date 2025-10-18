// Config - change to production URL when deploying
//var FRONTEND_URL = 'http://localhost:3000'; // or 
var FRONTEND_URL = 'https://pulsenews.app'

console.log('[Pulse Extension] Side panel script loaded');

var originalTabId = null;
var currentNewTabId = null;
var currentNewTabUrl = null;

// Cache of analyzed tabs: { tabId: { url: string, iframeHtml: string } }
var analyzedTabsCache = {};

function showError(message, details) {
  console.error('[Pulse Extension] Error:', message, details);

  var loading = document.getElementById("loading");
  var error = document.getElementById("error");
  var banner = document.getElementById("tabSwitchedBanner");
  var errorMessage = document.getElementById("errorMessage");
  var errorDetails = document.getElementById("errorDetails");
  var iframe = document.getElementById("analysisFrame");

  if (loading) loading.style.display = 'none';
  if (banner) banner.classList.remove('visible');
  if (iframe) iframe.style.display = 'none';
  document.body.classList.remove('banner-visible');

  if (error) {
    error.style.display = 'flex';
    if (errorMessage) errorMessage.textContent = message;
    if (errorDetails && details) errorDetails.textContent = details;
  }
}

function isLikelyArticle(url) {
  // Check if URL looks like a news article
  if (!url) return false;
  
  // Skip common non-article pages
  if (url.startsWith('chrome://') || 
      url.startsWith('chrome-extension://') ||
      url.includes('google.com/search') ||
      url.includes('facebook.com') ||
      url.includes('twitter.com') ||
      url.includes('instagram.com') ||
      url.includes('youtube.com/watch') ||
      url === 'about:blank') {
    return false;
  }
  
  // Check for article-like patterns in URL
  var articlePatterns = [
    /\/article[s]?\//i,
    /\/news\//i,
    /\/story\//i,
    /\/blog\//i,
    /\/post[s]?\//i,
    /\/\d{4}\/\d{2}\//,  // Date pattern like /2025/01/
    /\/(world|politics|business|technology|science|health|sports)\//i,
    /\.html?$/,
    /\d{4,}/  // Article IDs
  ];
  
  return articlePatterns.some(pattern => pattern.test(url));
}

function cacheTabAnalysis(tabId, url) {
  var iframe = document.getElementById("analysisFrame");
  if (!iframe || !iframe.src) return;
  
  console.log('[Pulse Extension] Caching analysis for tab', tabId, 'URL:', url);
  analyzedTabsCache[tabId] = {
    url: url,
    iframeUrl: iframe.src,
    timestamp: Date.now()
  };
  
  // Limit cache to 10 most recent tabs
  var cacheKeys = Object.keys(analyzedTabsCache);
  if (cacheKeys.length > 10) {
    // Sort by timestamp and remove oldest
    var sorted = cacheKeys.sort((a, b) => {
      return analyzedTabsCache[a].timestamp - analyzedTabsCache[b].timestamp;
    });
    delete analyzedTabsCache[sorted[0]];
  }
}

function getCachedAnalysis(tabId, url) {
  var cached = analyzedTabsCache[tabId];
  if (cached && cached.url === url) {
    console.log('[Pulse Extension] Found cached analysis for tab', tabId);
    return cached;
  }
  return null;
}

function showTabSwitchedMessage(newTabUrl, newTabId) {
  console.log('[Pulse Extension] Showing tab switched banner for URL:', newTabUrl);

  // Check if we have cached analysis for this tab
  var cached = getCachedAnalysis(newTabId, newTabUrl);
  if (cached) {
    console.log('[Pulse Extension] Loading cached analysis');
    loadCachedAnalysis(cached, newTabId);
    return;
  }

  var banner = document.getElementById("tabSwitchedBanner");
  var urlPreview = document.getElementById("urlPreview");
  var notArticle = document.getElementById("notArticle");
  var analyzeButton = document.getElementById("analyzeButton");
  var cancelButton = document.getElementById("cancelButton");

  // Show the banner (keep iframe visible below)
  if (banner) {
    banner.classList.add('visible');
    document.body.classList.add('banner-visible');

    // Show URL preview
    if (urlPreview) {
      try {
        var urlObj = new URL(newTabUrl);
        urlPreview.textContent = urlObj.hostname + urlObj.pathname;
      } catch (e) {
        urlPreview.textContent = newTabUrl;
      }
    }

    // Check if it's likely an article
    var isArticle = isLikelyArticle(newTabUrl);
    if (notArticle) {
      notArticle.style.display = isArticle ? 'none' : 'block';
    }

    // Enable/disable button based on URL validity
    if (analyzeButton) {
      var isInvalidPage = newTabUrl.startsWith('chrome://') ||
                          newTabUrl.startsWith('chrome-extension://') ||
                          newTabUrl === 'about:blank';
      analyzeButton.disabled = isInvalidPage;

      // Set up analyze button handler to use the stored new tab info
      analyzeButton.onclick = function() {
        if (analyzeButton.disabled) return;

        console.log('[Pulse Extension] Analyze button clicked for new tab', newTabId);
        banner.classList.remove('visible');
        document.body.classList.remove('banner-visible');

        // Load the new tab analysis (current analysis is already cached in loadAnalysis)
        originalTabId = newTabId;
        loadAnalysis(newTabUrl, newTabId);
      };
    }

    // Set up cancel button handler
    if (cancelButton) {
      cancelButton.onclick = function() {
        console.log('[Pulse Extension] Cancel button clicked');
        banner.classList.remove('visible');
        document.body.classList.remove('banner-visible');
        // Resume monitoring for the new tab (user wants to stay on old analysis)
        originalTabId = newTabId;
      };
    }
  }
}

function loadCachedAnalysis(cached, tabId) {
  var loading = document.getElementById("loading");
  var error = document.getElementById("error");
  var banner = document.getElementById("tabSwitchedBanner");
  var iframe = document.getElementById("analysisFrame");

  // Hide other screens and banner
  if (banner) banner.classList.remove('visible');
  if (error) error.style.display = 'none';
  if (loading) loading.style.display = 'none';
  document.body.classList.remove('banner-visible');

  // Show cached iframe
  if (iframe) {
    iframe.src = cached.iframeUrl;
    iframe.style.display = 'block';
    iframe.classList.add('loaded');
  }

  // Update tracking
  originalTabId = tabId;
}

function loadAnalysis(url, tabId) {
  var loading = document.getElementById("loading");
  var error = document.getElementById("error");
  var banner = document.getElementById("tabSwitchedBanner");
  var iframe = document.getElementById("analysisFrame");

  // Hide other screens and banner, show loading
  if (banner) banner.classList.remove('visible');
  if (error) error.style.display = 'none';
  document.body.classList.remove('banner-visible');
  if (iframe) {
    iframe.style.display = 'none';
    iframe.classList.remove('loaded');
  }
  if (loading) loading.style.display = 'flex';

  // Build iframe URL with autoSubmit parameter
  var iframeUrl = FRONTEND_URL + '/analyze?url=' + encodeURIComponent(url) + '&autoSubmit=true';
  console.log('[Pulse Extension] Loading iframe:', iframeUrl);

  // Set up iframe load handlers
  var loadTimeout = setTimeout(function() {
    showError(
      "Frontend took too long to load",
      "Make sure " + FRONTEND_URL + " is accessible. Check if your local dev server is running."
    );
  }, 15000);

  iframe.onload = function () {
    console.log('[Pulse Extension] Iframe loaded successfully');
    clearTimeout(loadTimeout);
    if (loading) loading.style.display = 'none';
    if (iframe) {
      iframe.style.display = 'block';
      iframe.classList.add('loaded');
    }

    // Cache this analysis
    if (tabId) {
      cacheTabAnalysis(tabId, url);
    }
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
    showError("Failed to set iframe URL", e.message);
  }
}

document.addEventListener("DOMContentLoaded", function () {
  console.log('[Pulse Extension] Side panel DOM loaded');
  
  var iframe = document.getElementById("analysisFrame");
  var loading = document.getElementById("loading");
  var analyzeButton = document.getElementById("analyzeButton");

  if (!iframe || !loading) {
    showError("Missing required elements", "The side panel HTML may be corrupted");
    return;
  }

  // Note: Analyze button click handler is now set in showTabSwitchedMessage()
  // to properly use the stored newTabId and newTabUrl instead of re-querying

  loading.style.display = 'flex';

  // Get current tab URL and remember the tab ID
  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    if (chrome.runtime.lastError || !tabs || !tabs[0]) {
      showError("Cannot access current tab", chrome.runtime.lastError?.message || "No active tab");
      return;
    }

    originalTabId = tabs[0].id;
    var currentUrl = tabs[0].url || '';
    console.log('[Pulse Extension] Opened for tab ID:', originalTabId, 'URL:', currentUrl);

    // Check if we have cached analysis for this tab
    var cached = getCachedAnalysis(originalTabId, currentUrl);
    if (cached) {
      console.log('[Pulse Extension] Loading from cache');
      loadCachedAnalysis(cached, originalTabId);
      return;
    }

    // Check if URL is valid
    if (currentUrl.startsWith('chrome://') || currentUrl.startsWith('chrome-extension://')) {
      showError(
        "Cannot analyze this page",
        "Chrome internal pages cannot be analyzed. Please navigate to a news article."
      );
      return;
    }

    // Load analysis for initial page
    loadAnalysis(currentUrl, originalTabId);
  });
});

// Monitor for tab changes - this runs continuously after panel is opened
setInterval(function() {
  // Only monitor if we have an active tracking tab
  if (originalTabId === null) return;

  chrome.tabs.query({ active: true, currentWindow: true }, function (tabs) {
    if (chrome.runtime.lastError || !tabs || !tabs[0]) {
      return; // Ignore errors
    }

    // If the active tab ID is different from the original
    if (tabs[0].id !== originalTabId) {
      var newTabUrl = tabs[0].url;
      var newTabId = tabs[0].id;

      console.log('[Pulse Extension] Tab switched from', originalTabId, 'to', newTabId);
      console.log('[Pulse Extension] New tab URL:', newTabUrl);

      // Check if new tab is likely an article
      var isArticle = isLikelyArticle(newTabUrl);
      console.log('[Pulse Extension] Is likely article?', isArticle);

      // Only show the tab switch message if it's likely an article
      if (isArticle) {
        // Cache the current tab's analysis before showing the banner
        var currentIframe = document.getElementById("analysisFrame");
        if (currentIframe && currentIframe.src) {
          var urlMatch = currentIframe.src.match(/url=([^&]+)/);
          if (urlMatch) {
            var decodedUrl = decodeURIComponent(urlMatch[1]);
            console.log('[Pulse Extension] Caching current tab', originalTabId, 'before showing banner');
            cacheTabAnalysis(originalTabId, decodedUrl);
          }
        }

        // Store the new tab info
        currentNewTabId = newTabId;
        currentNewTabUrl = newTabUrl;

        showTabSwitchedMessage(newTabUrl, newTabId);

        // Set to null to stop monitoring until user takes action
        originalTabId = null;
      } else {
        // Not an article - keep showing current analysis
        console.log('[Pulse Extension] Not an article, keeping current analysis visible');
        // Don't change anything - iframe stays showing the previous analysis
        // Don't set originalTabId to null - keep monitoring
      }
    }
  });
}, 500); // Check every 500ms
