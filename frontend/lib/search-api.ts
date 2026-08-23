import { apiRequest } from "@/lib/api";
import type { SearchResults } from "@/types/search";

export function searchCrm(
  query: string,
  token: string,
  limit = 10,
): Promise<SearchResults> {
  const searchParameters = new URLSearchParams({
    q: query.trim(),
    limit: String(limit),
  });

  return apiRequest<SearchResults>(`/search?${searchParameters.toString()}`, {
    token,
  });
}
