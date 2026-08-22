"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import type { ReactNode } from "react";

import { removeAccessToken } from "@/lib/auth-storage";
import type { User } from "@/types/auth";

const navigationItems = [
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

  function handleLogout() {
    removeAccessToken();
    router.replace("/login");
  }

  return (
    <div className="min-h-screen bg-slate-950 text-white lg:grid lg:grid-cols-[250px_1fr]">
      <aside className="border-b border-slate-800 bg-slate-900 lg:min-h-screen lg:border-b-0 lg:border-r">
        <div className="px-6 py-6">
          <p className="text-sm font-semibold uppercase tracking-[0.2em] text-blue-400">
            Mini CRM
          </p>

          <p className="mt-1 text-xs text-slate-500">
            Lead & client management
          </p>
        </div>

        <nav
          aria-label="CRM navigation"
          className="flex gap-2 overflow-x-auto px-4 pb-4 lg:flex-col lg:overflow-visible"
        >
          {navigationItems.map((item) => {
            const isActive =
              item.href === "/dashboard"
                ? pathname === item.href
                : pathname.startsWith(item.href);

            return (
              <Link
                aria-current={
                  isActive ? "page" : undefined
                }
                className={`shrink-0 rounded-lg px-4 py-3 text-sm font-medium transition ${
                  isActive
                    ? "bg-blue-600 text-white"
                    : "text-slate-400 hover:bg-slate-800 hover:text-white"
                }`}
                href={item.href}
                key={item.href}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </aside>

      <div className="min-w-0">
        <header className="border-b border-slate-800 bg-slate-900/90 backdrop-blur">
          <div className="flex min-h-20 items-center justify-between gap-4 px-6">
            <div className="min-w-0">
              <p className="truncate text-sm font-medium text-slate-200">
                {user.full_name}
              </p>

              <p className="truncate text-xs text-slate-500">
                {user.email}
              </p>
            </div>

            <button
              className="shrink-0 rounded-lg border border-slate-700 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-slate-500 hover:bg-slate-800"
              onClick={handleLogout}
              type="button"
            >
              Log out
            </button>
          </div>
        </header>

        <main className="px-6 py-8 lg:px-10">
          {children}
        </main>
      </div>
    </div>
  );
}