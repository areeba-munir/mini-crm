"use client";

import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { MeetingForm } from "@/components/meetings/meeting-form";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import {
  getMeeting,
  updateMeeting,
} from "@/lib/meetings-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type {
  Meeting,
  MeetingCreateInput,
} from "@/types/meeting";

export default function EditMeetingPage() {
  const params = useParams<{
    meetingId: string;
  }>();
  const router = useRouter();

  const meetingId = Number(params.meetingId);

  const isMeetingIdValid =
    Number.isInteger(meetingId) && meetingId >= 1;

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [meeting, setMeeting] =
    useState<Meeting | null>(null);
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
    if (!token || !isMeetingIdValid) {
      return;
    }

    let cancelled = false;

    async function loadMeetingData(
      accessToken: string,
    ) {
      try {
        const [
          meetingRecord,
          companyRecords,
          contactRecords,
        ] = await Promise.all([
          getMeeting(meetingId, accessToken),
          listCompanies(accessToken),
          listContacts(accessToken),
        ]);

        if (!cancelled) {
          setMeeting(meetingRecord);
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
            : "Unable to load the meeting.",
        );
        setIsDataLoading(false);
      }
    }

    void loadMeetingData(token);

    return () => {
      cancelled = true;
    };
  }, [
    isMeetingIdValid,
    meetingId,
    router,
    token,
  ]);

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
            "Loading meeting editor..."}
        </p>
      </main>
    );
  }

  if (!isMeetingIdValid) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Invalid meeting
          </h1>

          <p className="mt-2 text-sm text-red-200">
            The meeting ID must be a positive number.
          </p>
        </section>
      </AppShell>
    );
  }

  if (isDataLoading) {
    return (
      <AppShell user={user}>
        <p className="text-sm text-slate-400">
          Loading meeting...
        </p>
      </AppShell>
    );
  }

  if (dataError || !meeting) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h1 className="text-lg font-semibold text-red-300">
            Meeting unavailable
          </h1>

          <p className="mt-2 text-sm text-red-200">
            {dataError ||
              "The meeting could not be found."}
          </p>
        </section>
      </AppShell>
    );
  }

  async function handleUpdateMeeting(
    input: MeetingCreateInput,
  ) {
    if (!token || !meeting) {
      throw new Error(
        "Meeting or authentication data is unavailable.",
      );
    }

    await updateMeeting(
      meeting.id,
      {
        ...input,
        organizer_id: meeting.organizer_id,
      },
      token,
    );

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
            Edit meeting
          </h1>

          <p className="mt-2 text-sm text-slate-400">
            Update the meeting{" "}
            <span className="font-medium text-slate-200">
              {meeting.title}
            </span>
            .
          </p>
        </div>

        <div className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <MeetingForm
            cancelHref="/meetings"
            companies={companies}
            contacts={contacts}
            currentUserId={user.id}
            initialValues={{
              title: meeting.title,
              description: meeting.description,
              starts_at: meeting.starts_at,
              ends_at: meeting.ends_at,
              location: meeting.location,
              meeting_link: meeting.meeting_link,
              notes: meeting.notes,
              status: meeting.status,
              organizer_id: meeting.organizer_id,
              company_id: meeting.company_id,
              user_participant_ids:
                meeting.user_participant_ids,
              contact_participant_ids:
                meeting.contact_participant_ids,
            }}
            onSubmit={handleUpdateMeeting}
            submitLabel="Save changes"
          />
        </div>
      </section>
    </AppShell>
  );
}