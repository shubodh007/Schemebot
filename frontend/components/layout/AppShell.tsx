"use client";

import { useEffect, useState } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { usePathname } from "next/navigation";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";
import { MobileNav } from "./MobileNav";
import { useUIStore } from "@/lib/store/ui-store";
import { cn } from "@/lib/utils";

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const { sidebarOpen } = useUIStore();
  const [mounted, setMounted] = useState(false);

  useEffect(() => setMounted(true), []);

  const isAuthPage = pathname?.startsWith("/login") || pathname?.startsWith("/register");
  if (isAuthPage) return <>{children}</>;

  if (!mounted) return null;

  return (
    <div className="flex h-screen overflow-hidden bg-background">
      <AnimatePresence mode="wait">
        {sidebarOpen && (
          <motion.div
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={{ duration: 0.2, ease: "easeOut" }}
            className="hidden lg:block"
          >
            <Sidebar />
          </motion.div>
        )}
      </AnimatePresence>

      <div className="flex flex-1 flex-col min-w-0">
        <Header />
        <main
          className={cn(
            "flex-1 overflow-y-auto px-4 md:px-6 lg:px-8 py-6",
            "scroll-smooth"
          )}
        >
          {children}
        </main>
      </div>

      <MobileNav />
    </div>
  );
}
