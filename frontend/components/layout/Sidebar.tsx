"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useUIStore } from "@/lib/store/ui-store";
import { useAuthStore } from "@/lib/store/auth-store";
import {
  Home,
  MessageSquare,
  LayoutList,
  CheckCircle2,
  FileText,
  Scale,
  Bookmark,
  Clock,
  Settings,
  Shield,
  BarChart3,
  Sparkles,
} from "lucide-react";

const navItems = [
  { href: "/dashboard", icon: Home, label: "Home", auth: true },
  { href: "/chat", icon: MessageSquare, label: "Chat", auth: true },
  { href: "/schemes", icon: LayoutList, label: "Schemes", auth: false },
  { href: "/eligibility", icon: CheckCircle2, label: "Eligibility", auth: true },
  { href: "/documents", icon: FileText, label: "Documents", auth: true },
  { href: "/legal", icon: Scale, label: "Legal Help", auth: true },
  { href: "/saved", icon: Bookmark, label: "Saved", auth: true },
  { href: "/history", icon: Clock, label: "History", auth: true },
  { href: "/settings", icon: Settings, label: "Settings", auth: true },
];

const adminItems = [
  { href: "/admin", icon: Shield, label: "Admin", role: "admin" },
  { href: "/admin/analytics", icon: BarChart3, label: "Analytics", role: "admin" },
];

export function Sidebar() {
  const pathname = usePathname();
  const { language } = useUIStore();
  const { user } = useAuthStore();

  const isActive = (href: string) => pathname === href || pathname?.startsWith(href + "/");

  return (
    <aside className="w-60 h-full border-r border-border bg-card flex flex-col">
      <div className="p-5 border-b border-border">
        <Link href="/" className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-saffron-500 to-saffron-400 flex items-center justify-center shadow-lg shadow-saffron-500/20">
            <Sparkles className="w-4 h-4 text-white" />
          </div>
          <span className="font-heading font-bold text-lg tracking-tight">
            Gov<span className="text-saffron-500">Scheme</span>
          </span>
        </Link>
      </div>

      <nav className="flex-1 overflow-y-auto p-3 space-y-1">
        {navItems.map((item) => {
          if (item.auth && !user) return null;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                isActive(item.href)
                  ? "bg-saffron-500/10 text-saffron-500 border border-saffron-500/20"
                  : "text-slate-400 hover:text-foreground hover:bg-secondary/50"
              )}
            >
              <item.icon className="w-4 h-4 flex-shrink-0" />
              <span>{item.label}</span>
            </Link>
          );
        })}

        {user?.role === "admin" || user?.role === "superadmin" ? (
          <>
            <div className="pt-4 pb-2">
              <div className="text-[10px] uppercase tracking-widest text-slate-600 font-semibold px-3">
                Admin
              </div>
            </div>
            {adminItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all duration-200",
                  isActive(item.href)
                    ? "bg-saffron-500/10 text-saffron-500 border border-saffron-500/20"
                    : "text-slate-400 hover:text-foreground hover:bg-secondary/50"
                )}
              >
                <item.icon className="w-4 h-4 flex-shrink-0" />
                <span>{item.label}</span>
              </Link>
            ))}
          </>
        ) : null}
      </nav>

      <div className="p-3 border-t border-border">
        <div className="px-3 py-2 rounded-lg bg-gradient-to-r from-saffron-500/5 to-jade-500/5 border border-saffron-500/10">
          <p className="text-[11px] text-slate-400 leading-relaxed">
            {language === "hi" ? "AI द्वारा संचालित" : language === "te" ? "AI ద్వారా ఆధారితం" : "Powered by AI"}
          </p>
          <p className="text-[10px] text-slate-600 mt-0.5">
            OpenRouter · Google · Groq
          </p>
        </div>
      </div>
    </aside>
  );
}
