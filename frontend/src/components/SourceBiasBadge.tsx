/**
 * SourceBiasBadge Component
 *
 * Displays organizational bias rating for news sources with color coding.
 * Separate from article-level political lean analysis.
 */

import React from 'react';

type BiasType = 'left' | 'center-left' | 'center' | 'center-right' | 'right';

interface SourceBiasBadgeProps {
  bias: BiasType | string | null;
  size?: 'sm' | 'md' | 'lg';
  showLabel?: boolean;
}

export default function SourceBiasBadge({
  bias,
  size = 'md',
  showLabel = true
}: SourceBiasBadgeProps) {
  if (!bias) {
    return null;
  }

  // Normalize bias string
  const normalizedBias = bias.toLowerCase() as BiasType;

  // Map bias types to CSS classes (with dark mode support from globals.css)
  const biasClassMap = {
    'left': 'bias-left',
    'center-left': 'bias-center-left',
    'center': 'bias-center',
    'center-right': 'bias-center-right',
    'right': 'bias-right'
  };

  // Labels for each bias type
  const labelMap = {
    'left': 'Left',
    'center-left': 'Center-Left',
    'center': 'Center',
    'center-right': 'Center-Right',
    'right': 'Right'
  };

  const biasClass = biasClassMap[normalizedBias] || 'bias-fallback';
  const label = labelMap[normalizedBias] || bias;

  // Size classes
  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-2 py-1 text-xs',
    lg: 'px-3 py-1.5 text-sm'
  };

  return (
    <span
      className={`
        inline-flex items-center justify-center
        ${biasClass}
        ${sizeClasses[size]}
        font-medium rounded-md border
        whitespace-nowrap
      `}
      title={`Organizational Bias: ${label}`}
    >
      {showLabel && label}
    </span>
  );
}
