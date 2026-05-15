"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { useAuthStore } from "@/lib/store/auth-store";
import { Shield, Users, LayoutList, MessageSquare, Activity, Sparkles } from "lucide-react";
import { redirect } from "next/navigation";

export default function AdminPage() {
  const { user } = useAuthStore();
  const isAdmin = user?.role === "admin" || user?.role === "superadmin";

  if (!isAdmin) {
    redirect("/dashboard");
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center gap-3">
        <Shield className="w-6 h-6 text-saffron-500" />
        <div>
          <h1 className="text-2xl font-heading font-bold">Admin Dashboard</h1>
          <p className="text-sm text-slate-400">Platform management and analytics</p>
        </div>
      </div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          { icon: Users, label: "Users", value: "—", color: "from-blue-500/10 to-blue-500/5" },
          { icon: LayoutList, label: "Schemes", value: "—", color: "from-saffron-500/10 to-saffron-500/5" },
          { icon: MessageSquare, label: "Conversations", value: "—", color: "from-jade-500/10 to-jade-500/5" },
          { icon: Activity, label: "Health", value: "OK", color: "from-jade-500/10 to-jade-500/5" },
        ].map((stat) => (
          <div key={stat.label} className={`p-4 rounded-xl border border-border bg-card ${stat.color}`}>
            <stat.icon className="w-5 h-5 text-saffron-500 mb-2" />
            <div className="text-2xl font-heading font-bold">{stat.value}</div>
            <div className="text-xs text-slate-400">{stat.label}</div>
          </div>
        ))}
      </div>

      <div className="rounded-xl border border-border bg-card p-6">
        <h2 className="font-heading font-semibold mb-4">Quick Actions</h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <button className="text-left p-3 rounded-lg bg-secondary/30 border border-border text-sm hover:border-saffron-500/30 transition-colors">
            Manage Schemes
          </button>
          <button className="text-left p-3 rounded-lg bg-secondary/30 border border-border text-sm hover:border-saffron-500/30 transition-colors">
            View Scraping Jobs
          </button>
          <button className="text-left p-3 rounded-lg bg-secondary/30 border border-border text-sm hover:border-saffron-500/30 transition-colors">
            User Management
          </button>
          <button className="text-left p-3 rounded-lg bg-secondary/30 border border-border text-sm hover:border-saffron-500/30 transition-colors">
            System Health
          </button>
        </div>
      </div>
    </div>
  );
}
