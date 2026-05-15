"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { motion } from "framer-motion";
import { Button } from "@/components/ui/button";
import { useChatStore } from "@/lib/store/chat-store";
import { useAuthStore } from "@/lib/store/auth-store";
import { chatApi, type ConversationSummary } from "@/lib/api/chat";
import { Plus, MessageSquare, Trash2, Clock, Sparkles } from "lucide-react";
import { formatRelativeTime } from "@/lib/utils";

export default function ChatListPage() {
  const router = useRouter();
  const { user } = useAuthStore();
  const { sessions, setSessions, setActiveSession, addSession, removeSession } = useChatStore();
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    chatApi.sessions().then((res) => {
      setSessions(res.sessions);
    }).catch(() => {}).finally(() => setLoading(false));
  }, [setSessions]);

  const createSession = async () => {
    try {
      const res = await chatApi.createSession();
      addSession(res.session);
      setActiveSession(res.session.id);
      router.push(`/chat/${res.session.id}`);
    } catch {
      // handle error
    }
  };

  const deleteSession = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await chatApi.deleteSession(id);
      removeSession(id);
    } catch {
      // handle error
    }
  };

  return (
    <div className="max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-heading font-bold">Chat History</h1>
          <p className="text-sm text-slate-400 mt-1">
            Ask about schemes, eligibility, or legal guidance
          </p>
        </div>
        <Button variant="saffron" onClick={createSession} className="gap-2">
          <Plus className="w-4 h-4" />
          New Chat
        </Button>
      </div>

      {loading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-20 rounded-xl bg-secondary/50 animate-pulse" />
          ))}
        </div>
      ) : sessions.length > 0 ? (
        <div className="space-y-2">
          {sessions.map((session: ConversationSummary) => (
            <motion.div
              key={session.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              onClick={() => {
                setActiveSession(session.id);
                router.push(`/chat/${session.id}`);
              }}
              className="flex items-center gap-4 p-4 rounded-xl border border-border bg-card hover:border-saffron-500/20 hover:shadow-md transition-all cursor-pointer group"
            >
              <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-saffron-500/10 to-jade-500/10 border border-saffron-500/20 flex items-center justify-center flex-shrink-0">
                <MessageSquare className="w-5 h-5 text-saffron-500" />
              </div>
              <div className="flex-1 min-w-0">
                <p className="text-sm font-medium truncate">
                  {session.title || "New conversation"}
                </p>
                <div className="flex items-center gap-3 text-xs text-slate-500 mt-1">
                  <span className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {formatRelativeTime(session.updated_at)}
                  </span>
                  <span>{session.message_count} messages</span>
                </div>
              </div>
              <button
                onClick={(e) => deleteSession(session.id, e)}
                className="p-2 rounded-lg text-slate-500 hover:text-destructive hover:bg-destructive/10 opacity-0 group-hover:opacity-100 transition-all"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </motion.div>
          ))}
        </div>
      ) : (
        <div className="text-center py-20">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-saffron-500/10 to-jade-500/10 border border-saffron-500/20 flex items-center justify-center mx-auto mb-4">
            <Sparkles className="w-8 h-8 text-saffron-500" />
          </div>
          <h2 className="text-xl font-semibold font-heading mb-2">No conversations yet</h2>
          <p className="text-slate-400 text-sm mb-6">
            Start a chat to discover schemes you qualify for
          </p>
          <Button variant="saffron" onClick={createSession} className="gap-2">
            <Plus className="w-4 h-4" />
            Start Chatting
          </Button>
        </div>
      )}
    </div>
  );
}
