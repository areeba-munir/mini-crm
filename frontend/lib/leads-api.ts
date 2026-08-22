import { apiRequest } from "@/lib/api";
import type {
  Lead,
  LeadCreateInput,
  LeadStage,
  LeadUpdateInput,
} from "@/types/lead";

type LeadListFilters = {
  stage?: LeadStage;
};

export function listLeads(
  token: string,
  filters: LeadListFilters = {},
): Promise<Lead[]> {
  const searchParams = new URLSearchParams();

  if (filters.stage) {
    searchParams.set("stage", filters.stage);
  }

  const query = searchParams.toString();
  const path = query
    ? `/leads?${query}`
    : "/leads";

  return apiRequest<Lead[]>(path, {
    token,
  });
}

export function getLead(
  leadId: number,
  token: string,
): Promise<Lead> {
  return apiRequest<Lead>(
    `/leads/${leadId}`,
    {
      token,
    },
  );
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
  return apiRequest<Lead>(
    `/leads/${leadId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
      token,
    },
  );
}

export function deleteLead(
  leadId: number,
  token: string,
): Promise<void> {
  return apiRequest<void>(
    `/leads/${leadId}`,
    {
      method: "DELETE",
      token,
    },
  );
}