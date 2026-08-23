"use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { MeetingForm } from "@/components/meetings/meeting-form";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { createMeeting } from "@/lib/meetings-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { MeetingCreateInput } from "@/types/meeting";

export default function NewMeetingPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [companies, setCompanies] = useState<Company[]>(
    [],
  );
  const [contacts, setContacts] = useState<Contact[]>(
    [],
  );
  const [isDataLoading, setIsDataLoading] =
    useState(true);
  const [dataError, setDataError] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadFormData(
      accessToken: string,
    ) {
      try {
        const [
          companyRecords,
          contactRecords,
        ] = await Promise.all([
          listCompanies(accessToken),
          listContacts(accessToken),
        ]);

        if (!cancelled) {
          setCompanies(companyRecords);
          setContacts(contactRecords);
          setIsDataLoading(false);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (
          error instanceof ApiError &&
          error.status === 401
        ) {
          removeAccessToken();
          router.replace("/login");
          return;
        }

        setDataError(
          error instanceof ApiError
            ? error.message
            : "Unable to load the meeting form.",
        );
        setIsDataLoading(false);
      }
    }

    void loadFormData(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

  if (
    isAuthenticationLoading ||
    !user ||
    !token
  ) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError
              ? "text-red-300"
              : "text-slate-400"
          }`}
        >
          {authenticationError ||
            "Loading meeting form..."}
        </p>
      </main>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading companies and contacts...
        </p>
      </AppShell>
    );
  }

  if (dataError) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Meeting form unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleCreateMeeting(
    input: MeetingCreateInput,
  ) {
    if (!token) {
      throw new Error(
        "Authentication token is unavailable.",
      );
    }

    await createMeeting(input, token);
    router.push("/meetings");
  }

  return (
    <AppShell user={user}>
      <section className="mx-auto max-w-3xl">
        <div>
          <p className="text-sm font-medium text-blue-400">
            Meetings
          </p>

          <h1 className="mt-1 text-3xl font-bold">
            Add meeting
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Schedule a meeting with CRM users and
            contacts.
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <MeetingForm
            cancelHref="/meetings"
            companies={companies}
            contacts={contacts}
            currentUserId={user.id}
            onSubmit={handleCreateMeeting}
            submitLabel="Create meeting"
          />
        </div>
      </section>
    </AppShell>
  );
}