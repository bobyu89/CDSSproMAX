"use client";

import { create } from "zustand";

export type UserRole = "student" | "teacher" | "admin";

interface AuthState {
  participantId: string | null;
  participantCode: string | null;
  role: UserRole;
  name: string | null;
  token: string | null;
  expiresAt: number | null; // unix seconds
  isLoggedIn: boolean;
  hydrated: boolean;

  login: (data: {
    participantId: string;
    participantCode: string;
    role: UserRole;
    name: string;
    token: string;
    expiresAt: number;
  }) => void;
  logout: () => void;
  hydrate: () => void;
  isTokenExpired: () => boolean;
}

const STORAGE_KEY = "ticdss-auth";

interface StoredAuth {
  participantId: string;
  participantCode: string;
  role: UserRole;
  name: string;
  token: string;
  expiresAt: number;
}

function readStored(): StoredAuth | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = JSON.parse(raw) as StoredAuth;
    if (parsed.expiresAt && parsed.expiresAt < Math.floor(Date.now() / 1000)) {
      sessionStorage.removeItem(STORAGE_KEY);
      return null;
    }
    return parsed;
  } catch {
    return null;
  }
}

export const useAuthStore = create<AuthState>((set, get) => ({
  participantId: null,
  participantCode: null,
  role: "student",
  name: null,
  token: null,
  expiresAt: null,
  isLoggedIn: false,
  hydrated: false,

  hydrate: () => {
    if (get().hydrated) return;
    const stored = readStored();
    if (stored) {
      set({
        participantId: stored.participantId,
        participantCode: stored.participantCode,
        role: stored.role,
        name: stored.name,
        token: stored.token,
        expiresAt: stored.expiresAt,
        isLoggedIn: true,
        hydrated: true,
      });
    } else {
      set({ hydrated: true });
    }
  },

  login: ({ participantId, participantCode, role, name, token, expiresAt }) => {
    if (typeof window !== "undefined") {
      sessionStorage.setItem(
        STORAGE_KEY,
        JSON.stringify({ participantId, participantCode, role, name, token, expiresAt }),
      );
    }
    set({
      participantId,
      participantCode,
      role,
      name,
      token,
      expiresAt,
      isLoggedIn: true,
      hydrated: true,
    });
  },

  logout: () => {
    if (typeof window !== "undefined") {
      sessionStorage.removeItem(STORAGE_KEY);
    }
    set({
      participantId: null,
      participantCode: null,
      role: "student",
      name: null,
      token: null,
      expiresAt: null,
      isLoggedIn: false,
    });
  },

  isTokenExpired: () => {
    const exp = get().expiresAt;
    return !exp || exp < Math.floor(Date.now() / 1000);
  },
}));
