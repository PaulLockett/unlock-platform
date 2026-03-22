import useSWR from "swr";
import type { ViewDefinition } from "@/types/platform";

const fetcher = async (url: string) => {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to fetch views: ${res.status}`);
  const data = await res.json();
  return (data.items ?? []) as ViewDefinition[];
};

export function useViews() {
  const { data, error, isLoading, mutate } = useSWR("/api/views", fetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 10_000,
  });

  return {
    views: data ?? [],
    isLoading,
    isError: !!error,
    refresh: mutate,
  };
}
