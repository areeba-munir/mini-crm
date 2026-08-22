export type Company = {
  id: number;
  name: string;
  industry: string | null;
  website: string | null;
  email: string | null;
  phone: string | null;
  address: string | null;
  created_at: string;
  updated_at: string;
};

export type CompanyCreateInput = {
  name: string;
  industry?: string | null;
  website?: string | null;
  email?: string | null;
  phone?: string | null;
  address?: string | null;
};

export type CompanyUpdateInput =
  Partial<CompanyCreateInput>;