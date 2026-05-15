import { create } from "zustand";
import { persist } from "zustand/middleware";
import type { UserResponse, ProfileResponse } from "@/lib/api/auth";

interface AuthState {
  user: UserResponse | null;
  profile: ProfileResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  setUser: (user: UserResponse, profile: ProfileResponse) => void;
  updateProfile: (profile: Partial<ProfileResponse>) => void;
  clearUser: () => void;
  setLoading: (loading: boolean) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      profile: null,
      isAuthenticated: false,
      isLoading: true,
      setUser: (user, profile) =>
        set({ user, profile, isAuthenticated: true, isLoading: false }),
      updateProfile: (updates) =>
        set((state) => ({
          profile: state.profile ? { ...state.profile, ...updates } : null,
        })),
      clearUser: () =>
        set({
          user: null,
          profile: null,
          isAuthenticated: false,
          isLoading: false,
        }),
      setLoading: (loading) => set({ isLoading: loading }),
    }),
    {
      name: "govscheme-auth",
      partialize: (state) => ({
        user: state.user,
        profile: state.profile,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);
