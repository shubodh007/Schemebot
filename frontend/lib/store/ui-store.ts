import { create } from "zustand";

type Language = "en" | "hi" | "te";

interface UIState {
  sidebarOpen: boolean;
  language: Language;
  theme: "dark" | "light" | "system";
  mobileNavOpen: boolean;

  toggleSidebar: () => void;
  setSidebarOpen: (open: boolean) => void;
  setLanguage: (lang: Language) => void;
  setTheme: (theme: "dark" | "light" | "system") => void;
  setMobileNavOpen: (open: boolean) => void;
}

export const useUIStore = create<UIState>()((set) => ({
  sidebarOpen: true,
  language: "en",
  theme: "dark",
  mobileNavOpen: false,

  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  setLanguage: (lang) => set({ language: lang }),
  setTheme: (theme) => set({ theme }),
  setMobileNavOpen: (open) => set({ mobileNavOpen: open }),
}));
