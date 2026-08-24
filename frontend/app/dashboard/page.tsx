"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { ApiError } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth-api";
import { getAccessToken, removeAccessToken } from "@/lib/auth-storage";
import { getDashboardSummary } from "@/lib/dashboard-api";
import type { User } from "@/types/auth";
import type { DashboardSummary } from "@/types/dashboard";

const leadStages = ["New", "Contacted", "Qualified", "Won", "Lost"];

type SecondaryMetric = {
  label: string;
  value: string | number;
  danger?: boolean;
};

type MetricCardProps = {
  label: string;
  value: string | number;
  description: string;
  href: string;
  danger?: boolean;
  secondaryMetrics?: SecondaryMetric[];
};

function MetricCard({
  label,
  value,
  description,
  href,
  danger = false,
  secondaryMetrics = [],
}: MetricCardProps) {
  return (
    <Link
      className="group flex h-full flex-col rounded-2xl border border-slate-800 bg-slate-900 p-6 transition hover:-translate-y-0.5 hover:border-slate-700 hover:bg-slate-800/80 focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-500"
      href={href}
    >
      <p className="text-sm font-medium text-slate-400 transition group-hover:text-slate-300">
        {label}
      </p>

      <p
        className={`mt-3 text-3xl font-bold ${
          danger ? "text-red-300" : "text-white"
        }`}
      >
        {value}
      </p>

      <p className="mt-2 text-xs leading-5 text-slate-500">{description}</p>

      {secondaryMetrics.length > 0 && (
        <dl
          className={`mt-5 grid gap-4 border-t border-slate-800 pt-4 ${
            secondaryMetrics.length > 1 ? "grid-cols-2" : "grid-cols-1"
          }`}
        >
          {secondaryMetrics.map((metric) => (
            <div key={metric.label}>
              <dt className="text-xs text-slate-500">{metric.label}</dt>

              <dd
                className={`mt-1 text-lg font-semibold ${
                  metric.danger ? "text-red-300" : "text-slate-200"
                }`}
              >
                {metric.value}
              </dd>
            </div>
          ))}
        </dl>
      )}
    </Link>
  );
}

export default function DashboardPage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();

    if (!token) {
      router.replace("/login");
      return;
    }

    let cancelled = false;

    async function loadDashboard(accessToken: string) {
      try {
        const [currentUser, dashboardSummary] = await Promise.all([
          getCurrentUser(accessToken),
          getDashboardSummary(accessToken),
        ]);

        if (!cancelled) {
          setUser(currentUser);
          setSummary(dashboardSummary);
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

        setErrorMessage("Unable to load your CRM dashboard.");
      }
    }

    void loadDashboard(token);

    return () => {
      cancelled = true;
    };
  }, [router]);

  if (errorMessage) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <section className="max-w-md rounded-2xl border border-red-500/30 bg-slate-900 p-8 text-center">
          <h1 className="text-xl font-bold text-white">
            Dashboard unavailable
          </h1>

          <p className="mt-3 text-sm text-red-300">{errorMessage}</p>

          <button
            className="mt-6 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-500"
            onClick={() => window.location.reload()}
            type="button"
          >
            Try again
          </button>
        </section>
      </main>
    );
  }

  if (!user || !summary) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-400">Loading your CRM dashboard...</p>
      </main>
    );
  }

  const formattedPipelineValue = Number(summary.pipeline_value).toLocaleString(
    "en-US",
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    },
  );

  return (
    <AppShell user={user}>
      <section>
        <p className="text-sm text-slate-400">Welcome back,</p>

        <h1 className="mt-1 text-3xl font-bold">{user.full_name}</h1>

        <p className="mt-2 text-sm text-slate-400">
          Here is the latest overview of your CRM.
        </p>
      </section>

      <section className="mt-8 grid gap-5 sm:grid-cols-2 xl:grid-cols-3">
        <MetricCard
          description="Organizations stored in the CRM"
          href="/companies"
          label="Companies"
          value={summary.total_companies}
        />

        <MetricCard
          description="People stored in the CRM"
          href="/contacts"
          label="Contacts"
          value={summary.total_contacts}
        />

        <MetricCard
          description="All sales opportunities"
          href="/leads"
          label="Leads"
          secondaryMetrics={[
            {
              label: "Active opportunities",
              value: summary.active_opportunities,
            },
          ]}
          value={summary.total_leads}
        />

        <MetricCard
          description="Value of open sales opportunities"
          href="/leads"
          label="Pipeline value"
          value={formattedPipelineValue}
        />

        <MetricCard
          description="Work that still needs attention"
          href="/tasks"
          label="Tasks"
          secondaryMetrics={[
            {
              label: "Completed",
              value: summary.completed_tasks,
            },
            {
              danger: summary.overdue_tasks > 0,
              label: "Overdue",
              value: summary.overdue_tasks,
            },
          ]}
          value={summary.pending_tasks}
        />

        <MetricCard
          description="Scheduled future meetings"
          href="/meetings"
          label="Upcoming meetings"
          value={summary.upcoming_meetings}
        />
      </section>

      <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
        <div>
          <h2 className="text-lg font-semibold">Lead pipeline</h2>

          <p className="mt-1 text-sm text-slate-400">
            Number of leads currently in each stage.
          </p>
        </div>

        <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
          {leadStages.map((stage) => (
            <article
              className="rounded-xl border border-slate-800 bg-slate-950 p-5"
              key={stage}
            >
              <p className="text-sm text-slate-400">{stage}</p>

              <p className="mt-2 text-2xl font-bold">
                {summary.leads_by_stage[stage] ?? 0}
              </p>
            </article>
          ))}
        </div>
      </section>
    </AppShell>
  );
}
