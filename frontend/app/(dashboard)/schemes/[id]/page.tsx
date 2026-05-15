"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { schemesApi, type SchemeDetail } from "@/lib/api/schemes";
import { useSchemeStore } from "@/lib/store/scheme-store";
import { ArrowLeft, Bookmark, ExternalLink, CheckCircle2, XCircle } from "lucide-react";

export default function SchemeDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { isSaved, addToSaved, removeFromSaved } = useSchemeStore();
  const [scheme, setScheme] = useState<SchemeDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [eligibility, setEligibility] = useState<{ eligible: boolean; score: number; reasons: string[] } | null>(null);

  const schemeId = params.id as string;
  const saved = isSaved(schemeId);

  useEffect(() => {
    if (!schemeId) return;
    schemesApi.get(schemeId).then((res) => {
      setScheme(res.scheme);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [schemeId]);

  const checkEligibility = async () => {
    try {
      const res = await schemesApi.getEligibility(schemeId);
      setEligibility(res);
    } catch {
      // handle error
    }
  };

  if (loading) {
    return (
      <div className="max-w-4xl mx-auto space-y-4">
        <div className="h-8 w-48 bg-secondary/50 rounded animate-pulse" />
        <div className="h-64 bg-secondary/50 rounded-xl animate-pulse" />
      </div>
    );
  }

  if (!scheme) {
    return (
      <div className="text-center py-20">
        <p className="text-slate-400">Scheme not found</p>
        <Button variant="link" onClick={() => router.back()}>Go back</Button>
      </div>
    );
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto"
    >
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-foreground mb-4 transition-colors"
      >
        <ArrowLeft className="w-4 h-4" /> Back
      </button>

      <div className="flex items-start justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-2 mb-2">
            <Badge variant={scheme.level === "central" ? "saffron" : "slate"}>{scheme.level}</Badge>
            {scheme.state_code && <Badge variant="outline">{scheme.state_code}</Badge>}
          </div>
          <h1 className="text-2xl sm:text-3xl font-heading font-bold">{scheme.title}</h1>
          {scheme.ministry && (
            <p className="text-sm text-slate-400 mt-1">Ministry: {scheme.ministry}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <Button
            variant={saved ? "secondary" : "ghost"}
            size="sm"
            onClick={() => (saved ? removeFromSaved(schemeId) : addToSaved(schemeId))}
            className="gap-1.5"
          >
            <Bookmark className={`w-4 h-4 ${saved ? "fill-current" : ""}`} />
            {saved ? "Saved" : "Save"}
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 space-y-6">
          <div className="rounded-xl border border-border bg-card p-6">
            <h2 className="font-heading font-semibold mb-3">Description</h2>
            <p className="text-sm text-slate-300 leading-relaxed">{scheme.description}</p>
          </div>

          {scheme.eligibility_rules && scheme.eligibility_rules.length > 0 && (
            <div className="rounded-xl border border-border bg-card p-6">
              <h2 className="font-heading font-semibold mb-3">Eligibility Criteria</h2>
              <div className="space-y-2">
                {scheme.eligibility_rules.map((rule) => (
                  <div key={rule.id} className="flex items-start gap-2 text-sm">
                    <span className={`mt-0.5 ${rule.is_mandatory ? "text-saffron-500" : "text-slate-500"}`}>
                      {rule.is_mandatory ? "•" : "◦"}
                    </span>
                    <div>
                      <span className="font-medium capitalize">{rule.field_name.replace(/_/g, " ")}</span>
                      <span className="text-slate-400">
                        {" "}{rule.operator}{" "}
                        {typeof rule.value === "object" ? JSON.stringify(rule.value) : String(rule.value)}
                      </span>
                      {rule.description && (
                        <p className="text-xs text-slate-500 mt-0.5">{rule.description}</p>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-heading font-semibold mb-3">Actions</h2>
            <div className="space-y-2">
              {scheme.application_url && (
                <a href={scheme.application_url} target="_blank" rel="noopener noreferrer">
                  <Button variant="saffron" className="w-full gap-2">
                    Apply Now <ExternalLink className="w-3.5 h-3.5" />
                  </Button>
                </a>
              )}
              <Button
                variant="outline"
                className="w-full gap-2"
                onClick={checkEligibility}
              >
                <CheckCircle2 className="w-4 h-4" />
                Check Eligibility
              </Button>
            </div>
          </div>

          {eligibility && (
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className={`rounded-xl border p-5 ${
                eligibility.eligible
                  ? "border-jade-500/30 bg-jade-500/5"
                  : "border-saffron-500/30 bg-saffron-500/5"
              }`}
            >
              <div className="flex items-center gap-2 mb-2">
                {eligibility.eligible ? (
                  <CheckCircle2 className="w-5 h-5 text-jade-500" />
                ) : (
                  <XCircle className="w-5 h-5 text-saffron-500" />
                )}
                <span className="font-medium">
                  {eligibility.eligible ? "You may qualify" : "Eligibility unclear"}
                </span>
                <Badge variant={eligibility.eligible ? "jade" : "saffron"}>
                  {Math.round(eligibility.score * 100)}%
                </Badge>
              </div>
              {eligibility.reasons.length > 0 && (
                <ul className="text-xs text-slate-400 space-y-1 mt-2">
                  {eligibility.reasons.map((r, i) => (
                    <li key={i}>{r}</li>
                  ))}
                </ul>
              )}
            </motion.div>
          )}

          <div className="rounded-xl border border-border bg-card p-5">
            <h2 className="font-heading font-semibold mb-3">Details</h2>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-slate-400">Department</span>
                <span>{scheme.department || "—"}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-slate-400">Level</span>
                <Badge variant={scheme.level === "central" ? "saffron" : "slate"}>{scheme.level}</Badge>
              </div>
              {scheme.state_code && (
                <div className="flex justify-between">
                  <span className="text-slate-400">State</span>
                  <span>{scheme.state_code}</span>
                </div>
              )}
              {scheme.tags.length > 0 && (
                <div className="flex flex-wrap gap-1 pt-2">
                  {scheme.tags.map((tag) => (
                    <Badge key={tag} variant="secondary" className="text-[10px]">{tag}</Badge>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
