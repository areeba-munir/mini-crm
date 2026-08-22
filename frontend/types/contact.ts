export type Contact = {
  id: number;
  first_name: string;
  last_name: string | null;
  email: string | null;
  phone: string | null;
  job_title: string | null;
  company_id: number | null;
  created_at: string;
  updated_at: string;
};

export type ContactCreateInput = {
  first_name: string;
  last_name?: string | null;
  email?: string | null;
  phone?: string | null;
  job_title?: string | null;
  company_id?: number | null;
};

export type ContactUpdateInput =
  Partial<ContactCreateInput>;