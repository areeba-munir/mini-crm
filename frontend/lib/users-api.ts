import { apiRequest } from "@/lib/api";
import type { User, UserAdminUpdateInput } from "@/types/auth";

export function listUsers(token: string): Promise<User[]> {
  return apiRequest<User[]>("/users", {
    token,
  });
}

export function updateUserAdministration(
  userId: number,
  input: UserAdminUpdateInput,
  token: string,
): Promise<User> {
  return apiRequest<User>(`/users/${userId}`, {
    method: "PATCH",
    body: JSON.stringify(input),
    token,
  });
}
