"use client";

import { useRouter } from "next/navigation";
import type { FormEvent } from "react";
import { useState } from "react";

import { AppShell } from "@/components/layout/app-shell";
import { useAuthenticatedUser } from "@/hooks/use-authenticated-user";
import { ApiError } from "@/lib/api";
import { changeCurrentUserPassword, updateCurrentUser } from "@/lib/auth-api";
import { removeAccessToken } from "@/lib/auth-storage";
import type { User } from "@/types/auth";

type ProfileContentProps = {
  initialUser: User;
  token: string;
};

function ProfileContent({ initialUser, token }: ProfileContentProps) {
  const router = useRouter();

  const [user, setUser] = useState<User>(initialUser);
  const [fullName, setFullName] = useState(initialUser.full_name);
  const [email, setEmail] = useState(initialUser.email);

  const [profileError, setProfileError] = useState("");
  const [profileSuccess, setProfileSuccess] = useState("");
  const [isSavingProfile, setIsSavingProfile] = useState(false);

  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [passwordConfirmation, setPasswordConfirmation] = useState("");

  const [passwordError, setPasswordError] = useState("");
  const [passwordSuccess, setPasswordSuccess] = useState("");
  const [isChangingPassword, setIsChangingPassword] = useState(false);

  function handleUnauthorized(error: unknown) {
    if (error instanceof ApiError && error.status === 401) {
      removeAccessToken();
      router.replace("/login");
      return true;
    }

    return false;
  }

  async function handleProfileSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    const normalizedFullName = fullName.trim();
    const normalizedEmail = email.trim().toLowerCase();

    setProfileError("");
    setProfileSuccess("");

    if (
      normalizedFullName === user.full_name &&
      normalizedEmail === user.email
    ) {
      setProfileSuccess("Your profile is already up to date.");
      return;
    }

    setIsSavingProfile(true);

    try {
      const updatedUser = await updateCurrentUser(
        {
          full_name: normalizedFullName,
          email: normalizedEmail,
        },
        token,
      );

      setUser(updatedUser);
      setFullName(updatedUser.full_name);
      setEmail(updatedUser.email);
      setProfileSuccess("Profile updated successfully.");
    } catch (error) {
      if (handleUnauthorized(error)) {
        return;
      }

      setProfileError(
        error instanceof ApiError
          ? error.message
          : "Unable to update your profile.",
      );
    } finally {
      setIsSavingProfile(false);
    }
  }

  async function handlePasswordSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();

    setPasswordError("");
    setPasswordSuccess("");

    if (newPassword !== passwordConfirmation) {
      setPasswordError("New passwords do not match.");
      return;
    }

    if (currentPassword === newPassword) {
      setPasswordError("The new password must be different.");
      return;
    }

    setIsChangingPassword(true);

    try {
      await changeCurrentUserPassword(
        {
          current_password: currentPassword,
          new_password: newPassword,
        },
        token,
      );

      setCurrentPassword("");
      setNewPassword("");
      setPasswordConfirmation("");
      setPasswordSuccess("Password changed successfully.");
    } catch (error) {
      if (handleUnauthorized(error)) {
        return;
      }

      setPasswordError(
        error instanceof ApiError
          ? error.message
          : "Unable to change your password.",
      );
    } finally {
      setIsChangingPassword(false);
    }
  }

  return (
    <AppShell user={user}>
      <section>
        <p className="text-sm font-medium text-blue-400">Account</p>

        <h1 className="mt-1 text-3xl font-bold">Profile</h1>

        <p className="mt-2 text-sm text-slate-400">
          Manage your account information and password.
        </p>
      </section>

      <div className="mt-8 grid gap-6 xl:grid-cols-2">
        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <div>
            <h2 className="text-lg font-semibold">Profile details</h2>

            <p className="mt-1 text-sm text-slate-400">
              Update the name and email associated with your CRM account.
            </p>
          </div>

          <form className="mt-6 space-y-5" onSubmit={handleProfileSubmit}>
            <div>
              <label
                className="mb-2 block text-sm font-medium text-slate-200"
                htmlFor="profile-full-name"
              >
                Full name
              </label>

              <input
                autoComplete="name"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isSavingProfile}
                id="profile-full-name"
                maxLength={200}
                minLength={2}
                onChange={(event) => setFullName(event.target.value)}
                required
                type="text"
                value={fullName}
              />
            </div>

            <div>
              <label
                className="mb-2 block text-sm font-medium text-slate-200"
                htmlFor="profile-email"
              >
                Email address
              </label>

              <input
                autoComplete="email"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isSavingProfile}
                id="profile-email"
                maxLength={320}
                onChange={(event) => setEmail(event.target.value)}
                required
                type="email"
                value={email}
              />
            </div>

            {profileError && (
              <div
                className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
                role="alert"
              >
                {profileError}
              </div>
            )}

            {profileSuccess && (
              <div
                className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300"
                role="status"
              >
                {profileSuccess}
              </div>
            )}

            <button
              className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-700"
              disabled={isSavingProfile}
              type="submit"
            >
              {isSavingProfile ? "Saving..." : "Save profile"}
            </button>
          </form>

          <dl className="mt-8 border-t border-slate-800 pt-6 text-sm">
            <div className="flex items-center justify-between gap-4">
              <dt className="text-slate-500">Account ID</dt>

              <dd className="font-medium text-slate-300">#{user.id}</dd>
            </div>

            <div className="mt-3 flex items-center justify-between gap-4">
              <dt className="text-slate-500">Account created</dt>

              <dd className="font-medium text-slate-300">
                {new Date(user.created_at).toLocaleDateString()}
              </dd>
            </div>

            <div className="mt-3 flex items-center justify-between gap-4">
              <dt className="text-slate-500">Status</dt>

              <dd className="font-medium text-emerald-300">
                {user.is_active ? "Active" : "Inactive"}
              </dd>
            </div>
          </dl>
        </section>

        <section className="rounded-2xl border border-slate-800 bg-slate-900 p-6 sm:p-8">
          <div>
            <h2 className="text-lg font-semibold">Change password</h2>

            <p className="mt-1 text-sm text-slate-400">
              Confirm your current password before choosing a new one.
            </p>
          </div>

          <form className="mt-6 space-y-5" onSubmit={handlePasswordSubmit}>
            <div>
              <label
                className="mb-2 block text-sm font-medium text-slate-200"
                htmlFor="current-password"
              >
                Current password
              </label>

              <input
                autoComplete="current-password"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isChangingPassword}
                id="current-password"
                maxLength={128}
                minLength={8}
                onChange={(event) => setCurrentPassword(event.target.value)}
                required
                type="password"
                value={currentPassword}
              />
            </div>

            <div>
              <label
                className="mb-2 block text-sm font-medium text-slate-200"
                htmlFor="new-password"
              >
                New password
              </label>

              <input
                autoComplete="new-password"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isChangingPassword}
                id="new-password"
                maxLength={128}
                minLength={8}
                onChange={(event) => setNewPassword(event.target.value)}
                placeholder="At least 8 characters"
                required
                type="password"
                value={newPassword}
              />
            </div>

            <div>
              <label
                className="mb-2 block text-sm font-medium text-slate-200"
                htmlFor="confirm-new-password"
              >
                Confirm new password
              </label>

              <input
                autoComplete="new-password"
                className="w-full rounded-lg border border-slate-700 bg-slate-950 px-4 py-3 text-white outline-none transition placeholder:text-slate-600 focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 disabled:cursor-not-allowed disabled:opacity-60"
                disabled={isChangingPassword}
                id="confirm-new-password"
                maxLength={128}
                minLength={8}
                onChange={(event) =>
                  setPasswordConfirmation(event.target.value)
                }
                required
                type="password"
                value={passwordConfirmation}
              />
            </div>

            {passwordError && (
              <div
                className="rounded-lg border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-300"
                role="alert"
              >
                {passwordError}
              </div>
            )}

            {passwordSuccess && (
              <div
                className="rounded-lg border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-300"
                role="status"
              >
                {passwordSuccess}
              </div>
            )}

            <button
              className="rounded-lg bg-blue-600 px-5 py-3 text-sm font-semibold text-white transition hover:bg-blue-500 disabled:cursor-not-allowed disabled:bg-slate-700"
              disabled={isChangingPassword}
              type="submit"
            >
              {isChangingPassword ? "Changing password..." : "Change password"}
            </button>
          </form>
        </section>
      </div>
    </AppShell>
  );
}

export default function ProfilePage() {
  const { user, token, isLoading, errorMessage } = useAuthenticatedUser();

  if (isLoading || !user || !token) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-slate-950 px-4">
        <p
          className={`text-sm ${
            errorMessage ? "text-red-300" : "text-slate-400"
          }`}
        >
          {errorMessage || "Loading profile..."}
        </p>
      </main>
    );
  }

  return <ProfileContent initialUser={user} token={token} />;
}
