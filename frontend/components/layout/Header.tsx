"use client";

import { useState } from "react";
import { useAuthStore } from "@/lib/store/auth-store";
import { useUIStore } from "@/lib/store/ui-store";
import { authApi } from "@/lib/api/auth";
import { Button } from "@/components/ui/button";
import {
  Menu,
  Search,
  Bell,
  Sun,
  Moon,
  LogOut,
  User,
  Settings,
} from "lucide-react";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { useRouter } from "next/navigation";

export function Header() {
  const { user, clearUser } = useAuthStore();
  const { toggleSidebar, language, setTheme, theme } = useUIStore();
  const router = useRouter();
  const [searchOpen, setSearchOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await authApi.logout();
    } catch {
      // ignore logout errors
    }
    localStorage.removeItem("access_token");
    clearUser();
    router.push("/");
  };

  return (
    <header className="h-14 border-b border-border bg-background/80 backdrop-blur-xl sticky top-0 z-40">
      <div className="flex items-center justify-between h-full px-4 md:px-6">
        <div className="flex items-center gap-3">
          <Button
            variant="ghost"
            size="icon"
            onClick={toggleSidebar}
            className="hidden lg:flex"
          >
            <Menu className="w-4 h-4" />
          </Button>

          <button
            onClick={() => setSearchOpen(!searchOpen)}
            className="flex items-center gap-2 px-3 py-1.5 rounded-lg bg-secondary/50 border border-border text-sm text-slate-400 hover:text-foreground transition-colors md:w-64"
          >
            <Search className="w-3.5 h-3.5" />
            <span className="hidden md:inline">
              {language === "hi" ? "योजनाएं खोजें..." : "Search schemes..."}
            </span>
            <span className="hidden md:inline ml-auto text-[10px] text-slate-600 border border-border rounded px-1.5">
              ⌘K
            </span>
          </button>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="icon"
            onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
            className="text-slate-400 hover:text-foreground"
          >
            {theme === "dark" ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
          </Button>

          {user ? (
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="icon" className="rounded-full">
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-saffron-500 to-saffron-400 flex items-center justify-center text-[11px] font-bold text-white">
                    {user.email.charAt(0).toUpperCase()}
                  </div>
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end" className="w-56">
                <DropdownMenuLabel>
                  <div className="flex flex-col">
                    <span className="text-sm font-medium">{user.email}</span>
                    <span className="text-xs text-muted-foreground capitalize">{user.role}</span>
                  </div>
                </DropdownMenuLabel>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={() => router.push("/settings")}>
                  <Settings className="w-4 h-4 mr-2" /> Settings
                </DropdownMenuItem>
                <DropdownMenuSeparator />
                <DropdownMenuItem onClick={handleLogout} className="text-destructive">
                  <LogOut className="w-4 h-4 mr-2" /> Sign Out
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          ) : (
            <Button variant="default" size="sm" onClick={() => router.push("/login")}>
              Sign In
            </Button>
          )}
        </div>
      </div>
    </header>
  );
}
