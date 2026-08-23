import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Lead } from "@/types/lead";

export type SearchResults = {
  companies: Company[];
  contacts: Contact[];
  leads: Lead[];
};
