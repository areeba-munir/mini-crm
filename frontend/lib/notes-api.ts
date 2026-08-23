import { apiRequest } from "@/lib/api";
import type {
  Note,
  NoteCreateInput,
  NoteUpdateInput,
} from "@/types/note";

export function listNotes(
  token: string,
): Promise<Note[]> {
  return apiRequest<Note[]>("/notes", {
    token,
  });
}

export function getNote(
  noteId: number,
  token: string,
): Promise<Note> {
  return apiRequest<Note>(
    `/notes/${noteId}`,
    {
      token,
    },
  );
}

export function createNote(
  input: NoteCreateInput,
  token: string,
): Promise<Note> {
  return apiRequest<Note>("/notes", {
    method: "POST",
    body: JSON.stringify(input),
    token,
  });
}

export function updateNote(
  noteId: number,
  input: NoteUpdateInput,
  token: string,
): Promise<Note> {
  return apiRequest<Note>(
    `/notes/${noteId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
      token,
    },
  );
}

export function deleteNote(
  noteId: number,
  token: string,
): Promise<void> {
  return apiRequest<void>(
    `/notes/${noteId}`,
    {
      method: "DELETE",
      token,
    },
  );
}