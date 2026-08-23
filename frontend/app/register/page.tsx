"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { ApiError } from "@/lib/api";
import { loginUser, registerUser } from "@/lib/auth-api";
import { saveAccessToken } from "@/lib/auth-storage";

export default function RegisterPage() {
  const router = useRouter();

  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setErrorMessage("");

    const normalizedFullName = fullName.trim();
    const normalizedEmail = email.trim().toLowerCase();

    if (password !== passwordConfirmation) {
      setErrorMessage("Passwords do not match.");
      return;
    }

    setIsSubmitting(true);

    try {
      await registerUser({
        full_name: normalizedFullName,
        email: normalizedEmail,
        password,
      });

      const tokenResponse = await loginUser({
        email: normalizedEmail,
        password,
      });

      saveAccessToken(tokenResponse.access_token);
      router.replace("/dashboard");
    } catch (error) {
      setErrorMessage(
        error instanceof ApiError
          ? error.message
          : "Unable to create your CRM account.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <main className="flex min-h-screen items-start justify-center bg-slate-950 px-4 py-8">
      <section className="w-full max-w-md rounded-2xl border border-slate-800 bg-slate-900 p-8 shadow-2xl">
        <div className="mb-8">
          <p className="mb-3 text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
            Mini CRM
          </p>

          <h1 className="text-3xl font-bold text-white">Create your account</h1>

          <p className="mt-2 text-sm leading-6 text-slate-400">
            Register to manage customers, sales, tasks, meetings, and notes.
          </p>
        </div>

        <form className="space-y-5" onSubmit={handleSubmit}>
          <div>
            <label
              className="mb-2 block text-sm font-medium text-slate-200"
              htmlFor="full-name"
            >
              Full name
            </label>

            <input
              autoComplete="name"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              id="full-name"
              maxLength={200}
              onChange={(event) => setFullName(event.target.value)}
              placeholder="Your full name"
              required
              type="text"
              value={fullName}
            />
          </div>

          <div>
            <label
              className="mb-2 block text-sm font-medium text-slate-200"
              htmlFor="email"
            >
              Email address
            </label>

            <input
              autoComplete="email"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              id="email"
              maxLength={320}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="you@example.com"
              required
              type="email"
              value={email}
            />
          </div>

          <div>
            <label
              className="mb-2 block text-sm font-medium text-slate-200"
              htmlFor="password"
            >
              Password
            </label>

            <input
              autoComplete="new-password"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              id="password"
              maxLength={128}
              minLength={8}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="At least 8 characters"
              required
              type="password"
              value={password}
            />
          </div>

          <div>
            <label
              className="mb-2 block text-sm font-medium text-slate-200"
              htmlFor="password-confirmation"
            >
              Confirm password
            </label>

            <input
              autoComplete="new-password"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
              disabled={isSubmitting}
              id="password-confirmation"
              maxLength={128}
              minLength={8}
              onChange={(event) => setPasswordConfirmation(event.target.value)}
              placeholder="Enter the password again"
              required
              type="password"
              value={passwordConfirmation}
            />
          </div>

          {errorMessage && (
            <div
              className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
              role="alert"
            >
              {errorMessage}
            </div>
          )}

          <button
            className="w-full rounded-lg bg-blue-600 px-4 py-3 font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-700"
            disabled={isSubmitting}
            type="submit"
          >
            {isSubmitting ? "Creating account..." : "Create account"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-slate-400">
          Already have an account?{" "}
          <Link
            className="font-semibold text-blue-400 transition hover:text-blue-300"
            href="/login"
          >
            Sign in
          </Link>
        </p>
      </section>
    </main>
  );
}
