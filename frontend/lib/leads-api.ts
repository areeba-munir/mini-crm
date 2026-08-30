import { apiRequest } from "@/lib/api";
import type {
  Lead,
  LeadCreateInput,
  LeadListFilters,
  LeadUpdateInput,
} from "@/types/lead";

export function listLeads(
  token: string,
  filters: LeadListFilters = {},
): Promise<Lead[]> {
  const searchParams = new URLSearchParams();
  const queryText = filters.q?.trim();

  if (queryText) {
    searchParams.set("q", queryText);
  }

  if (filters.stage) {
    searchParams.set("stage", filters.stage);
  }

  if (filters.company_id !== undefined) {
    searchParams.set("company_id", String(filters.company_id));
  }

  if (filters.contact_id !== undefined) {
    searchParams.set("contact_id", String(filters.contact_id));
  }

  if (filters.min_estimated_value) {
    searchParams.set("min_estimated_value", filters.min_estimated_value);
  }

  if (filters.max_estimated_value) {
    searchParams.set("max_estimated_value", filters.max_estimated_value);
  }

  if (filters.expected_close_from) {
    searchParams.set("expected_close_from", filters.expected_close_from);
  }

  if (filters.expected_close_to) {
    searchParams.set("expected_close_to", filters.expected_close_to);
  }

  if (filters.sort_by) {
    searchParams.set("sort_by", filters.sort_by);
  }

  const query = searchParams.toString();
  const path = query ? `/leads?${query}` : "/leads";

  return apiRequest<Lead[]>(path, {
    token,
  });
}

export function getLead(leadId: number, token: string): Promise<Lead> {
  return apiRequest<Lead>(`/leads/${leadId}`, {
    token,
  });
}

export function createLead(
  input: LeadCreateInput,
  token: string,
): Promise<Lead> {
  return apiRequest<Lead>("/leads", {
    method: "POST",
    body: JSON.stringify(input),
    token,
  });
}

export function updateLead(
  leadId: number,
  input: LeadUpdateInput,
  token: string,
): Promise<Lead> {
  return apiRequest<Lead>(`/leads/${leadId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
    token,
  });
}

export function deleteLead(leadId: number, token: string): Promise<void> {
  return apiRequest<void>(`/leads/${leadId}`, {
    method: "DELETE",
    token,
  });
}
