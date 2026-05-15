"use client";

import { useEffect, useRef } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { useChatStore } from "@/lib/store/chat-store";
import { MessageBubble } from "./MessageBubble";
import { ChatInput } from "./ChatInput";
import { StreamingText } from "./StreamingText";
import { FollowUpSuggestions } from "./FollowUpSuggestions";
import { ProviderSelector } from "./ProviderSelector";
import { SourceCitations } from "./SourceCitations";
import { ChatSkeleton } from "@/components/common/SkeletonLoader";
import { MessageSquare } from "lucide-react";
import { useUIStore } from "@/lib/store/ui-store";

export function ChatInterface() {
  const {
    messages,
    isStreaming,
    streamingContent,
    citations,
    activeSessionId,
  } = useChatStore();
  const { language } = useUIStore();
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, streamingContent]);

  if (!activeSessionId) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-saffron-500/10 to-jade-500/10 border border-saffron-500/20 flex items-center justify-center mx-auto mb-4">
            <MessageSquare className="w-8 h-8 text-saffron-500" />
          </div>
          <h2 className="text-xl font-semibold font-heading mb-2">
            {language === "hi" ? "कोई बातचीत नहीं" : "No conversation selected"}
          </h2>
          <p className="text-slate-400 text-sm leading-relaxed">
            {language === "hi"
              ? "एक नई चैट शुरू करें और सरकारी योजनाओं के बारे में पूछें"
              : "Start a new chat and ask about government schemes you might qualify for"}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b border-border">
        <ProviderSelector />
      </div>

      <div className="flex-1 overflow-y-auto px-4 py-4 space-y-4">
        {messages.length === 0 && !isStreaming && (
          <div className="text-center py-16">
            <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-saffron-500/10 to-jade-500/10 border border-saffron-500/20 flex items-center justify-center mx-auto mb-3">
              <MessageSquare className="w-6 h-6 text-saffron-500" />
            </div>
            <p className="text-slate-400 text-sm">
              {language === "hi" ? "अपना प्रश्न पूछें" : "Ask anything about schemes"}
            </p>
          </div>
        )}

        <AnimatePresence>
          {messages.map((msg) => (
            <motion.div
              key={msg.id}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
            >
              <MessageBubble message={msg} />
            </motion.div>
          ))}
        </AnimatePresence>

        {isStreaming && streamingContent && (
          <div className="flex gap-3">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-saffron-500 to-saffron-400 flex items-center justify-center flex-shrink-0">
              <span className="text-[10px] font-bold text-white">AI</span>
            </div>
            <div className="flex-1 max-w-[80%]">
              <div className="rounded-2xl rounded-tl-sm bg-card border border-border p-4">
                <StreamingText content={streamingContent} />
              </div>
              <SourceCitations citations={citations} />
            </div>
          </div>
        )}

        {isStreaming && !streamingContent && <ChatSkeleton />}

        <div ref={bottomRef} />

        {!isStreaming && messages.length > 0 && (
          <FollowUpSuggestions />
        )}
      </div>

      <div className="border-t border-border p-4">
        <ChatInput />
      </div>
    </div>
  );
}
