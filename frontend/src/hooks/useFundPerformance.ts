import { useState, useEffect, useCallback, useRef } from "react";
import { getFundPerformanceTrend } from "@/api/fund";
import type { PerformanceTrendResponse } from "@/types/fund";

interface UseFundPerformanceReturn {
  data: PerformanceTrendResponse | null;
  loading: boolean;
  error: string | null;
  refetch: () => void;
}

export function useFundPerformance(code: string | undefined, period: string): UseFundPerformanceReturn {
  const [data, setData] = useState<PerformanceTrendResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const fetchData = useCallback(async () => {
    if (!code || !period) {
      setData(null);
      return;
    }

    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setLoading(true);
    setError(null);

    try {
      const res = await getFundPerformanceTrend(code, period);
      if (!controller.signal.aborted) {
        setData(res.data);
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        setError(err instanceof Error ? err.message : "获取数据失败");
      }
    } finally {
      if (!controller.signal.aborted) {
        setLoading(false);
      }
    }
  }, [code, period]);

  useEffect(() => {
    fetchData();
    return () => {
      abortRef.current?.abort();
    };
  }, [fetchData]);

  return { data, loading, error, refetch: fetchData };
}