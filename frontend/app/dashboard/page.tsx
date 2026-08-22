 "use client";

import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { ApiError } from "@/lib/api";
import { getCurrentUser } from "@/lib/auth-api";
import {
  getAccessToken,
  removeAccessToken,
} from "@/lib/auth-storage";
import type { User } from "@/types/auth";

export default function DashboardPage() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const token = getAccessToken();

    if (!token) {
      router.replace("/login");
      return;
    }

    let cancelled = false;

    async function loadCurrentUser(
      accessToken: string,
    ) {
      try {
        const currentUser = await getCurrentUser(
          accessToken,
        );

        if (!cancelled) {
          setUser(currentUser);
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

        setErrorMessage(
          "Unable to load your CRM account.",
        );
      }
    }

    void loadCurrentUser(token);

    return () => {
      cancelled = true;
    };
  }, [router]);

  function handleLogout() {
    removeAccessToken();
    router.replace("/login");
  }

  if (errorMessage) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <section className="max-w-md rounded-2xl border border-red-500/30 bg-slate-900 p-8 text-center">
          <h1 className="text-xl font-bold text-white">
            Dashboard unavailable
          </h1>

          <p className="mt-3 text-sm text-red-300">
            {errorMessage}
          </p>

          <button
            className="mt-6 rounded-lg bg-blue-600 px-5 py-3 font-semibold text-white hover:bg-blue-500"
            onClick={() => router.refresh()}
            type="button"
          >
            Try again
          </button>
        </section>
      </main>
    );
  }

  if (!user) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950">
        <p className="text-sm text-slate-400">
          Loading your CRM...
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-slate-950 text-white">
      <header className="border-b border-slate-800 bg-slate-900">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-6 py-5">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
              Mini CRM
            </p>

            <h1 className="mt-1 text-xl font-bold">
              Dashboard
            </h1>
          </div>

          <button
            className="rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800"
            onClick={handleLogout}
            type="button"
          >
            Log out
          </button>
        </div>
      </header>

      <div className="mx-auto max-w-6xl px-6 py-10">
        <section>
          <p className="text-sm text-slate-400">
            Welcome back,
          </p>

          <h2 className="mt-1 text-3xl font-bold">
            {user.full_name}
          </h2>
        </section>

        <section className="mt-8 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 p-6">
          <p className="font-semibold text-emerald-300">
            Authentication successful
          </p>

          <p className="mt-2 text-sm leading-6 text-slate-300">
            The frontend used your saved JWT token to
            request your account from the protected
            backend endpoint.
          </p>
        </section>

        <section className="mt-8 rounded-2xl border border-slate-800 bg-slate-900 p-6">
          <h3 className="text-lg font-semibold">
            Account
          </h3>

          <dl className="mt-5 grid gap-5 sm:grid-cols-2">
            <div>
              <dt className="text-sm text-slate-500">
                Full name
              </dt>

              <dd className="mt-1 text-slate-200">
                {user.full_name}
              </dd>
            </div>

            <div>
              <dt className="text-sm text-slate-500">
                Email
              </dt>

              <dd className="mt-1 text-slate-200">
                {user.email}
              </dd>
            </div>
          </dl>
        </section>
      </div>
    </main>
  );
}