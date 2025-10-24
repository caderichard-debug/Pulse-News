import React from 'react';

interface SkeletonProps {
  className?: string;
  variant?: 'text' | 'circular' | 'rectangular' | 'rounded';
  width?: string | number;
  height?: string | number;
  lines?: number;
}

export function Skeleton({
  className = '',
  variant = 'text',
  width,
  height,
  lines = 1
}: SkeletonProps) {
  const baseClasses = 'animate-pulse bg-muted rounded';

  const variantClasses = {
    text: 'h-4',
    circular: 'rounded-full',
    rectangular: '',
    rounded: 'rounded-md'
  };

  const style = {
    width: width || undefined,
    height: height || undefined,
  };

  if (variant === 'text' && lines > 1) {
    return (
      <div className={`space-y-2 ${className}`}>
        {Array.from({ length: lines }, (_, i) => (
          <div
            key={i}
            className={`${baseClasses} ${variantClasses[variant]}`}
            style={{
              ...style,
              width: i === lines - 1 ? '70%' : '100%', // Last line shorter
            }}
          />
        ))}
      </div>
    );
  }

  return (
    <div
      className={`${baseClasses} ${variantClasses[variant]} ${className}`}
      style={style}
    />
  );
}

// Card skeleton for loading states
export function CardSkeleton({
  showAvatar = false,
  showTitle = true,
  showDescription = true,
  showFooter = false
}: {
  showAvatar?: boolean;
  showTitle?: boolean;
  showDescription?: boolean;
  showFooter?: boolean;
}) {
  return (
    <div className="bg-card rounded-lg shadow-sm p-6 border border-border">
      {showAvatar && (
        <div className="flex items-center space-x-4 mb-4">
          <Skeleton variant="circular" width={48} height={48} />
          <div className="flex-1">
            <Skeleton className="mb-2" width="60%" />
            <Skeleton width="40%" />
          </div>
        </div>
      )}

      {showTitle && (
        <Skeleton className="mb-4" width="80%" height={24} />
      )}

      {showDescription && (
        <div className="space-y-2 mb-4">
          <Skeleton lines={3} />
        </div>
      )}

      {showFooter && (
        <div className="flex items-center justify-between pt-4 border-t border-border">
          <Skeleton width={120} />
          <Skeleton width={80} height={32} variant="rounded" />
        </div>
      )}
    </div>
  );
}

// Chart skeleton for loading states
export function ChartSkeleton({
  height = 350,
  showLegend = false,
  showControls = false
}: {
  height?: number;
  showLegend?: boolean;
  showControls?: boolean;
}) {
  return (
    <div className="bg-card rounded-lg shadow-sm p-6 border border-border">
      <div className="mb-4">
        <Skeleton width={200} height={24} className="mb-2" />
        <Skeleton lines={2} width="90%" />
      </div>

      {showControls && (
        <div className="flex justify-end mb-4">
          <div className="flex gap-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} width={60} height={36} variant="rounded" />
            ))}
          </div>
        </div>
      )}

      <div
        className="bg-muted rounded border border-border flex items-center justify-center"
        style={{ height }}
      >
        <div className="text-center">
          <Skeleton variant="circular" width={40} height={40} className="mx-auto mb-4" />
          <Skeleton width={120} className="mx-auto" />
        </div>
      </div>

      {showLegend && (
        <div className="flex justify-center mt-4 space-x-6">
          {[1, 2, 3].map((i) => (
            <div key={i} className="flex items-center space-x-2">
              <Skeleton variant="circular" width={12} height={12} />
              <Skeleton width={60} />
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Article card skeleton
export function ArticleCardSkeleton() {
  return (
    <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
      <div className="p-6">
        <div className="flex items-start justify-between mb-3">
          <div className="flex-1">
            <Skeleton className="mb-2" height={20} />
            <Skeleton width="30%" height={16} />
          </div>
          <Skeleton variant="circular" width={8} height={8} className="ml-3 mt-1" />
        </div>

        <Skeleton lines={3} className="mb-4" />

        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <Skeleton width={80} height={20} variant="rounded" />
            <Skeleton width={60} height={20} variant="rounded" />
          </div>
          <Skeleton width={100} height={16} />
        </div>
      </div>
    </div>
  );
}

// Table skeleton for loading states
export function TableSkeleton({
  rows = 5,
  columns = 4,
  showHeader = true
}: {
  rows?: number;
  columns?: number;
  showHeader?: boolean;
}) {
  return (
    <div className="bg-card rounded-lg shadow-sm border border-border overflow-hidden">
      {showHeader && (
        <div className="border-b border-border bg-muted/50 px-6 py-3">
          <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
            {Array.from({ length: columns }, (_, i) => (
              <Skeleton key={i} height={20} />
            ))}
          </div>
        </div>
      )}

      <div className="divide-y divide-border">
        {Array.from({ length: rows }, (_, rowIndex) => (
          <div key={rowIndex} className="px-6 py-4">
            <div className="grid gap-4" style={{ gridTemplateColumns: `repeat(${columns}, 1fr)` }}>
              {Array.from({ length: columns }, (_, colIndex) => (
                <Skeleton key={colIndex} height={20} />
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// Loading spinner component
export function LoadingSpinner({
  size = 'md',
  text = 'Loading...'
}: {
  size?: 'sm' | 'md' | 'lg';
  text?: string;
}) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className="flex items-center justify-center space-x-3">
      <div
        className={`animate-spin rounded-full border-2 border-primary border-t-transparent ${sizeClasses[size]}`}
      />
      {text && (
        <span className="text-muted-foreground">{text}</span>
      )}
    </div>
  );
}