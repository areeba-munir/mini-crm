"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { DeleteMeetingDialog } from "@/components/meetings/delete-meeting-dialog";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { listCompanies } from "@/lib/companies-api";
import { listContacts } from "@/lib/contacts-api";
import { deleteMeeting, listMeetings } from "@/lib/meetings-api";
import type { Company } from "@/types/company";
import type { Contact } from "@/types/contact";
import type { Meeting, MeetingStatus } from "@/types/meeting";

const meetingStatuses: MeetingStatus[] = [
  "Scheduled",
  "Completed",
  "Cancelled",
];

const emptyValue = "\u2014";

function getStatusClassName(status: MeetingStatus) {
  switch (status) {
    case "Completed":
      return "bg-emerald-500/10 text-emerald-300";
    case "Cancelled":
      return "bg-red-500/10 text-red-300";
    default:
      return "bg-blue-500/10 text-blue-300";
  }
}

export default function MeetingsPage() {
  const router = useRouter();

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [meetings, setMeetings] = useState<Meeting[]>([]);
  const [companies, setCompanies] = useState<Company[]>([]);
  const [contacts, setContacts] = useState<Contact[]>([]);
  const [selectedStatus, setSelectedStatus] = useState<MeetingStatus | "">("");
  const [isDataLoading, setIsDataLoading] = useState(true);
  const [dataError, setDataError] = useState("");

  const [meetingToDelete, setMeetingToDelete] = useState<Meeting | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadMeetingData(accessToken: string) {
      try {
        const [meetingRecords, companyRecords, contactRecords] =
          await Promise.all([
            listMeetings(accessToken),
            listCompanies(accessToken),
            listContacts(accessToken),
          ]);

        if (!cancelled) {
          setMeetings(meetingRecords);
          setCompanies(companyRecords);
          setContacts(contactRecords);
          setIsDataLoading(false);
        }
      } catch (error) {
        if (cancelled) {
          return;
        }

        if (error instanceof ApiError && error.status === 401) {
          removeAccessToken();
          router.replace("/login");
          return;
        }

        setDataError(
          error instanceof ApiError
            ? error.message
            : "Unable to load meetings.",
        );
        setIsDataLoading(false);
      }
    }

    void loadMeetingData(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

  const companyNamesById = new Map(
    companies.map((company) => [company.id, company.name]),
  );

  const contactNamesById = new Map(
    contacts.map((contact) => [
      contact.id,
      [contact.first_name, contact.last_name].filter(Boolean).join(" "),
    ]),
  );

  const filteredMeetings = selectedStatus
    ? meetings.filter((meeting) => meeting.status === selectedStatus)
    : meetings;

  function getParticipantNames(meeting: Meeting) {
    return meeting.contact_participant_ids
      .map(
        (contactId) =>
          contactNamesById.get(contactId) ?? `Contact #${contactId}`,
      )
      .join(", ");
  }

  function openDeleteDialog(meeting: Meeting) {
    setDeleteError("");
    setMeetingToDelete(meeting);
  }

  function closeDeleteDialog() {
    if (isDeleting) {
      return;
    }

    setDeleteError("");
    setMeetingToDelete(null);
  }

  async function handleDeleteMeeting() {
    if (!token || !meetingToDelete) {
      return;
    }

    setIsDeleting(true);
    setDeleteError("");

    try {
      await deleteMeeting(meetingToDelete.id, token);

      setMeetings((currentMeetings) =>
        currentMeetings.filter((meeting) => meeting.id !== meetingToDelete.id),
      );

      setMeetingToDelete(null);
    } catch (error) {
      if (error instanceof ApiError && error.status === 401) {
        removeAccessToken();
        router.replace("/login");
        return;
      }

      setDeleteError(
        error instanceof ApiError
          ? error.message
          : "Unable to delete the meeting.",
      );
    } finally {
      setIsDeleting(false);
    }
  }

  if (isAuthenticationLoading || !user || !token) {
    if (authenticationError) {
      return (
        <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
          <p className="text-sm text-red-300">{authenticationError}</p>
        </main>
      );
    }

    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-400">Loading meetings...</p>
      </main>
    );
  }

  return (
    <AppShell user={user}>
      <section className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
        <div>
          <p className="text-sm font-medium text-blue-400">Schedule</p>

          <h1 className="mt-1 text-3xl font-bold">Meetings</h1>

          <p className="mt-2 text-sm text-slate-400">
            Manage meetings with CRM users and contacts.
          </p>
        </div>

        <div className="flex flex-col gap-3 sm:flex-row sm:items-end">
          <label className="text-sm text-slate-300">
            <span className="mb-2 block">Status</span>

            <select
              className="min-w-44 rounded-lg border border-slate-700 bg-slate-900 px-4 py-3 text-sm text-white outline-none focus:border-blue-500"
              onChange={(event) =>
                setSelectedStatus(event.target.value as MeetingStatus | "")
              }
              value={selectedStatus}
            >
              <option value="">All statuses</option>

              {meetingStatuses.map((status) => (
                <option key={status} value={status}>
                  {status}
                </option>
              ))}
            </select>
          </label>

          <Link
            className="rounded-lg bg-blue-600 px-5 py-3 text-center text-sm font-semibold text-white transition hover:bg-blue-500"
            href="/meetings/new"
          >
            Add meeting
          </Link>
        </div>
      </section>

      <p className="mt-5 text-sm text-slate-400">
        Total meetings:{" "}
        <span className="font-semibold text-white">
          {filteredMeetings.length}
        </span>
      </p>

      {isDataLoading && (
        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-8 text-center">
          <p className="text-sm text-slate-400">Loading meeting records...</p>
        </section>
      )}

      {!isDataLoading && dataError && (
        <section className="mt-8 rounded-2xl border border-red-500/30 bg-red-500/10 p-6">
          <h2 className="font-semibold text-red-300">Meetings unavailable</h2>

          <p className="mt-2 text-sm text-red-200">{dataError}</p>
        </section>
      )}

      {!isDataLoading && !dataError && filteredMeetings.length === 0 && (
        <section className="mt-8 rounded-2xl border border-dashed border-slate-700 bg-slate-900 p-10 text-center">
          <h2 className="text-lg font-semibold">No meetings found</h2>

          <p className="mt-2 text-sm text-slate-400">
            Create a meeting or select a different status.
          </p>

          <Link
            className="mt-5 inline-flex rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500"
            href="/meetings/new"
          >
            Schedule a meeting
          </Link>
        </section>
      )}

      {!isDataLoading && !dataError && filteredMeetings.length > 0 && (
        <section className="mt-8">
          <div className="grid gap-4 md:hidden">
            {filteredMeetings.map((meeting) => {
              const participantNames = getParticipantNames(meeting);

              return (
                <article
                  className="rounded-2xl border border-slate-800 bg-slate-900 p-5"
                  key={meeting.id}
                >
                  <div className="flex items-start justify-between gap-4">
                    <div className="min-w-0">
                      <h2 className="truncate font-semibold text-white">
                        {meeting.title}
                      </h2>

                      <p className="mt-1 text-xs text-slate-500">
                        Organizer:{" "}
                        {meeting.organizer_id === user.id
                          ? "You"
                          : `User #${meeting.organizer_id}`}
                      </p>
                    </div>

                    <span
                      className={`shrink-0 rounded-full px-3 py-1 text-xs font-medium ${getStatusClassName(
                        meeting.status,
                      )}`}
                    >
                      {meeting.status}
                    </span>
                  </div>

                  <dl className="mt-5 grid gap-4 text-sm sm:grid-cols-2">
                    <div>
                      <dt className="text-xs text-slate-500">Starts</dt>

                      <dd className="mt-1 text-slate-300">
                        {new Date(meeting.starts_at).toLocaleString()}
                      </dd>
                    </div>

                    <div>
                      <dt className="text-xs text-slate-500">Ends</dt>

                      <dd className="mt-1 text-slate-300">
                        {new Date(meeting.ends_at).toLocaleString()}
                      </dd>
                    </div>

                    <div>
                      <dt className="text-xs text-slate-500">Company</dt>

                      <dd className="mt-1 text-slate-300">
                        {meeting.company_id === null
                          ? emptyValue
                          : (companyNamesById.get(meeting.company_id) ??
                            "Unknown company")}
                      </dd>
                    </div>

                    <div>
                      <dt className="text-xs text-slate-500">
                        Contact participants
                      </dt>

                      <dd className="mt-1 text-slate-300">
                        {participantNames || emptyValue}
                      </dd>
                    </div>
                  </dl>

                  <div className="mt-5 border-t border-slate-800 pt-4">
                    {meeting.meeting_link ? (
                      <a
                        className="text-sm font-medium text-blue-400 hover:text-blue-300"
                        href={meeting.meeting_link}
                        rel="noreferrer"
                        target="_blank"
                      >
                        Join meeting
                      </a>
                    ) : (
                      <p className="text-sm text-slate-400">
                        {meeting.location ?? emptyValue}
                      </p>
                    )}

                    <div className="mt-4 flex justify-end gap-4">
                      <Link
                        className="text-sm font-semibold text-blue-400 transition hover:text-blue-300"
                        href={`/meetings/${meeting.id}/edit`}
                      >
                        Edit
                      </Link>

                      <button
                        className="text-sm font-semibold text-red-400 transition hover:text-red-300"
                        onClick={() => openDeleteDialog(meeting)}
                        type="button"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                </article>
              );
            })}
          </div>

          <div className="hidden overflow-hidden rounded-2xl border border-slate-800 bg-slate-900 md:block">
            <table className="w-full table-fixed text-left">
              <thead className="border-b border-slate-800">
                <tr className="text-xs uppercase tracking-wider text-slate-500">
                  <th className="w-[22%] px-4 py-4 font-medium">Meeting</th>

                  <th className="w-[14%] px-4 py-4 font-medium">Status</th>

                  <th className="w-[22%] px-4 py-4 font-medium">Starts</th>

                  <th className="w-[18%] px-4 py-4 font-medium">Company</th>

                  <th className="hidden px-4 py-4 font-medium 2xl:table-cell">
                    Participants
                  </th>

                  <th className="hidden w-[14%] px-4 py-4 font-medium xl:table-cell">
                    Location
                  </th>

                  <th className="w-[24%] px-4 py-4 text-right font-medium xl:w-[14%]">
                    Actions
                  </th>
                </tr>
              </thead>

              <tbody className="divide-y divide-slate-800">
                {filteredMeetings.map((meeting) => {
                  const participantNames = getParticipantNames(meeting);

                  return (
                    <tr
                      className="transition hover:bg-slate-800/50"
                      key={meeting.id}
                    >
                      <td className="px-4 py-4">
                        <p className="truncate font-medium text-white">
                          {meeting.title}
                        </p>

                        <p className="mt-1 text-xs text-slate-500">
                          Organizer:{" "}
                          {meeting.organizer_id === user.id
                            ? "You"
                            : `User #${meeting.organizer_id}`}
                        </p>
                      </td>

                      <td className="px-4 py-4">
                        <span
                          className={`inline-flex rounded-full px-3 py-1 text-xs font-medium ${getStatusClassName(
                            meeting.status,
                          )}`}
                        >
                          {meeting.status}
                        </span>
                      </td>

                      <td className="px-4 py-4 text-sm text-slate-300">
                        <p>{new Date(meeting.starts_at).toLocaleString()}</p>

                        <p className="mt-1 text-xs text-slate-500">
                          Ends {new Date(meeting.ends_at).toLocaleString()}
                        </p>
                      </td>

                      <td className="truncate px-4 py-4 text-sm text-slate-300">
                        {meeting.company_id === null
                          ? emptyValue
                          : (companyNamesById.get(meeting.company_id) ??
                            "Unknown company")}
                      </td>

                      <td className="hidden truncate px-4 py-4 text-sm text-slate-300 2xl:table-cell">
                        {participantNames || emptyValue}
                      </td>

                      <td className="hidden truncate px-4 py-4 text-sm text-slate-300 xl:table-cell">
                        {meeting.meeting_link ? (
                          <a
                            className="font-medium text-blue-400 hover:text-blue-300"
                            href={meeting.meeting_link}
                            rel="noreferrer"
                            target="_blank"
                          >
                            Join meeting
                          </a>
                        ) : (
                          (meeting.location ?? emptyValue)
                        )}
                      </td>

                      <td className="px-4 py-4">
                        <div className="flex justify-end gap-3">
                          <Link
                            className="text-sm font-semibold text-blue-400 transition hover:text-blue-300"
                            href={`/meetings/${meeting.id}/edit`}
                          >
                            Edit
                          </Link>

                          <button
                            className="text-sm font-semibold text-red-400 transition hover:text-red-300"
                            onClick={() => openDeleteDialog(meeting)}
                            type="button"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {meetingToDelete && (
        <DeleteMeetingDialog
          errorMessage={deleteError}
          isDeleting={isDeleting}
          meetingTitle={meetingToDelete.title}
          onCancel={closeDeleteDialog}
          onConfirm={handleDeleteMeeting}
        />
      )}
    </AppShell>
  );
}
