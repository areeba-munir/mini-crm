export type TaskStatus =
  | "Pending"
  | "In Progress"
  | "Completed";

export type TaskPriority =
  | "Low"
  | "Medium"
  | "High";

export type Task = {
  id: number;
  title: string;
  description: string | null;
  status: TaskStatus;
  priority: TaskPriority;
  due_at: string | null;
  assigned_to_id: number;
  created_by_id: number;
  company_id: number | null;
  contact_id: number | null;
  lead_id: number | null;
  completed_at: string | null;
  created_at: string;
  updated_at: string;
};

export type TaskCreateInput = {
  title: string;
  description?: string | null;
  status?: TaskStatus;
  priority?: TaskPriority;
  due_at?: string | null;
  assigned_to_id: number;
  company_id?: number | null;
  contact_id?: number | null;
  lead_id?: number | null;
};

export type TaskUpdateInput =
  Partial<TaskCreateInput>;