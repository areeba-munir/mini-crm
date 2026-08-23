import { apiRequest } from "@/lib/api";
import type {
  Meeting,
  MeetingCreateInput,
  MeetingUpdateInput,
} from "@/types/meeting";

export function listMeetings(
  token: string,
): Promise<Meeting[]> {
  return apiRequest<Meeting[]>("/meetings", {
    token,
  });
}

export function getMeeting(
  meetingId: number,
  token: string,
): Promise<Meeting> {
  return apiRequest<Meeting>(
    `/meetings/${meetingId}`,
    {
      token,
    },
  );
}

export function createMeeting(
  input: MeetingCreateInput,
  token: string,
): Promise<Meeting> {
  return apiRequest<Meeting>("/meetings", {
    method: "POST",
    body: JSON.stringify(input),
    token,
  });
}

export function updateMeeting(
  meetingId: number,
  input: MeetingUpdateInput,
  token: string,
): Promise<Meeting> {
  return apiRequest<Meeting>(
    `/meetings/${meetingId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
      token,
    },
  );
}

export function deleteMeeting(
  meetingId: number,
  token: string,
): Promise<void> {
  return apiRequest<void>(
    `/meetings/${meetingId}`,
    {
      method: "DELETE",
      token,
    },
  );
}