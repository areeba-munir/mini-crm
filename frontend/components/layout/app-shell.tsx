"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { useState, type ReactNode } from "react";

import { removeAccessToken } from "@/lib/auth-storage";
import type { User, UserRole } from "@/types/auth";

type NavigationItem = {
  href: string;
  label: string;
  allowedRoles?: UserRole[];
};

const navigationItems: NavigationItem[] = [
  {
    href: "/dashboard",
    label: "Dashboard",
  },
  {
    href: "/companies",
    label: "Companies",
  },
  {
    href: "/contacts",
    label: "Contacts",
  },
  {
    href: "/leads",
    label: "Leads",
  },
  {
    href: "/tasks",
    label: "Tasks",
  },
  {
    href: "/meetings",
    label: "Meetings",
  },
  {
    href: "/notes",
    label: "Notes",
  },
  {
    href: "/search",
    label: "Search",
  },
  {
    href: "/activities",
    label: "Activity",
    allowedRoles: ["Admin", "Manager"],
  },
  {
    href: "/users",
    label: "Users",
    allowedRoles: ["Admin"],
  },
  {
    href: "/profile",
    label: "Profile",
  },
];

type AppShellProps = {
  user: User;
  children: ReactNode;
};

export function AppShell({
  user,
  children,
}: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();

  const [
    isMobileNavigationOpen,
    setIsMobileNavigationOpen,
  ] = useState(false);

  const visibleNavigationItems =
    navigationItems.filter(
      (item) =>
        !item.allowedRoles ||
        item.allowedRoles.includes(user.role),
    );

  function closeMobileNavigation() {
    setIsMobileNavigationOpen(false);
  }

  function handleLogout() {
    closeMobileNavigation();
    removeAccessToken();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white lg:grid lg:grid-cols-[250px_minmax(0,1fr)]">
      {isMobileNavigationOpen && (
        <button
          aria-label="Close navigation"
          className="fixed inset-0 z-40 bg-slate-950/80 backdrop-blur-sm lg:hidden"
          onClick={closeMobileNavigation}
          type="button"
        />
      )}

      <aside
        aria-label="Main navigation"
        className={`fixed inset-y-0 left-0 z-50 flex w-72 flex-col border-r border-slate-800 bg-slate-900 transition-transform duration-200 lg:sticky lg:top-0 lg:z-auto lg:h-screen lg:w-auto lg:translate-x-0 lg:self-start ${
          isMobileNavigationOpen
            ? "translate-x-0"
            : "-translate-x-full"
        }`}
        id="mobile-navigation"
      >
        <div className="flex items-start justify-between gap-4 px-6 py-6">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
              Mini CRM
            </p>

            <p className="mt-1 text-xs text-slate-500">
              Lead &amp; client management
            </p>
          </div>

          <button
            aria-label="Close navigation"
            className="rounded-lg border border-slate-700 p-2 text-slate-300 transition hover:bg-slate-800 hover:text-white lg:hidden"
            onClick={closeMobileNavigation}
            type="button"
          >
            <svg
              aria-hidden="true"
              className="h-5 w-5"
              fill="none"
              stroke="currentColor"
              strokeWidth="2"
              viewBox="0 0 24 24"
            >
              <path
                d="M6 6l12 12M18 6 6 18"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        <nav
          aria-label="CRM navigation"
          className="flex flex-1 flex-col gap-2 overflow-y-auto px-4 pb-6"
        >
          {visibleNavigationItems.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === item.href
                : pathname.startsWith(item.href);

            return (
              <Link
                aria-current={
                  isActive ? "page" : undefined
                }
                className={`rounded-lg px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
                href={item.href}
                key={item.href}
                onClick={closeMobileNavigation}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>

        <div className="border-t border-slate-800 p-4 lg:hidden">
          <Link
            className="block rounded-lg px-4 py-3 transition hover:bg-slate-800"
            href="/profile"
            onClick={closeMobileNavigation}
          >
            <p className="truncate text-sm font-medium text-slate-200">
              {user.full_name}
            </p>

            <p className="mt-1 truncate text-xs text-slate-500">
              {user.email}
            </p>

            <p className="mt-1 text-xs font-medium text-blue-400">
              {user.role}
            </p>
          </Link>
        </div>
      </aside>

      <div className="min-w-0">
        <header className="sticky top-0 z-30 border-b border-slate-800 bg-slate-900/95 backdrop-blur">
          <div className="flex min-h-20 items-center justify-between gap-3 px-4 sm:px-6">
            <div className="flex min-w-0 items-center gap-3">
              <button
                aria-controls="mobile-navigation"
                aria-expanded={
                  isMobileNavigationOpen
                }
                aria-label="Open navigation"
                className="shrink-0 rounded-lg border border-slate-700 p-2 text-slate-300 transition hover:bg-slate-800 hover:text-white lg:hidden"
                onClick={() =>
                  setIsMobileNavigationOpen(true)
                }
                type="button"
              >
                <svg
                  aria-hidden="true"
                  className="h-5 w-5"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  viewBox="0 0 24 24"
                >
                  <path
                    d="M4 6h16M4 12h16M4 18h16"
                    strokeLinecap="round"
                  />
                </svg>
              </button>

              <Link
                className="min-w-0 rounded-lg px-2 py-1 transition hover:bg-slate-800"
                href="/profile"
              >
                <div className="flex min-w-0 items-center gap-2">
                  <p className="truncate text-sm font-medium text-slate-200">
                    {user.full_name}
                  </p>

                  <span className="hidden rounded-full bg-blue-500/10 px-2 py-0.5 text-xs font-medium text-blue-300 sm:inline">
                    {user.role}
                  </span>
                </div>

                <p className="hidden truncate text-xs text-slate-500 sm:block">
                  {user.email}
                </p>
              </Link>
            </div>

            <button
              className="shrink-0 rounded-lg border border-slate-700 px-3 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800 sm:px-4"
              onClick={handleLogout}
              type="button"
            >
              Log out
            </button>
          </div>
        </header>

        <main className="px-4 py-6 sm:px-6 sm:py-8 lg:px-10">
          {children}
        </main>
      </div>
    </div>
  );
}