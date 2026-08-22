import { apiRequest } from "@/lib/api";
import type {
  Company,
  CompanyCreateInput,
  CompanyUpdateInput,
} from "@/types/company";

export function listCompanies(
  token: string,
): Promise<Company[]> {
  return apiRequest<Company[]>("/companies", {
    token,
  });
}

export function getCompany(
  companyId: number,
  token: string,
): Promise<Company> {
  return apiRequest<Company>(
    `/companies/${companyId}`,
    {
      token,
    },
  );
}

export function createCompany(
  input: CompanyCreateInput,
  token: string,
): Promise<Company> {
  return apiRequest<Company>("/companies", {
    method: "POST",
    body: JSON.stringify(input),
    token,
  });
}

export function updateCompany(
  companyId: number,
  input: CompanyUpdateInput,
  token: string,
): Promise<Company> {
  return apiRequest<Company>(
    `/companies/${companyId}`,
    {
      method: "PATCH",
      body: JSON.stringify(input),
      token,
    },
  );
}

export function deleteCompany(
  companyId: number,
  token: string,
): Promise<void> {
  return apiRequest<void>(
    `/companies/${companyId}`,
    {
      method: "DELETE",
      token,
    },
  );
}
