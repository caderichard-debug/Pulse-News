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

  // Color schemes for each bias type (muted)
  const colorSchemes = {
    'left': {
      bg: 'bg-blue-100',
      text: 'text-blue-700',
      border: 'border-blue-300',
      label: 'Left'
    },
    'center-left': {
      bg: 'bg-blue-50',
      text: 'text-blue-600',
      border: 'border-blue-200',
      label: 'Center-Left'
    },
    'center': {
      bg: 'bg-purple-100',
      text: 'text-purple-700',
      border: 'border-purple-300',
      label: 'Center'
    },
    'center-right': {
      bg: 'bg-red-50',
      text: 'text-red-600',
      border: 'border-red-200',
      label: 'Center-Right'
    },
    'right': {
      bg: 'bg-red-100',
      text: 'text-red-700',
      border: 'border-red-300',
      label: 'Right'
    }
  };

  const scheme = colorSchemes[normalizedBias] || {
    bg: 'bg-gray-100',
    text: 'text-gray-700',
    border: 'border-gray-300',
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
