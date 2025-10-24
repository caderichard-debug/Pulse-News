'use client';

import { useState } from 'react';

interface ExtensionBannerProps {
  className?: string;
}

export default function ExtensionBanner({ className = '' }: ExtensionBannerProps) {
  const [isVisible, setIsVisible] = useState(true);

  if (!isVisible) return null;

  return (
    <div className={`bg-gradient-to-r from-indigo-500 to-purple-600 text-white px-4 py-3 ${className}`}>
      <div className="max-w-7xl mx-auto flex items-center justify-between">
        <div className="flex items-center space-x-4">
          <span className="text-lg">🚀</span>
          <div>
            <span className="font-semibold">New: Pulse Chrome Extension</span>
            <span className="ml-2 text-indigo-100">Analyze any article instantly while browsing</span>
          </div>
        </div>

        <div className="flex items-center space-x-4">
          <a
            href="https://chromewebstore.google.com/detail/gcfamjhnhdhoobgcmnkepjibcmhafpfp?utm_source=item-share-cb"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-white text-indigo-600 px-4 py-2 rounded-lg font-medium hover:bg-indigo-50 transition-colors"
          >
            Install Extension
          </a>

          <button
            onClick={() => setIsVisible(false)}
            className="text-indigo-200 hover:text-white transition-colors"
            aria-label="Dismiss banner"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  );
}