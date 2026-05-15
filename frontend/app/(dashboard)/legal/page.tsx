"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { Scale, ArrowRight, AlertTriangle, ExternalLink } from "lucide-react";

export default function LegalPage() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setResponse("");
    try {
      const res = await fetch("/api/legal/query", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ query, query_type: "general" }),
      });
      const data = await res.json();
      setResponse(data.response || "No response received");
    } catch {
      setResponse("Failed to get response. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center gap-3 mb-2">
        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-saffron-500/10 to-jade-500/10 border border-saffron-500/20 flex items-center justify-center">
          <Scale className="w-5 h-5 text-saffron-500" />
        </div>
        <div>
          <h1 className="text-2xl font-heading font-bold">Legal Guidance</h1>
          <p className="text-sm text-slate-400">Know your rights, file RTIs, understand the law</p>
        </div>
      </div>

      <div className="p-4 rounded-xl border border-saffron-500/20 bg-saffron-500/5 flex items-start gap-3">
        <AlertTriangle className="w-5 h-5 text-saffron-500 flex-shrink-0 mt-0.5" />
        <p className="text-xs text-slate-400 leading-relaxed">
          This is general legal information, not legal advice. For your specific situation,
          consult a qualified advocate. Information is based on Indian law.
        </p>
      </div>

      <form onSubmit={handleSubmit}>
        <div className="flex gap-2">
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Ask about your legal rights, RTI, or grievance procedures..."
            className="flex-1 bg-card border border-border rounded-xl px-4 py-3 text-sm outline-none focus:border-saffron-500/50 transition-colors"
          />
          <Button type="submit" variant="saffron" disabled={loading || !query.trim()} className="gap-2">
            {loading ? "..." : <><ArrowRight className="w-4 h-4" /> Ask</>}
          </Button>
        </div>
      </form>

      {response && (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="rounded-xl border border-border bg-card p-6"
        >
          <div className="prose prose-sm dark:prose-invert max-w-none">
            {response.split("\n").map((line, i) => (
              <p key={i} className="text-sm text-slate-300 leading-relaxed">{line}</p>
            ))}
          </div>
        </motion.div>
      )}

      <div className="rounded-xl border border-border bg-card p-5">
        <h3 className="font-heading font-semibold mb-3">Common Legal Topics</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {[
            "How to file an RTI application?",
            "What are my consumer rights?",
            "How to file a grievance on CPGRAMS?",
            "Land rights for farmers",
            "Women's legal rights in India",
            "Disability rights under RPWD 2016",
          ].map((topic) => (
            <button
              key={topic}
              onClick={() => setQuery(topic)}
              className="text-left px-3 py-2 rounded-lg bg-secondary/30 border border-border text-sm text-slate-400 hover:text-foreground transition-colors"
            >
              {topic}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
}
