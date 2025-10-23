'use client';

import React, { useCallback, useMemo, useState, useEffect } from 'react';
import { FixedSizeList as List, VariableSizeList as VariableSizeList } from 'react-window';
import InfiniteLoader from 'react-window-infinite-loader';

interface VirtualizedListProps<T> {
  items: T[];
  itemHeight: number | ((index: number) => number);
  height: number;
  renderItem: (item: T, index: number, style: React.CSSProperties) => React.ReactNode;
  loadMoreItems?: (startIndex: number, stopIndex: number) => Promise<void>;
  hasNextPage?: boolean;
  isNextPageLoading?: boolean;
  estimatedItemHeight?: number;
  overscanCount?: number;
  className?: string;
}

export function VirtualizedList<T>({
  items,
  itemHeight,
  height,
  renderItem,
  loadMoreItems,
  hasNextPage = false,
  isNextPageLoading = false,
  estimatedItemHeight,
  overscanCount = 5,
  className = '',
}: VirtualizedListProps<T>) {
  const [containerHeight, setContainerHeight] = useState(height);

  // Update container height on window resize
  useEffect(() => {
    const updateHeight = () => {
      if (typeof window !== 'undefined') {
        const viewportHeight = window.innerHeight;
        // Reserve space for header, filters, and pagination
        const reservedSpace = 300;
        const newHeight = Math.max(400, viewportHeight - reservedSpace);
        setContainerHeight(newHeight);
      }
    };

    updateHeight();
    window.addEventListener('resize', updateHeight);
    return () => window.removeEventListener('resize', updateHeight);
  }, []);

  const isItemLoaded = useCallback((index: number) => {
    return !hasNextPage || index < items.length;
  }, [hasNextPage, items.length]);

  const loadMoreItemsCallback = useCallback(async (startIndex: number, stopIndex: number) => {
    if (loadMoreItems) {
      await loadMoreItems(startIndex, stopIndex);
    }
  }, [loadMoreItems]);

  const itemCount = hasNextPage ? items.length + 1 : items.length;

  // Render item function for react-window
  const Row = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    if (!isItemLoaded(index)) {
      return (
        <div style={style} className="flex items-center justify-center p-4">
          <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
        </div>
      );
    }

    const item = items[index];
    if (!item) return null;

    return (
      <div style={style}>
        {renderItem(item, index, style)}
      </div>
    );
  }, [items, isItemLoaded, renderItem]);

  // If we have infinite loading, use InfiniteLoader
  if (loadMoreItems) {
    return (
      <div className={className} style={{ height: containerHeight }}>
        <InfiniteLoader
          isItemLoaded={isItemLoaded}
          itemCount={itemCount}
          loadMoreItems={loadMoreItemsCallback}
          threshold={5}
        >
          {({ onItemsRendered, ref }) => {
            if (typeof itemHeight === 'function') {
              return (
                <VariableSizeList
                  ref={ref}
                  height={containerHeight}
                  itemCount={itemCount}
                  itemSize={itemHeight}
                  itemData={items}
                  onItemsRendered={onItemsRendered}
                  overscanCount={overscanCount}
                >
                  {Row}
                </VariableSizeList>
              );
            } else {
              return (
                <List
                  ref={ref}
                  height={containerHeight}
                  itemCount={itemCount}
                  itemSize={itemHeight}
                  itemData={items}
                  onItemsRendered={onItemsRendered}
                  overscanCount={overscanCount}
                >
                  {Row}
                </List>
              );
            }
          }}
        </InfiniteLoader>
      </div>
    );
  }

  // Simple fixed-size list
  if (typeof itemHeight === 'number') {
    return (
      <div className={className} style={{ height: containerHeight }}>
        <List
          height={containerHeight}
          itemCount={items.length}
          itemSize={itemHeight}
          itemData={items}
          overscanCount={overscanCount}
        >
          {Row}
        </List>
      </div>
    );
  }

  // Variable-size list
  return (
    <div className={className} style={{ height: containerHeight }}>
      <VariableSizeList
        height={containerHeight}
        itemCount={items.length}
        itemSize={itemHeight}
        itemData={items}
        overscanCount={overscanCount}
      >
        {Row}
      </VariableSizeList>
    </div>
  );
}

// Hook for measuring dynamic item heights
export function useItemHeights(
  itemCount: number,
  defaultHeight: number,
  measureElement?: (index: number) => number | null
) {
  const [itemHeights, setItemHeights] = useState<number[]>(() =>
    Array(itemCount).fill(defaultHeight)
  );

  const getItemHeight = useCallback((index: number) => {
    if (measureElement) {
      const measuredHeight = measureElement(index);
      if (measuredHeight !== null) {
        return measuredHeight;
      }
    }
    return itemHeights[index] || defaultHeight;
  }, [itemHeights, defaultHeight, measureElement]);

  const setItemHeight = useCallback((index: number, height: number) => {
    setItemHeights(prev => {
      const newHeights = [...prev];
      newHeights[index] = height;
      return newHeights;
    });
  }, []);

  return { getItemHeight, setItemHeight };
}

// Virtualized grid component for card layouts
interface VirtualizedGridProps<T> {
  items: T[];
  columns: number;
  itemHeight: number;
  height: number;
  renderItem: (item: T, index: number) => React.ReactNode;
  gap?: number;
  className?: string;
}

export function VirtualizedGrid<T>({
  items,
  columns,
  itemHeight,
  height,
  renderItem,
  gap = 16,
  className = '',
}: VirtualizedGridProps<T>) {
  const rowCount = Math.ceil(items.length / columns);

  const Row = useCallback(({ index, style }: { index: number; style: React.CSSProperties }) => {
    const start = index * columns;
    const end = Math.min(start + columns, items.length);
    const rowItems = items.slice(start, end);

    return (
      <div
        style={{
          ...style,
          display: 'flex',
          gap: `${gap}px`,
          padding: '0 8px',
        }}
      >
        {rowItems.map((item, colIndex) => (
          <div
            key={`${index}-${colIndex}`}
            style={{
              flex: 1,
              minWidth: 0,
            }}
          >
            {renderItem(item, start + colIndex)}
          </div>
        ))}
      </div>
    );
  }, [items, columns, gap, renderItem]);

  return (
    <div className={className}>
      <List
        height={height}
        itemCount={rowCount}
        itemSize={itemHeight + gap}
        overscanCount={3}
      >
        {Row}
      </List>
    </div>
  );
}

// Hook for intersection observer to load more items
export function useInfiniteScroll(
  hasMore: boolean,
  isLoading: boolean,
  onLoadMore: () => void
) {
  const [containerRef, setContainerRef] = useState<HTMLElement | null>(null);

  useEffect(() => {
    if (!containerRef) return;

    const observer = new IntersectionObserver(
      (entries) => {
        const target = entries[0];
        if (target.isIntersecting && hasMore && !isLoading) {
          onLoadMore();
        }
      },
      {
        root: null,
        rootMargin: '200px',
        threshold: 0.1,
      }
    );

    const sentinel = document.createElement('div');
    sentinel.style.height = '1px';
    containerRef.appendChild(sentinel);

    observer.observe(sentinel);

    return () => {
      observer.unobserve(sentinel);
      if (containerRef.contains(sentinel)) {
        containerRef.removeChild(sentinel);
      }
    };
  }, [containerRef, hasMore, isLoading, onLoadMore]);

  return setContainerRef;
}