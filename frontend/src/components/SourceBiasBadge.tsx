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

  // Color schemes for each bias type
  const colorSchemes = {
    'left': {
      bg: 'bg-blue-600',
      text: 'text-white',
      border: 'border-blue-700',
      label: 'Left'
    },
    'center-left': {
      bg: 'bg-blue-400',
      text: 'text-white',
      border: 'border-blue-500',
      label: 'Center-Left'
    },
    'center': {
      bg: 'bg-purple-600',
      text: 'text-white',
      border: 'border-purple-700',
      label: 'Center'
    },
    'center-right': {
      bg: 'bg-red-400',
      text: 'text-white',
      border: 'border-red-500',
      label: 'Center-Right'
    },
    'right': {
      bg: 'bg-red-600',
      text: 'text-white',
      border: 'border-red-700',
      label: 'Right'
    }
  };

  const scheme = colorSchemes[normalizedBias] || {
    bg: 'bg-gray-400',
    text: 'text-white',
    border: 'border-gray-500',
    label: bias
  };

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
        ${scheme.bg} ${scheme.text} ${scheme.border}
        ${sizeClasses[size]}
        font-medium rounded-md border
        whitespace-nowrap
      `}
      title={`Organizational Bias: ${scheme.label}`}
    >
      {showLabel && scheme.label}
    </span>
  );
}
