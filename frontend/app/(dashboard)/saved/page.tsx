"use client";

import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { schemesApi, type SchemeCard } from "@/lib/api/schemes";
import { SchemeCard as SchemeCardComponent } from "@/components/schemes/SchemeCard";
import { Bookmark, Sparkles } from "lucide-react";

export default function SavedPage() {
  const [savedSchemes, setSavedSchemes] = useState<SchemeCard[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    schemesApi.saved().then((res) => {
      setSavedSchemes(res.saved as unknown as SchemeCard[]);
    }).catch(() => {}).finally(() => setLoading(false));
  }, []);

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-heading font-bold">Saved Schemes</h1>
        <p className="text-sm text-slate-400 mt-1">
          Schemes you have bookmarked for later
        </p>
      </div>

      {loading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {[1, 2].map((i) => (
            <div key={i} className="h-40 rounded-xl bg-secondary/50 animate-pulse" />
          ))}
        </div>
      ) : savedSchemes.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {savedSchemes.map((scheme, i) => (
            <SchemeCardComponent key={scheme.id} scheme={scheme} index={i} />
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <Bookmark className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-400">No saved schemes yet</p>
          <p className="text-sm text-slate-600 mt-1">
            Save schemes to access them quickly later
          </p>
        </div>
      )}
    </div>
  );
}
