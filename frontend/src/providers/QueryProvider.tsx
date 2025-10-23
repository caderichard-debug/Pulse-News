"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { ReactQueryDevtools } from "@tanstack/react-query-devtools";
import { useState } from "react";

export function QueryProvider({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            // Time in milliseconds that data remains fresh
            staleTime: 5 * 60 * 1000, // 5 minutes
            // Time in milliseconds that inactive queries will remain in cache
            gcTime: 10 * 60 * 1000, // 10 minutes (previously cacheTime)
            // Number of times to retry a failed request
            retry: (failureCount, error: any) => {
              // Don't retry on 4xx errors except 408, 429
              if (error?.status >= 400 && error?.status < 500 &&
                  ![408, 429].includes(error.status)) {
                return false;
              }
              // Retry up to 2 times for other errors
              return failureCount < 2;
            },
            // Delay between retries in milliseconds
            retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
            // Refetch on window focus (disabled for mobile data savings)
            refetchOnWindowFocus: false,
            // Refetch on reconnect
            refetchOnReconnect: true,
          },
          mutations: {
            // Retry mutations once
            retry: 1,
            // Don't retry mutations on 4xx errors
            retryDelay: 1000,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      {children}
      {process.env.NODE_ENV === "development" && (
        <ReactQueryDevtools initialIsOpen={false} />
      )}
    </QueryClientProvider>
  );
}