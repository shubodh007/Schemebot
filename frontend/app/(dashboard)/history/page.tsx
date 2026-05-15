"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { chatApi, type ConversationSummary } from "@/lib/api/chat";
import { useChatStore } from "@/lib/store/chat-store";
import { Clock, MessageSquare, Trash2, Sparkles } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";
import { motion } from "framer-motion";

export default function HistoryPage() {
  const router = useRouter();
  const { sessions, setSessions, setActiveSession, removeSession } = useChatStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    chatApi.sessions({ limit: 50 }).then((res) => {
      setSessions(res.sessions);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [setSessions]);

  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await chatApi.deleteSession(id);
      removeSession(id);
    } catch {}
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div>
        <h1 className="text-2xl font-heading font-bold">History</h1>
        <p className="text-sm text-slate-400 mt-1">Your past conversations</p>
      </div>

      {loading ? (
        <div className="space-y-2">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 rounded-xl bg-secondary/50 animate-pulse" />
          ))}
        </div>
      ) : sessions.length > 0 ? (
        <div className="space-y-2">
          {sessions.map((session) => (
            <motion.div
              key={session.id}
              initial={{ opacity: 0, y: 5 }}
              animate={{ opacity: 1, y: 0 }}
              onClick={() => {
                setActiveSession(session.id);
                router.push(`/chat/${session.id}`);
              }}
              className="flex items-center gap-3 p-4 rounded-xl border border-border bg-card hover:border-saffron-500/20 cursor-pointer transition-all group"
            >
              <MessageSquare className="w-4 h-4 text-slate-400 flex-shrink-0" />
              <div className="flex-1 min-w-0">
                <p className="text-sm truncate">{session.title || "New conversation"}</p>
                <p className="text-xs text-slate-500">{formatRelativeTime(session.updated_at)}</p>
              </div>
              <button onClick={(e) => deleteSession(session.id, e)} className="p-1.5 rounded-lg text-slate-500 hover:text-destructive opacity-0 group-hover:opacity-100 transition-all">
                <Trash2 className="w-3.5 h-3.5" />
              </button>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <Clock className="w-12 h-12 text-slate-500 mx-auto mb-3" />
          <p className="text-slate-400">No history yet</p>
          <p className="text-sm text-slate-600 mt-1">Your conversations will appear here</p>
        </div>
      )}
    </div>
  );
}
