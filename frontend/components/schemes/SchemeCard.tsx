"use client";

import { motion } from "framer-motion";
import Link from "next/link";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { Bookmark, CheckCircle2, ChevronRight, Building2, Users } from "lucide-react";
import type { SchemeCard as SchemeCardType } from "@/lib/api/schemes";
import { useSchemeStore } from "@/lib/store/scheme-store";

interface SchemeCardProps {
  scheme: SchemeCardType;
  eligibilityScore?: number;
  index?: number;
}

export function SchemeCard({ scheme, eligibilityScore, index = 0 }: SchemeCardProps) {
  const { isSaved, toggleComparison, addToSaved, removeFromSaved } = useSchemeStore();
  const saved = isSaved(scheme.id);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ delay: index * 0.05, duration: 0.3 }}
      className="group relative rounded-xl border border-border bg-card hover:border-saffron-500/20 hover:shadow-lg hover:shadow-saffron-500/5 transition-all duration-300"
    >
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-saffron-500/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity rounded-t-xl" />

      <div className="p-5">
        <div className="flex items-start justify-between gap-3">
          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1.5">
              <Badge variant={scheme.level === "central" ? "saffron" : "slate"}>
                {scheme.level}
              </Badge>
              {eligibilityScore !== undefined && (
                <Badge variant={eligibilityScore > 0.5 ? "jade" : "outline"}>
                  {Math.round(eligibilityScore * 100)}% match
                </Badge>
              )}
            </div>
            <Link href={`/schemes/${scheme.id}`}>
              <h3 className="font-heading font-semibold text-base leading-snug group-hover:text-saffron-500 transition-colors">
                {scheme.title}
              </h3>
            </Link>
            <p className="text-sm text-slate-400 mt-1.5 line-clamp-2 leading-relaxed">
              {scheme.description}
            </p>
          </div>

          <button
            onClick={() => (saved ? removeFromSaved(scheme.id) : addToSaved(scheme.id))}
            className={cn(
              "flex-shrink-0 p-2 rounded-lg transition-colors",
              saved
                ? "bg-saffron-500/10 text-saffron-500"
                : "text-slate-500 hover:text-foreground hover:bg-secondary/50"
            )}
          >
            <Bookmark className={cn("w-4 h-4", saved && "fill-current")} />
          </button>
        </div>

        <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
          {scheme.state_code && (
            <span className="flex items-center gap-1">
              <Building2 className="w-3 h-3" />
              {scheme.state_code}
            </span>
          )}
          {scheme.tags.length > 0 && (
            <div className="flex items-center gap-1.5 flex-wrap">
              {scheme.tags.slice(0, 3).map((tag) => (
                <span key={tag} className="px-1.5 py-0.5 rounded bg-secondary/50 text-[10px]">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>

        <div className="flex items-center gap-2 mt-4">
          <Link href={`/schemes/${scheme.id}`} className="flex-1">
            <Button variant="ghost" size="sm" className="w-full gap-1.5">
              View Details <ChevronRight className="w-3 h-3" />
            </Button>
          </Link>
        </div>
      </div>
    </motion.div>
  );
}
