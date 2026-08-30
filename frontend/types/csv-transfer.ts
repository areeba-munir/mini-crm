export const csvEntities = ["companies", "contacts", "leads"] as const;

export type CsvEntity = (typeof csvEntities)[number];

export type CsvRowPreview = {
  row_number: number;
  values: Record<string, string | null>;
  errors: string[];
};

export type CsvPreviewResult = {
  entity: CsvEntity;
  columns: string[];
  total_rows: number;
  valid_rows: number;
  invalid_rows: number;
  can_import: boolean;
  rows: CsvRowPreview[];
};

export type CsvImportResult = {
  imported_count: number;
  preview: CsvPreviewResult;
};

export const csvEntityLabels: Record<CsvEntity, string> = {
  companies: "Companies",
  contacts: "Contacts",
  leads: "Leads",
};
