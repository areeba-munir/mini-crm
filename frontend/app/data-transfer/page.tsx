"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import {
  downloadCsvExport,
  importCsvFile,
  previewCsvImport,
} from "@/lib/csv-transfer-api";
import {
  csvEntities,
  csvEntityLabels,
  type CsvEntity,
  type CsvPreviewResult,
} from "@/types/csv-transfer";

type Operation = "exporting" | "previewing" | "importing" | null;

const MAX_FILE_SIZE_BYTES = 2 * 1024 * 1024;

export default function DataTransferPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [entity, setEntity] = useState<CsvEntity>("companies");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<CsvPreviewResult | null>(null);
  const [operation, setOperation] = useState<Operation>(null);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");
  const [fileInputKey, setFileInputKey] = useState(0);

  const canManageData = user?.role === "Admin" || user?.role === "Manager";

  const isBusy = operation !== null;

  function handleRequestError(error: unknown, fallbackMessage: string) {
    if (error instanceof ApiError && error.status === 401) {
      removeAccessToken();
      router.replace("/login");
      return;
    }

    setErrorMessage(
      error instanceof ApiError ? error.message : fallbackMessage,
    );
  }

  function resetTransferState() {
    setSelectedFile(null);
    setPreview(null);
    setErrorMessage("");
    setSuccessMessage("");
    setFileInputKey((currentKey) => currentKey + 1);
  }

  function handleEntityChange(nextEntity: CsvEntity) {
    setEntity(nextEntity);
    resetTransferState();
  }

  function handleFileChange(file: File | null) {
    setPreview(null);
    setErrorMessage("");
    setSuccessMessage("");

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!file.name.toLowerCase().endsWith(".csv")) {
      setSelectedFile(null);
      setErrorMessage("Select a file with the .csv extension.");
      setFileInputKey((currentKey) => currentKey + 1);
      return;
    }

    if (file.size > MAX_FILE_SIZE_BYTES) {
      setSelectedFile(null);
      setErrorMessage("The CSV file must not exceed 2 MB.");
      setFileInputKey((currentKey) => currentKey + 1);
      return;
    }

    setSelectedFile(file);
  }

  async function handleExport() {
    if (!token) {
      return;
    }

    setOperation("exporting");
    setErrorMessage("");
    setSuccessMessage("");

    try {
      await downloadCsvExport(entity, token);

      setSuccessMessage(`${csvEntityLabels[entity]} CSV downloaded.`);
    } catch (error) {
      handleRequestError(error, "Unable to export CSV.");
    } finally {
      setOperation(null);
    }
  }

  async function handlePreview() {
    if (!token || !selectedFile) {
      return;
    }

    setOperation("previewing");
    setPreview(null);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const result = await previewCsvImport(entity, selectedFile, token);

      setPreview(result);
    } catch (error) {
      handleRequestError(error, "Unable to preview the CSV file.");
    } finally {
      setOperation(null);
    }
  }

  async function handleImport() {
    if (!token || !selectedFile || !preview?.can_import) {
      return;
    }

    setOperation("importing");
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const result = await importCsvFile(entity, selectedFile, token);

      if (!result.preview.can_import) {
        setPreview(result.preview);
        setErrorMessage(
          "The data changed during validation. Review the updated preview.",
        );
        return;
      }

      setSuccessMessage(
        `${result.imported_count} ${
          result.imported_count === 1 ? "record" : "records"
        } imported successfully.`,
      );
      setSelectedFile(null);
      setPreview(null);
      setFileInputKey((currentKey) => currentKey + 1);
    } catch (error) {
      handleRequestError(error, "Unable to import the CSV file.");
    } finally {
      setOperation(null);
    }
  }

  if (isAuthenticationLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError ? "text-red-300" : "text-slate-400"
          }`}
        >
          {authenticationError || "Loading data transfer..."}
        </p>
      </main>
    );
  }

  if (!canManageData) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Manager access required
          </h1>

          <p className="mt-2 text-sm text-red-200">
            You do not have permission to import or export CRM data.
          </p>
        </section>
      </AppShell>
    );
  }

  return (
    <AppShell user={user}>
      <section>
        <p className="text-sm font-medium text-blue-400">Data management</p>

        <h1 className="mt-1 text-3xl font-bold">CSV data transfer</h1>

        <p className="mt-2 max-w-3xl text-sm text-slate-400">
          Export CRM records or validate and import up to 1,000 rows at a time.
          Imports are transactional, so no rows are saved when validation errors
          exist.
        </p>
      </section>

      <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
        <label
          className="block text-sm font-medium text-slate-300"
          htmlFor="csv-entity"
        >
          Record type
        </label>

        <select
          className="mt-2 w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none focus:border-blue-500 sm:max-w-sm"
          disabled={isBusy}
          id="csv-entity"
          onChange={(event) =>
            handleEntityChange(event.target.value as CsvEntity)
          }
          value={entity}
        >
          {csvEntities.map((csvEntity) => (
            <option key={csvEntity} value={csvEntity}>
              {csvEntityLabels[csvEntity]}
            </option>
          ))}
        </select>
      </section>

      {(errorMessage || successMessage) && (
        <section
          className={`mt-6 rounded-2xl border p-5 ${
            errorMessage
              ? "border-red-500/30 bg-red-500/10"
              : "border-emerald-500/30 bg-emerald-500/10"
          }`}
        >
          <p
            className={`text-sm ${
              errorMessage ? "text-red-200" : "text-emerald-200"
            }`}
          >
            {errorMessage || successMessage}
          </p>
        </section>
      )}

      <section className="mt-6 grid gap-6 xl:grid-cols-2">
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
          <p className="text-sm font-medium text-blue-400">Export</p>

          <h2 className="mt-1 text-xl font-semibold">
            Download {csvEntityLabels[entity]}
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Download the current records as a UTF-8 CSV file that can be edited
            and imported again.
          </p>

          <button
            className="mt-6 rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isBusy}
            onClick={() => void handleExport()}
            type="button"
          >
            {operation === "exporting"
              ? "Preparing download..."
              : `Export ${csvEntityLabels[entity]}`}
          </button>
        </article>

        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
          <p className="text-sm font-medium text-blue-400">Import</p>

          <h2 className="mt-1 text-xl font-semibold">
            Upload {csvEntityLabels[entity]}
          </h2>

          <p className="mt-2 text-sm text-slate-400">
            Select a CSV file no larger than 2 MB. Preview validation is
            required before importing.
          </p>

          <label
            className="mt-6 block text-sm font-medium text-slate-300"
            htmlFor="csv-upload"
          >
            CSV file
          </label>

          <input
            accept=".csv,text/csv"
            className="mt-2 block w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-3 text-sm text-slate-300 file:mr-4 file:rounded-md file:border-0 file:bg-blue-600 file:px-4 file:py-2 file:font-medium file:text-white hover:file:bg-blue-500"
            disabled={isBusy}
            id="csv-upload"
            key={fileInputKey}
            onChange={(event) =>
              handleFileChange(event.target.files?.[0] ?? null)
            }
            type="file"
          />

          {selectedFile && (
            <p className="mt-3 text-xs text-slate-500">
              Selected: {selectedFile.name} (
              {Math.max(1, Math.ceil(selectedFile.size / 1024))} KB)
            </p>
          )}

          <button
            className="mt-5 rounded-lg border border-blue-500 px-5 py-3 text-sm font-semibold text-blue-300 transition hover:bg-blue-500/10 disabled:cursor-not-allowed disabled:opacity-50"
            disabled={isBusy || !selectedFile}
            onClick={() => void handlePreview()}
            type="button"
          >
            {operation === "previewing" ? "Validating..." : "Preview import"}
          </button>
        </article>
      </section>

      {preview && (
        <section className="mt-6 rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
          <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
            <div>
              <p className="text-sm font-medium text-blue-400">
                Validation result
              </p>

              <h2 className="mt-1 text-xl font-semibold">
                {preview.can_import ? "Ready to import" : "Fix CSV errors"}
              </h2>

              <p className="mt-2 text-sm text-slate-400">
                {preview.can_import
                  ? "Every row passed validation."
                  : "No records will be imported until every row is valid."}
              </p>
            </div>

            <button
              className="rounded-lg bg-emerald-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-50"
              disabled={isBusy || !preview.can_import || !selectedFile}
              onClick={() => void handleImport()}
              type="button"
            >
              {operation === "importing" ? "Importing..." : "Confirm import"}
            </button>
          </div>

          <div className="mt-6 grid gap-3 sm:grid-cols-3">
            <article className="rounded-xl border border-slate-800 bg-slate-950 p-4">
              <p className="text-xs text-slate-500">Total rows</p>
              <p className="mt-2 text-2xl font-bold">{preview.total_rows}</p>
            </article>

            <article className="rounded-xl border border-emerald-500/20 bg-emerald-500/5 p-4">
              <p className="text-xs text-emerald-300">Valid rows</p>
              <p className="mt-2 text-2xl font-bold text-emerald-200">
                {preview.valid_rows}
              </p>
            </article>

            <article className="rounded-xl border border-red-500/20 bg-red-500/5 p-4">
              <p className="text-xs text-red-300">Invalid rows</p>
              <p className="mt-2 text-2xl font-bold text-red-200">
                {preview.invalid_rows}
              </p>
            </article>
          </div>

          <div className="mt-6 max-h-[32rem] overflow-auto rounded-xl border border-slate-800">
            <table className="min-w-full divide-y divide-slate-800 text-left text-sm">
              <thead className="sticky top-0 bg-slate-950">
                <tr>
                  <th className="px-4 py-3 font-medium text-slate-400">Row</th>

                  {preview.columns.map((column) => (
                    <th
                      className="whitespace-nowrap px-4 py-3 font-medium text-slate-400"
                      key={column}
                    >
                      {column}
                    </th>
                  ))}

                  <th className="px-4 py-3 font-medium text-slate-400">
                    Errors
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800">
                {preview.rows.map((row) => (
                  <tr
                    className={row.errors.length > 0 ? "bg-red-500/5" : ""}
                    key={row.row_number}
                  >
                    <td className="whitespace-nowrap px-4 py-3 text-slate-400">
                      {row.row_number}
                    </td>

                    {preview.columns.map((column) => (
                      <td
                        className="max-w-xs px-4 py-3 text-slate-300"
                        key={column}
                      >
                        <span className="line-clamp-3">
                          {row.values[column] ?? "—"}
                        </span>
                      </td>
                    ))}

                    <td className="min-w-64 px-4 py-3">
                      {row.errors.length > 0 ? (
                        <ul className="space-y-1 text-xs text-red-300">
                          {row.errors.map((rowError) => (
                            <li key={rowError}>{rowError}</li>
                          ))}
                        </ul>
                      ) : (
                        <span className="text-xs text-emerald-300">Valid</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}
    </AppShell>
  );
}
