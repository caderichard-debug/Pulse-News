#!/usr/bin/env node
/**
 * Script to automatically apply dark mode classes to files
 * Usage: node scripts/apply-dark-mode.js <file-path>
 */

const fs = require('fs');
const path = require('path');

// Color class mappings from light-only to theme-aware
const replacements = [
  // Backgrounds
  { from: /className="([^"]*)\bbg-white\b([^"]*)"/g, to: 'className="$1bg-card$2"' },
  { from: /className="([^"]*)\bbg-gray-50\b([^"]*)"/g, to: 'className="$1bg-background$2"' },
  { from: /className="([^"]*)\bbg-gray-100\b([^"]*)"/g, to: 'className="$1bg-secondary$2"' },

  // Text colors
  { from: /className="([^"]*)\btext-gray-900\b([^"]*)"/g, to: 'className="$1text-foreground$2"' },
  { from: /className="([^"]*)\btext-gray-800\b([^"]*)"/g, to: 'className="$1text-foreground$2"' },
  { from: /className="([^"]*)\btext-gray-700\b([^"]*)"/g, to: 'className="$1text-card-foreground$2"' },
  { from: /className="([^"]*)\btext-gray-600\b([^"]*)"/g, to: 'className="$1text-muted-foreground$2"' },
  { from: /className="([^"]*)\btext-gray-500\b([^"]*)"/g, to: 'className="$1text-muted-foreground$2"' },

  // Borders
  { from: /className="([^"]*)\bborder-gray-200\b([^"]*)"/g, to: 'className="$1border-border$2"' },
  { from: /className="([^"]*)\bborder-gray-300\b([^"]*)"/g, to: 'className="$1border-border$2"' },

  // Primary colors (indigo -> primary)
  { from: /className="([^"]*)\bbg-indigo-600\b([^"]*)"/g, to: 'className="$1bg-primary$2"' },
  { from: /className="([^"]*)\btext-indigo-600\b([^"]*)"/g, to: 'className="$1text-primary$2"' },
  { from: /className="([^"]*)\bhover:bg-indigo-700\b([^"]*)"/g, to: 'className="$1hover:bg-primary-hover$2"' },

  // Loading states
  { from: /border-indigo-600/g, to: 'border-primary' },
];

function applyDarkMode(filePath) {
  if (!fs.existsSync(filePath)) {
    console.error(`File not found: ${filePath}`);
    process.exit(1);
  }

  let content = fs.readFileSync(filePath, 'utf8');
  let changeCount = 0;

  replacements.forEach(({ from, to }) => {
    const matches = content.match(from);
    if (matches) {
      changeCount += matches.length;
      content = content.replace(from, to);
    }
  });

  if (changeCount > 0) {
    fs.writeFileSync(filePath, content, 'utf8');
    console.log(`✅ Updated ${filePath}: ${changeCount} changes`);
  } else {
    console.log(`ℹ️  No changes needed for ${filePath}`);
  }
}

// Main
const filePath = process.argv[2];
if (!filePath) {
  console.error('Usage: node scripts/apply-dark-mode.js <file-path>');
  process.exit(1);
}

applyDarkMode(filePath);
