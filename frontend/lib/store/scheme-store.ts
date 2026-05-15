import { create } from "zustand";
import type { SchemeCard } from "@/lib/api/schemes";

interface SchemeState {
  savedSchemeIds: Set<string>;
  comparisonIds: string[];
  addToSaved: (id: string) => void;
  removeFromSaved: (id: string) => void;
  isSaved: (id: string) => boolean;
  setSavedIds: (ids: string[]) => void;
  setComparisonIds: (ids: string[]) => void;
  toggleComparison: (id: string) => void;
  clearComparison: () => void;
}

export const useSchemeStore = create<SchemeState>()((set, get) => ({
  savedSchemeIds: new Set(),
  comparisonIds: [],
  addToSaved: (id) =>
    set((state) => {
      const next = new Set(state.savedSchemeIds);
      next.add(id);
      return { savedSchemeIds: next };
    }),
  removeFromSaved: (id) =>
    set((state) => {
      const next = new Set(state.savedSchemeIds);
      next.delete(id);
      return { savedSchemeIds: next };
    }),
  isSaved: (id) => get().savedSchemeIds.has(id),
  setSavedIds: (ids) => set({ savedSchemeIds: new Set(ids) }),
  setComparisonIds: (ids) => set({ comparisonIds: ids }),
  toggleComparison: (id) =>
    set((state) => {
      const exists = state.comparisonIds.includes(id);
      return {
        comparisonIds: exists
          ? state.comparisonIds.filter((i) => i !== id)
          : [...state.comparisonIds, id],
      };
    }),
  clearComparison: () => set({ comparisonIds: [] }),
}));
