"use client";

import { Lightbulb } from "lucide-react";

const suggestions = [
  "What schemes am I eligible for?",
  "Explain PM Kisan Samman Nidhi",
  "Compare education and health schemes",
  "How to apply for Awas Yojana?",
];

export function FollowUpSuggestions() {
  return (
    <div className="space-y-2 px-1">
      <div className="flex items-center gap-1.5">
        <Lightbulb className="w-3 h-3 text-saffron-500" />
        <span className="text-[10px] text-slate-500 font-medium uppercase tracking-wider">
          Follow-up questions
        </span>
      </div>
      <div className="flex flex-wrap gap-2">
        {suggestions.map((suggestion, i) => (
          <button
            key={i}
            className="px-3 py-1.5 rounded-lg bg-secondary/50 border border-border text-xs text-slate-400 hover:text-foreground hover:border-saffron-500/30 transition-colors"
          >
            {suggestion}
          </button>
        ))}
      </div>
    </div>
  );
}
