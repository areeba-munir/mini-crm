export type MeetingStatus =
  | "Scheduled"
  | "Completed"
  | "Cancelled";

export type Meeting = {
  id: number;
  title: string;
  description: string | null;
  starts_at: string;
  ends_at: string;
  location: string | null;
  meeting_link: string | null;
  notes: string | null;
  status: MeetingStatus;
  organizer_id: number;
  company_id: number | null;
  user_participant_ids: number[];
  contact_participant_ids: number[];
  created_at: string;
  updated_at: string;
};

export type MeetingCreateInput = {
  title: string;
  description?: string | null;
  starts_at: string;
  ends_at: string;
  location?: string | null;
  meeting_link?: string | null;
  notes?: string | null;
  status?: MeetingStatus;
  organizer_id: number;
  company_id?: number | null;
  user_participant_ids?: number[];
  contact_participant_ids?: number[];
};

export type MeetingUpdateInput =
  Partial<MeetingCreateInput>;