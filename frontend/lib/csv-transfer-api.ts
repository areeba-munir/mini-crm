import { ApiError, apiRequest } from "@/lib/api";
import type {
  CsvEntity,
  CsvImportResult,
  CsvPreviewResult,
} from "@/types/csv-transfer";

const API_URL = process.env.NEXT_PUBLIC_API_URL;

function createCsvFormData(file: File): FormData {
  const formData = new FormData();
  formData.append("upload", file);
  return formData;
}

export function previewCsvImport(
  entity: CsvEntity,
  file: File,
  token: string,
): Promise<CsvPreviewResult> {
  return apiRequest<CsvPreviewResult>(`/${entity}/import/preview`, {
    method: "POST",
    token,
    body: createCsvFormData(file),
  });
}

export function importCsvFile(
  entity: CsvEntity,
  file: File,
  token: string,
): Promise<CsvImportResult> {
  return apiRequest<CsvImportResult>(`/${entity}/import`, {
    method: "POST",
    token,
    body: createCsvFormData(file),
  });
}

export async function downloadCsvExport(
  entity: CsvEntity,
  token: string,
): Promise<void> {
  if (!API_URL) {
    throw new Error("NEXT_PUBLIC_API_URL is not configured");
  }

  const response = await fetch(`${API_URL}/${entity}/export`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const details: unknown = await response.json().catch(() => null);

    let message = "Unable to export CSV.";

    if (
      details &&
      typeof details === "object" &&
      "detail" in details &&
      typeof details.detail === "string"
    ) {
      message = details.detail;
    }

    throw new ApiError(message, response.status, details);
  }

  const blob = await response.blob();
  const downloadUrl = URL.createObjectURL(blob);
  const anchor = document.createElement("a");

  anchor.href = downloadUrl;
  anchor.download = `${entity}.csv`;
  document.body.appendChild(anchor);
  anchor.click();
  anchor.remove();

  URL.revokeObjectURL(downloadUrl);
}
