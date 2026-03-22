import useSWR from "swr";
import type { ViewDefinition } from "@/types/platform";

interface ViewResponse {
  success: boolean;
  message?: string;
  view?: ViewDefinition;
  schema?: Record<string, unknown> | null;
  permissions?: Array<{ principal_id: string; permission: string }>;
}

const fetcher = async (url: string): Promise<ViewResponse> => {
  const res = await fetch(url);
  const data = await res.json();
  if (!data.success) {
    const err = new Error(data.message || "Failed to load view");
    (err as Error & { status: number }).status = res.status;
    throw err;
  }
  return data;
};

export function useView(shareToken: string | null) {
  const { data, error, isLoading, mutate } = useSWR(
    shareToken ? `/api/views/${shareToken}` : null,
    fetcher,
    {
      revalidateOnFocus: false,
      dedupingInterval: 10_000,
    },
  );

  return {
    view: data?.view ?? null,
    schema: data?.schema ?? null,
    permissions: data?.permissions ?? [],
    isLoading,
    isError: !!error,
    errorMessage: error?.message ?? "",
    refresh: mutate,
  };
}
