"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { removeAccessToken } from "@/lib/auth-storage";
import { getDashboardSummary } from "@/lib/dashboard-api";
import type { DashboardSummary } from "@/types/dashboard";

const leadStages = ["New", "Contacted", "Qualified", "Won", "Lost"] as const;

const stageBarClasses: Record<(typeof leadStages)[number], string> = {
  New: "bg-sky-500",
  Contacted: "bg-blue-500",
  Qualified: "bg-violet-500",
  Won: "bg-emerald-500",
  Lost: "bg-red-500",
};

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

function formatValue(value: string | number): string {
  const numberValue = Number(value);

  return numberValue.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
}

function formatPercentage(value: string | number): string {
  return `${formatValue(value)}%`;
}

function percentageWidth(value: string | number): number {
  const numericValue = Number(value);

  if (!Number.isFinite(numericValue)) {
    return 0;
  }

  return Math.min(100, Math.max(0, numericValue));
}

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

  const {
    user,
    token,
    isLoading: isAuthenticationLoading,
    errorMessage: authenticationError,
  } = useAuthenticatedUser();

  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [dashboardError, setDashboardError] = useState("");

  useEffect(() => {
    if (!token) {
      return;
    }

    let cancelled = false;

    async function loadDashboard(accessToken: string) {
      try {
        const dashboardSummary = await getDashboardSummary(accessToken);

        if (!cancelled) {
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

        setDashboardError(
          error instanceof ApiError
            ? error.message
            : "Unable to load your CRM dashboard.",
        );
      }
    }

    void loadDashboard(token);

    return () => {
      cancelled = true;
    };
  }, [router, token]);

  if (isAuthenticationLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            authenticationError ? "text-red-300" : "text-slate-400"
          }`}
        >
          {authenticationError || "Loading your CRM dashboard..."}
        </p>
      </main>
    );
  }

  if (dashboardError) {
    return (
      <AppShell user={user}>
        <section className="mx-auto max-w-lg rounded-2xl border border-red-500/30 bg-red-500/10 p-8 text-center">
          <h1 className="text-xl font-bold text-red-200">
            Dashboard unavailable
          </h1>

          <p className="mt-3 text-sm text-red-300">{dashboardError}</p>

          <button
            className="mt-6 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white transition hover:bg-blue-500"
            onClick={() => window.location.reload()}
            type="button"
          >
            Try again
          </button>
        </section>
      </AppShell>
    );
  }

  if (!summary) {
    return (
      <AppShell user={user}>
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-10 text-center">
          <p className="text-sm text-slate-400">Calculating CRM analytics...</p>
        </section>
      </AppShell>
    );
  }

  const maximumStageCount = Math.max(
    1,
    ...leadStages.map((stage) => summary.leads_by_stage[stage] ?? 0),
  );

  const taskCompletionWidth = percentageWidth(summary.task_completion_rate);

  return (
    <AppShell user={user}>
      <section>
        <p className="text-sm text-slate-400">Welcome back,</p>

        <h1 className="mt-1 text-3xl font-bold">{user.full_name}</h1>

        <p className="mt-2 text-sm text-slate-400">
          Here is the latest performance overview of your CRM.
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
              label: "Active",
              value: summary.active_opportunities,
            },
            {
              label: "Last 30 days",
              value: summary.leads_created_last_30_days,
            },
          ]}
          value={summary.total_leads}
        />

        <MetricCard
          description="Total estimated value of open opportunities"
          href="/leads"
          label="Open pipeline"
          secondaryMetrics={[
            {
              label: "Average open deal",
              value: formatValue(summary.average_open_deal_value),
            },
          ]}
          value={formatValue(summary.pipeline_value)}
        />

        <MetricCard
          description="Work that still needs attention"
          href="/tasks"
          label="Pending tasks"
          secondaryMetrics={[
            {
              label: "Due in 7 days",
              value: summary.tasks_due_next_7_days,
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
          secondaryMetrics={[
            {
              label: "Next 7 days",
              value: summary.meetings_next_7_days,
            },
          ]}
          value={summary.upcoming_meetings}
        />
      </section>

      <section className="mt-8">
        <div>
          <p className="text-sm font-medium text-blue-400">Revenue analytics</p>

          <h2 className="mt-1 text-2xl font-bold">Sales performance</h2>

          <p className="mt-2 text-sm text-slate-400">
            Compare open-pipeline potential, weighted forecasts, and closed
            results.
          </p>
        </div>

        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
          <article className="rounded-2xl border border-blue-500/20 bg-blue-500/5 p-5">
            <p className="text-sm text-blue-300">Weighted pipeline</p>

            <p className="mt-3 text-2xl font-bold">
              {formatValue(summary.weighted_pipeline_value)}
            </p>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              New 10%, Contacted 30%, and Qualified 60%.
            </p>
          </article>

          <article className="rounded-2xl border border-emerald-500/20 bg-emerald-500/5 p-5">
            <p className="text-sm text-emerald-300">Won value</p>

            <p className="mt-3 text-2xl font-bold text-emerald-200">
              {formatValue(summary.won_value)}
            </p>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Estimated value of opportunities marked Won.
            </p>
          </article>

          <article className="rounded-2xl border border-violet-500/20 bg-violet-500/5 p-5">
            <p className="text-sm text-violet-300">Average open deal</p>

            <p className="mt-3 text-2xl font-bold text-violet-200">
              {formatValue(summary.average_open_deal_value)}
            </p>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Open pipeline divided by active opportunities.
            </p>
          </article>

          <article className="rounded-2xl border border-amber-500/20 bg-amber-500/5 p-5">
            <p className="text-sm text-amber-300">Closed-lead win rate</p>

            <p className="mt-3 text-2xl font-bold text-amber-200">
              {formatPercentage(summary.win_rate)}
            </p>

            <p className="mt-2 text-xs leading-5 text-slate-500">
              Won opportunities divided by all closed opportunities.
            </p>
          </article>
        </div>
      </section>

      <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
        <div className="flex flex-col gap-2 sm:flex-row sm:items-end sm:justify-between">
          <div>
            <p className="text-sm font-medium text-blue-400">
              Pipeline distribution
            </p>

            <h2 className="mt-1 text-xl font-semibold">Leads by stage</h2>

            <p className="mt-2 text-sm text-slate-400">
              Relative lead volume and estimated value at every stage.
            </p>
          </div>

          <Link
            className="text-sm font-medium text-blue-400 transition hover:text-blue-300"
            href="/leads"
          >
            View all leads
          </Link>
        </div>

        <div className="mt-7 space-y-5">
          {leadStages.map((stage) => {
            const stageCount = summary.leads_by_stage[stage] ?? 0;
            const stageValue = summary.pipeline_value_by_stage[stage] ?? "0";
            const width = (stageCount / maximumStageCount) * 100;

            return (
              <article key={stage}>
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <div className="flex items-center gap-3">
                    <span
                      className={`h-3 w-3 rounded-full ${stageBarClasses[stage]}`}
                    />

                    <p className="font-medium text-slate-200">{stage}</p>
                  </div>

                  <div className="flex items-center gap-4 text-sm">
                    <span className="text-slate-400">
                      {stageCount} {stageCount === 1 ? "lead" : "leads"}
                    </span>

                    <span className="min-w-24 text-right font-medium text-slate-200">
                      {formatValue(stageValue)}
                    </span>
                  </div>
                </div>

                <div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-950">
                  <div
                    className={`h-full rounded-full transition-all ${stageBarClasses[stage]}`}
                    style={{
                      width: `${width}%`,
                    }}
                  />
                </div>
              </article>
            );
          })}
        </div>
      </section>

      <section className="mt-8 grid gap-6 xl:grid-cols-2">
        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-medium text-blue-400">Execution</p>

              <h2 className="mt-1 text-xl font-semibold">Task completion</h2>
            </div>

            <p className="text-2xl font-bold">
              {formatPercentage(summary.task_completion_rate)}
            </p>
          </div>

          <div className="mt-6 h-3 overflow-hidden rounded-full bg-slate-950">
            <div
              className="h-full rounded-full bg-emerald-500 transition-all"
              style={{
                width: `${taskCompletionWidth}%`,
              }}
            />
          </div>

          <dl className="mt-6 grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <dt className="text-xs text-slate-500">Pending</dt>
              <dd className="mt-1 text-xl font-semibold">
                {summary.pending_tasks}
              </dd>
            </div>

            <div>
              <dt className="text-xs text-slate-500">Completed</dt>
              <dd className="mt-1 text-xl font-semibold text-emerald-300">
                {summary.completed_tasks}
              </dd>
            </div>

            <div>
              <dt className="text-xs text-slate-500">Due soon</dt>
              <dd className="mt-1 text-xl font-semibold text-amber-300">
                {summary.tasks_due_next_7_days}
              </dd>
            </div>

            <div>
              <dt className="text-xs text-slate-500">Overdue</dt>
              <dd
                className={`mt-1 text-xl font-semibold ${
                  summary.overdue_tasks > 0 ? "text-red-300" : "text-slate-200"
                }`}
              >
                {summary.overdue_tasks}
              </dd>
            </div>
          </dl>
        </article>

        <article className="rounded-2xl border border-slate-800 bg-slate-900 p-5 sm:p-6">
          <p className="text-sm font-medium text-blue-400">
            Near-term activity
          </p>

          <h2 className="mt-1 text-xl font-semibold">Next steps</h2>

          <div className="mt-6 grid gap-4 sm:grid-cols-3">
            <Link
              className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition hover:border-slate-700"
              href="/leads"
            >
              <p className="text-xs text-slate-500">New leads, 30 days</p>

              <p className="mt-2 text-2xl font-bold text-blue-300">
                {summary.leads_created_last_30_days}
              </p>
            </Link>

            <Link
              className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition hover:border-slate-700"
              href="/tasks"
            >
              <p className="text-xs text-slate-500">Tasks due, 7 days</p>

              <p className="mt-2 text-2xl font-bold text-amber-300">
                {summary.tasks_due_next_7_days}
              </p>
            </Link>

            <Link
              className="rounded-xl border border-slate-800 bg-slate-950 p-4 transition hover:border-slate-700"
              href="/meetings"
            >
              <p className="text-xs text-slate-500">Meetings, 7 days</p>

              <p className="mt-2 text-2xl font-bold text-violet-300">
                {summary.meetings_next_7_days}
              </p>
            </Link>
          </div>
        </article>
      </section>
    </AppShell>
  );
}
