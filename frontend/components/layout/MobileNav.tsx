"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/lib/store/auth-store";
import { MessageSquare, LayoutList, CheckCircle2, Home, Bookmark } from "lucide-react";

const mobileItems = [
  { href: "/dashboard", icon: Home, label: "Home" },
  { href: "/chat", icon: MessageSquare, label: "Chat" },
  { href: "/schemes", icon: LayoutList, label: "Schemes" },
  { href: "/eligibility", icon: CheckCircle2, label: "Check" },
  { href: "/saved", icon: Bookmark, label: "Saved" },
];

export function MobileNav() {
  const pathname = usePathname();
  const { user } = useAuthStore();

  const isAuthPage = pathname?.startsWith("/login") || pathname?.startsWith("/register");
  if (isAuthPage) return null;

  return (
    <nav className="lg:hidden fixed bottom-0 left-0 right-0 z-50 border-t border-border bg-background/95 backdrop-blur-xl safe-area-bottom">
      <div className="flex items-center justify-around h-14 px-2">
        {mobileItems.map((item) => {
          if (item.href !== "/schemes" && !user) return null;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex flex-col items-center gap-0.5 px-3 py-1.5 rounded-lg transition-colors",
                pathname === item.href || pathname?.startsWith(item.href + "/")
                  ? "text-saffron-500"
                  : "text-slate-500 hover:text-foreground"
              )}
            >
              <item.icon className="w-5 h-5" />
              <span className="text-[10px] font-medium">{item.label}</span>
            </Link>
          );
        })}
      </div>
    </nav>
  );
}
