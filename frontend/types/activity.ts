import type { UserRole } from "@/types/auth";

export type ActivityAction = "Created" | "Updated" | "Deleted";

export type ActivityActor = {
  id: number;
  full_name: string;
  email: string;
  role: UserRole;
};

export type ActivityLog = {
  id: number;
  actor_id: number | null;
  actor: ActivityActor | null;
  action: ActivityAction;
  entity_type: string;
  entity_id: number | null;
  description: string;
  details: Record<string, unknown> | null;
  created_at: string;
};
