"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { SchemeCard } from "@/components/schemes/SchemeCard";
import { DashboardSkeleton } from "@/components/common/SkeletonLoader";
import { useAuthStore } from "@/lib/store/auth-store";
import { schemesApi, type EligibilityMatch } from "@/lib/api/schemes";
import { CheckCircle2, AlertCircle, Sparkles, RefreshCw, UserCheck } from "lucide-react";

export default function EligibilityPage() {
  const { profile } = useAuthStore();
  const [matches, setMatches] = useState<EligibilityMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [checked, setChecked] = useState(false);

  const runCheck = async () => {
    setLoading(true);
    try {
      const res = await schemesApi.checkEligibility();
      setMatches(res.matches);
      setChecked(true);
    } catch {
      // handle error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (profile && !checked) runCheck();
  }, [profile]);

  const eligible = matches.filter((m) => m.eligible);
  const notEligible = matches.filter((m) => !m.eligible);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-heading font-bold">Eligibility Check</h1>
          <p className="text-sm text-slate-400 mt-1">
            Schemes matched to your profile
          </p>
        </div>
        <Button variant="outline" onClick={runCheck} disabled={loading} className="gap-2">
          <RefreshCw className={`w-4 h-4 ${loading ? "animate-spin" : ""}`} />
          Refresh
        </Button>
      </div>

      {!profile?.profile_complete && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex items-start gap-3 p-4 rounded-xl border border-saffron-500/20 bg-saffron-500/5"
        >
          <AlertCircle className="w-5 h-5 text-saffron-500 flex-shrink-0 mt-0.5" />
          <div>
            <p className="text-sm font-medium">Profile incomplete</p>
            <p className="text-xs text-slate-400 mt-1">
              Complete your profile for more accurate scheme matching
            </p>
          </div>
        </motion.div>
      )}

      {loading ? (
        <DashboardSkeleton />
      ) : checked ? (
        <div className="space-y-8">
          {eligible.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <CheckCircle2 className="w-5 h-5 text-jade-500" />
                <h2 className="text-lg font-heading font-semibold">
                  You may qualify for {eligible.length} scheme{eligible.length > 1 ? "s" : ""}
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {eligible.map((match, i) => (
                  <SchemeCard key={match.scheme.id} scheme={match.scheme} eligibilityScore={match.score} index={i} />
                ))}
              </div>
            </div>
          )}

          {notEligible.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-4">
                <AlertCircle className="w-5 h-5 text-slate-400" />
                <h2 className="text-lg font-heading font-semibold text-slate-400">
                  Other schemes
                </h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {notEligible.slice(0, 4).map((match, i) => (
                  <SchemeCard key={match.scheme.id} scheme={match.scheme} eligibilityScore={match.score} index={i} />
                ))}
              </div>
            </div>
          )}

          {eligible.length === 0 && notEligible.length === 0 && (
            <div className="text-center py-16">
              <UserCheck className="w-12 h-12 text-slate-500 mx-auto mb-3" />
              <p className="text-slate-400">No schemes matched your profile yet</p>
              <p className="text-sm text-slate-600 mt-1">Update your profile for better results</p>
            </div>
          )}
        </div>
      ) : (
        <div className="text-center py-20">
          <Sparkles className="w-12 h-12 text-saffron-500 mx-auto mb-4" />
          <h2 className="text-xl font-semibold font-heading mb-2">Ready to check?</h2>
          <p className="text-slate-400 mb-6">
            We&apos;ll match your profile against all active schemes
          </p>
          <Button variant="saffron" onClick={runCheck} className="gap-2">
            <CheckCircle2 className="w-4 h-4" />
            Check Eligibility
          </Button>
        </div>
      )}
    </div>
  );
}
