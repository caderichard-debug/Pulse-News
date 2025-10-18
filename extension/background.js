// Keep track of the current URL
let currentUrl = null;

// Listen for messages from sidepanel
chrome.runtime.onMessage.addListener(function (message, sender, sendResponse) {
  switch (message.type) {
    case "getCurrentUrl":
      sendResponse(currentUrl);
      break;
    case "setCurrentUrl":
      currentUrl = message.url;
      sendResponse(true);
      break;
    default:
      sendResponse(null);
  }
  return true;
});

// When extension icon is clicked, open side panel
chrome.action.onClicked.addListener(async (tab) => {
  await chrome.sidePanel.open({ windowId: tab.windowId });
});
