# Pulse News Analyzer - Chrome Extension

A Chrome extension that allows you to analyze news articles directly from your browser using Pulse's AI-powered analysis. The extension opens as a **side panel** on the right side of your browser window for a better reading experience.

## Features

- **Right-aligned side panel**: Opens on the right side of your browser window, not as a small popup
- **Auto-updating URL**: Automatically updates when you navigate to different pages
- **One-click article analysis**: Automatically detects the current page URL and opens the Pulse analyzer
- **Embedded interface**: View analysis results directly in the side panel
- **URL persistence**: Remembers the last analyzed URL across sessions
- **Tab awareness**: Updates when you switch tabs or navigate to new pages

## Installation

### For Development

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top right)
3. Click "Load unpacked"
4. Select the `extension` directory from this project
5. The Pulse icon will appear in your Chrome toolbar

### Building for Production

Before deploying to production:

1. Edit `sidepanel/sidepanel.js` and change `FRONTEND_URL` to your production URL:
   ```javascript
   var FRONTEND_URL = 'https://pulsenews.app';
   ```

2. Update `manifest.json` `host_permissions` if needed:
   ```json
   "host_permissions": ["https://pulsenews.app/*"]
   ```

## Project Structure

```
extension/
├── manifest.json              # Extension configuration (Side Panel API)
├── background.js             # Service worker for URL state & side panel trigger
├── config.js                 # Environment configuration
├── sidepanel/
│   ├── sidepanel.html        # Side panel UI (full height)
│   └── sidepanel.js          # Side panel logic with auto-updates
├── popup/                    # Legacy popup (kept for reference)
│   ├── popup.html
│   └── popup.js
├── icons/                    # Extension icons (16, 48, 128px)
├── generate-icons.js         # Icon generation script
└── pulse-icon.png            # Source icon
```

## How It Works

1. **User clicks extension icon**: The side panel opens on the right side of the browser
2. **Side panel captures current URL**: Gets the active tab's URL
3. **Background state**: The background service worker stores the URL to persist it
4. **Iframe loading**: The side panel loads the Pulse analyze page in an iframe with the URL pre-filled
5. **Analysis display**: User can submit the URL for analysis and view results in the side panel
6. **Auto-update**: When you navigate to a new page or switch tabs, the side panel automatically updates

## Using the Extension

### Opening the Side Panel

1. Navigate to any news article (e.g., NYTimes, BBC, etc.)
2. Click the **Pulse extension icon** in your Chrome toolbar
3. The side panel opens on the **right side** of your browser window
4. The article URL is already pre-filled in the input field
5. Click **"Analyze Article"** to get AI-powered insights

### Analyzing Multiple Articles

- The side panel stays open as you browse
- Navigate to a different article → the URL updates automatically
- Click "Analyze Article" again for the new page

### Viewing Full Articles

- After analysis, click **"View in Feed"** to open the full article page in a new tab
- Click **"Analyze Another Article"** to reset the form

## Configuration

### Environment Setup

Edit `sidepanel/sidepanel.js` to change the frontend URL:

```javascript
// For development
var FRONTEND_URL = 'http://localhost:3000';

// For production
var FRONTEND_URL = 'https://pulsenews.app';
```

### Permissions

The extension requires these permissions:
- `tabs`: To access the current tab's URL
- `storage`: To persist state
- `activeTab`: To interact with the active tab
- `scripting`: For potential future features
- `sidePanel`: To use the Chrome Side Panel API

## Development

### Generating Icons

If you update `pulse-icon.png`, regenerate the icon sizes:

```bash
npm run generate-icons
```

This creates 16x16, 48x48, and 128x128 versions in the `icons/` directory.

### Testing

1. Make sure your Pulse frontend is running (http://localhost:3000)
2. Load the extension in Chrome (see Installation above)
3. Navigate to any news article
4. Click the Pulse extension icon
5. The side panel should open on the right with the current URL pre-filled

### Debugging

- **Side panel issues**: Right-click in the side panel → "Inspect"
- **Background worker issues**: Go to `chrome://extensions/` → Click "Inspect views: service worker"
- **Console logs**: Check both side panel and background worker consoles
- **Auto-update not working**: Check background worker console for tab listener errors

## Key Differences: Side Panel vs Popup

### Old Popup Approach ❌
- Small fixed size (600x500px)
- Appeared below extension icon
- Closed when clicking outside
- Fixed position, not moveable

### New Side Panel Approach ✅
- Full browser height
- Opens on right side of window
- Stays open while you browse
- Can be resized by dragging
- Auto-updates when navigating
- Better for reading long analysis results

## Browser Compatibility

- **Chrome 114+**: Full support (Side Panel API introduced)
- **Edge 114+**: Full support (Chromium-based)
- **Firefox**: Not supported (Side Panel API is Chrome-specific)
- **Safari**: Not supported

## Known Limitations

- Side Panel API requires Chrome 114 or higher
- The iframe approach means the analyze page loads within the side panel
- Cross-origin restrictions prevent direct communication with the iframe
- Side panel width can be resized by user but defaults to ~400px

## Future Enhancements

- [ ] Add keyboard shortcuts to toggle side panel
- [ ] Support for analyzing selected text
- [ ] Quick source bias lookup
- [ ] Recent analysis history within side panel
- [ ] Dark mode support matching browser theme
- [ ] Persistent width preference

## Troubleshooting

### Extension won't load
- Make sure you're using Chrome 114 or higher
- Check that `manifest.json` is valid JSON
- Verify all icon files exist in `icons/`
- Ensure file paths in manifest match actual structure

### Side panel shows blank screen
- Check browser console for errors (right-click in panel → Inspect)
- Verify `FRONTEND_URL` is accessible
- Ensure frontend is running (for development)
- Check background worker for errors

### URL not pre-filling
- Check background worker console for errors
- Verify the current tab URL is accessible (won't work on chrome:// pages)
- Make sure tab permissions are granted

### Side panel won't open
- Make sure you're clicking the extension icon, not right-clicking
- Check that `sidePanel` permission is in manifest.json
- Verify Chrome version is 114+

### Auto-update not working
- Check background worker console for tab listener errors
- Make sure you're on Chrome 114+ (earlier versions may not support all features)
- Try reloading the extension

## Publishing

To publish to the Chrome Web Store:

1. Update `FRONTEND_URL` to production in `sidepanel/sidepanel.js`
2. Create a `.zip` of the extension directory:
   ```bash
   # Exclude development files
   zip -r pulse-extension.zip extension/ -x "*/node_modules/*" "*.png" "*/popup/*"
   ```
3. Upload to [Chrome Web Store Developer Dashboard](https://chrome.google.com/webstore/devconsole/)
4. Fill in store listing details:
   - **Name**: Pulse News Analyzer
   - **Description**: AI-powered news analysis with bias detection, fact-checking, and ethical framework mapping
   - **Category**: Productivity
   - **Screenshots**: Side panel showing analysis results
5. Submit for review (usually takes 1-3 days)

## License

ISC
