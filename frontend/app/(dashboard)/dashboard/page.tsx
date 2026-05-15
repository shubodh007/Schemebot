"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { SchemeCard } from "@/components/schemes/SchemeCard";
import { DashboardSkeleton } from "@/components/common/SkeletonLoader";
import { useAuthStore } from "@/lib/store/auth-store";
import { schemesApi, type SchemeCard as SchemeCardType } from "@/lib/api/schemes";
import { MessageSquare, CheckCircle2, FileText, Bookmark, ArrowRight, Sparkles } from "lucide-react";

const quickActions = [
  { href: "/chat", icon: MessageSquare, label: "Ask AI", color: "from-saffron-500/10 to-jade-500/10 border-saffron-500/20" },
  { href: "/eligibility", icon: CheckCircle2, label: "Check Eligibility", color: "from-jade-500/10 to-jade-500/5 border-jade-500/20" },
  { href: "/documents", icon: FileText, label: "Upload Document", color: "from-slate-500/10 to-slate-500/5 border-slate-500/20" },
  { href: "/saved", icon: Bookmark, label: "Saved Schemes", color: "from-saffron-500/10 to-slate-500/5 border-saffron-500/20" },
];

export default function DashboardPage() {
  const { profile } = useAuthStore();
  const [schemes, setSchemes] = useState<SchemeCardType[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    schemesApi.list({ limit: 6 }).then((res) => {
      setSchemes(res.schemes);
    }).catch(() => {
    }).finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
      >
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-heading font-bold">
              Welcome{profile?.full_name ? `, ${profile.full_name.split(" ")[0]}` : ""}
            </h1>
            <p className="text-slate-400 text-sm mt-1">
              Discover schemes tailored to your profile
            </p>
          </div>
          <Link href="/chat">
            <Button variant="saffron" className="gap-2">
              <MessageSquare className="w-4 h-4" />
              Chat with AI
            </Button>
          </Link>
        </div>
      </motion.div>

      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {quickActions.map((action, i) => (
          <motion.div
            key={action.href}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.05 }}
          >
            <Link href={action.href}>
              <div className={`p-4 rounded-xl border ${action.color} hover:shadow-lg transition-all duration-200 group`}>
                <action.icon className="w-5 h-5 text-saffron-500 mb-2 group-hover:scale-110 transition-transform" />
                <p className="text-sm font-medium">{action.label}</p>
              </div>
            </Link>
          </motion.div>
        ))}
      </div>

      <div>
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-heading font-semibold flex items-center gap-2">
            <Sparkles className="w-4 h-4 text-saffron-500" />
            Popular Schemes
          </h2>
          <Link href="/schemes">
            <Button variant="ghost" size="sm" className="gap-1 text-slate-400">
              View All <ArrowRight className="w-3 h-3" />
            </Button>
          </Link>
        </div>

        {loading ? (
          <DashboardSkeleton />
        ) : schemes.length > 0 ? (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {schemes.map((scheme, i) => (
              <SchemeCard key={scheme.id} scheme={scheme} index={i} />
            ))}
          </div>
        ) : (
          <div className="text-center py-12 rounded-xl border border-border bg-card">
            <Sparkles className="w-8 h-8 text-saffron-500 mx-auto mb-3" />
            <p className="text-slate-400">No schemes loaded yet</p>
            <p className="text-sm text-slate-600 mt-1">Schemes will appear here once indexed</p>
          </div>
        )}
      </div>

      {profile && !profile.profile_complete && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="p-4 rounded-xl border border-saffron-500/20 bg-gradient-to-r from-saffron-500/5 to-transparent"
        >
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-saffron-500/10 flex items-center justify-center">
                <Sparkles className="w-4 h-4 text-saffron-500" />
              </div>
              <div>
                <p className="text-sm font-medium">Complete your profile</p>
                <p className="text-xs text-slate-400">Get better scheme recommendations</p>
              </div>
            </div>
            <Link href="/settings">
              <Button variant="outline" size="sm">Complete</Button>
            </Link>
          </div>
        </motion.div>
      )}
    </div>
  );
}
