export type LeadStage = "New" | "Contacted" | "Qualified" | "Won" | "Lost";

export type LeadSort =
  "newest" | "oldest" | "value_high" | "value_low" | "close_soon";

export type LeadListFilters = {
  q?: string;
  stage?: LeadStage;
  company_id?: number;
  contact_id?: number;
  min_estimated_value?: string;
  max_estimated_value?: string;
  expected_close_from?: string;
  expected_close_to?: string;
  sort_by?: LeadSort;
};

export type Lead = {
  id: number;
  title: string;
  company_id: number;
  contact_id: number | null;
  stage: LeadStage;
  estimated_value: string | null;
  source: string | null;
  expected_close_date: string | null;
  description: string | null;
  created_at: string;
  updated_at: string;
};

export type LeadCreateInput = {
  title: string;
  company_id: number;
  contact_id?: number | null;
  stage?: LeadStage;
  estimated_value?: string | null;
  source?: string | null;
  expected_close_date?: string | null;
  description?: string | null;
};

export type LeadUpdateInput = Partial<LeadCreateInput>;
