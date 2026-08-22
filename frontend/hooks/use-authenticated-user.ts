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

export function useAuthenticatedUser() {
  const router = useRouter();

  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(
    null,
  );
  const [isLoading, setIsLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    const storedToken = getAccessToken();

    if (!storedToken) {
      router.replace("/login");
      return;
    }

    let cancelled = false;

    async function authenticate(
      accessToken: string,
    ) {
      try {
        const currentUser = await getCurrentUser(
          accessToken,
        );

        if (!cancelled) {
          setUser(currentUser);
          setToken(accessToken);
          setIsLoading(false);
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
          "Unable to verify your CRM account.",
        );
        setIsLoading(false);
      }
    }

    void authenticate(storedToken);

    return () => {
      cancelled = true;
    };
  }, [router]);

  return {
    user,
    token,
    isLoading,
    errorMessage,
  };
}