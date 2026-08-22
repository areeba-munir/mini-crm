import { apiRequest } from "@/lib/api";
import type {
  Contact,
  ContactCreateInput,
  ContactUpdateInput,
} from "@/types/contact";

export function listContacts(
  token: string,
): Promise<Contact[]> {
  return apiRequest<Contact[]>("/contacts", {
    token,
  });
}

export function getContact(
  contactId: number,
  token: string,
): Promise<Contact> {
  return apiRequest<Contact>(
    `/contacts/${contactId}`,
    {
      token,
    },
  );
}

export function createContact(
  input: ContactCreateInput,
  token: string,
): Promise<Contact> {
  return apiRequest<Contact>("/contacts", {
    method: "POST",
    body: JSON.stringify(input),
    token,
  });
}

export function updateContact(
  contactId: number,
  input: ContactUpdateInput,
  token: string,
): Promise<Contact> {
  return apiRequest<Contact>(
    `/contacts/${contactId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
      token,
    },
  );
}

export function deleteContact(
  contactId: number,
  token: string,
): Promise<void> {
  return apiRequest<void>(
    `/contacts/${contactId}`,
    {
      method: "DELETE",
      token,
    },
  );
}