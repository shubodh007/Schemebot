"use client";

import type { Citation } from "@/lib/api/chat";
import { FileText, ExternalLink } from "lucide-react";

interface SourceCitationsProps {
  citations: Citation[];
}

export function SourceCitations({ citations }: SourceCitationsProps) {
  if (!citations || citations.length === 0) return null;

  return (
    <div className="mt-2 space-y-1 px-1">
      <p className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">
        Sources
      </p>
      <div className="flex flex-wrap gap-1.5">
        {citations.map((citation, i) => (
          <a
            key={i}
            href={citation.source_url || "#"}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 px-2 py-1 rounded-md bg-secondary/50 border border-border text-[11px] text-slate-400 hover:text-foreground hover:border-saffron-500/30 transition-colors"
          >
            <FileText className="w-3 h-3" />
            <span className="truncate max-w-[120px]">{citation.title || `Source ${i + 1}`}</span>
            <ExternalLink className="w-2.5 h-2.5" />
          </a>
        ))}
      </div>
    </div>
  );
}
