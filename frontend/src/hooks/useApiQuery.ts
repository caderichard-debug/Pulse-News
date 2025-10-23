import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import toast from "react-hot-toast";

// Generic query key factory
export const createQueryKeys = (prefix: string) => ({
  all: [prefix] as const,
  lists: () => [...[prefix], "list"] as const,
  list: (filters?: any) => [...[prefix], "list", filters] as const,
  details: () => [...[prefix], "detail"] as const,
  detail: (id: string | number) => [...[prefix], "detail", id] as const,
});

// Generic API query hook
export function useApiQuery<T = any>(
  queryKey: readonly unknown[],
  queryFn: () => Promise<T>,
  options?: {
    enabled?: boolean;
    refetchOnWindowFocus?: boolean;
    staleTime?: number;
    onSuccess?: (data: T) => void;
    onError?: (error: Error) => void;
    errorMessage?: string;
  }
) {
  const {
    enabled = true,
    refetchOnWindowFocus = false,
    staleTime = 5 * 60 * 1000, // 5 minutes
    onSuccess,
    onError,
    errorMessage = "Failed to fetch data",
  } = options || {};

  return useQuery({
    queryKey,
    queryFn,
    enabled,
    refetchOnWindowFocus,
    staleTime,
    onSuccess,
    onError: (error: Error) => {
      console.error("API Query Error:", error);
      toast.error(errorMessage);
      onError?.(error);
    },
  });
}

// Generic API mutation hook
export function useApiMutation<T = any, V = any>(
  mutationFn: (variables: V) => Promise<T>,
  options?: {
    onSuccess?: (data: T, variables: V) => void;
    onError?: (error: Error, variables: V) => void;
    successMessage?: string;
    errorMessage?: string;
    invalidateQueries?: readonly unknown[][];
  }
) {
  const queryClient = useQueryClient();
  const {
    onSuccess,
    onError,
    successMessage,
    errorMessage = "Operation failed",
    invalidateQueries = [],
  } = options || {};

  return useMutation({
    mutationFn,
    onSuccess: (data, variables) => {
      // Invalidate related queries
      invalidateQueries.forEach((queryKey) => {
        queryClient.invalidateQueries({ queryKey });
      });

      // Show success toast
      if (successMessage) {
        toast.success(successMessage);
      }

      // Call custom success handler
      onSuccess?.(data, variables);
    },
    onError: (error: Error, variables) => {
      console.error("API Mutation Error:", error);
      toast.error(errorMessage);
      onError?.(error, variables);
    },
  });
}

// Specific hooks for common API operations
export function useAnalytics(timeRange: number = 30) {
  return useApiQuery(
    ["analytics", timeRange],
    () => api.get(`/analytics/user-stats?days=${timeRange}`),
    {
      errorMessage: "Failed to load analytics data",
    }
  );
}

export function useSentimentOverTime(days: number = 30, topicIds?: number[]) {
  const topicParam = topicIds?.length ? topicIds.join(",") : "";
  return useApiQuery(
    ["analytics", "sentiment", days, topicIds],
    () => api.get(`/analytics/sentiment-over-time?days=${days}${topicParam ? `&topic_ids=${topicParam}` : ""}`),
    {
      errorMessage: "Failed to load sentiment data",
    }
  );
}

export function useBiasDistribution(weeks: number = 4) {
  return useApiQuery(
    ["analytics", "bias", weeks],
    () => api.get(`/analytics/bias-distribution?weeks=${weeks}`),
    {
      errorMessage: "Failed to load bias distribution",
    }
  );
}

export function useUserPreferences() {
  return useApiQuery(
    ["preferences"],
    () => api.get("/preferences"),
    {
      errorMessage: "Failed to load user preferences",
    }
  );
}

export function useUpdatePreferences() {
  return useApiMutation(
    (preferences: any) => api.put("/preferences", preferences),
    {
      successMessage: "Preferences updated successfully",
      errorMessage: "Failed to update preferences",
      invalidateQueries: [["preferences"]],
    }
  );
}

export function useArticles(filters: {
  page?: number;
  topics?: number[];
  sources?: number[];
  politicalLean?: string[];
  timeRange?: number;
  sortBy?: string;
}) {
  const params = new URLSearchParams();

  if (filters.page) params.append("page", filters.page.toString());
  if (filters.topics?.length) params.append("topic_ids", filters.topics.join(","));
  if (filters.sources?.length) params.append("source_ids", filters.sources.join(","));
  if (filters.politicalLean?.length) params.append("political_lean", filters.politicalLean.join(","));
  if (filters.timeRange) params.append("days", filters.timeRange.toString());
  if (filters.sortBy) params.append("sort_by", filters.sortBy);

  return useApiQuery(
    ["articles", filters],
    () => api.get(`/feed/articles?${params.toString()}`),
    {
      errorMessage: "Failed to load articles",
    }
  );
}

export function useArticleDetail(id: string | number) {
  return useApiQuery(
    ["article", id],
    () => api.get(`/articles/${id}`),
    {
      enabled: !!id,
      errorMessage: "Failed to load article",
    }
  );
}

export function useTopics() {
  return useApiQuery(
    ["topics"],
    () => api.get("/feed/topics"),
    {
      errorMessage: "Failed to load topics",
    }
  );
}

export function useSources() {
  return useApiQuery(
    ["sources"],
    () => api.get("/feed/sources"),
    {
      errorMessage: "Failed to load sources",
    }
  );
}