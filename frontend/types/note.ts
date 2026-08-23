export type Note = {
  id: number;
  body: string;
  author_id: number;
  company_id: number | null;
  contact_id: number | null;
  lead_id: number | null;
  created_at: string;
  updated_at: string;
};

export type NoteCreateInput = {
  body: string;
  company_id?: number | null;
  contact_id?: number | null;
  lead_id?: number | null;
};

export type NoteUpdateInput =
  Partial<NoteCreateInput>;