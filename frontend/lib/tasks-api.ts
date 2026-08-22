import { apiRequest } from "@/lib/api";
import type {
  Task,
  TaskCreateInput,
  TaskPriority,
  TaskStatus,
  TaskUpdateInput,
} from "@/types/task";

type TaskListFilters = {
  status?: TaskStatus;
  priority?: TaskPriority;
  assigned_to_id?: number;
};

export function listTasks(
  token: string,
  filters: TaskListFilters = {},
): Promise<Task[]> {
  const searchParams = new URLSearchParams();

  if (filters.status) {
    searchParams.set("status", filters.status);
  }

  if (filters.priority) {
    searchParams.set(
      "priority",
      filters.priority,
    );
  }

  if (filters.assigned_to_id) {
    searchParams.set(
      "assigned_to_id",
      String(filters.assigned_to_id),
    );
  }

  const query = searchParams.toString();
  const path = query
    ? `/tasks?${query}`
    : "/tasks";

  return apiRequest<Task[]>(path, {
    token,
  });
}

export function getTask(
  taskId: number,
  token: string,
): Promise<Task> {
  return apiRequest<Task>(
    `/tasks/${taskId}`,
    {
      token,
    },
  );
}

export function createTask(
  input: TaskCreateInput,
  token: string,
): Promise<Task> {
  return apiRequest<Task>("/tasks", {
    method: "POST",
    body: JSON.stringify(input),
    token,
  });
}

export function updateTask(
  taskId: number,
  input: TaskUpdateInput,
  token: string,
): Promise<Task> {
  return apiRequest<Task>(
    `/tasks/${taskId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
      token,
    },
  );
}

export function deleteTask(
  taskId: number,
  token: string,
): Promise<void> {
  return apiRequest<void>(
    `/tasks/${taskId}`,
    {
      method: "DELETE",
      token,
    },
  );
}