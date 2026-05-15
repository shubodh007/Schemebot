"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useStream } from "@/lib/hooks/useStream";
import { useChatStore } from "@/lib/store/chat-store";
import { useUIStore } from "@/lib/store/ui-store";
import { ArrowUp, Square, Paperclip } from "lucide-react";

export function ChatInput() {
  const [input, setInput] = useState("");
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const { sendMessage, cancelStream } = useStream();
  const { isStreaming } = useChatStore();
  const { language } = useUIStore();

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = "auto";
      textareaRef.current.style.height = `${Math.min(textareaRef.current.scrollHeight, 200)}px`;
    }
  }, [input]);

  const handleSubmit = () => {
    const trimmed = input.trim();
    if (!trimmed || isStreaming) return;
    setInput("");
    sendMessage(trimmed, language);
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="relative max-w-3xl mx-auto">
      <div className="relative flex items-end gap-2 bg-card border border-border rounded-2xl p-2 transition-all duration-200 focus-within:border-saffron-500/50 focus-within:shadow-lg focus-within:shadow-saffron-500/5">
        <Button
          variant="ghost"
          size="icon-sm"
          className="flex-shrink-0 text-slate-400 hover:text-foreground mb-0.5"
          disabled={isStreaming}
        >
          <Paperclip className="w-4 h-4" />
        </Button>

        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={
            language === "hi"
              ? "किसी भी योजना के बारे में पूछें..."
              : language === "te"
              ? "ఏదైనా పథకం గురించి అడగండి..."
              : "Ask about any scheme..."
          }
          rows={1}
          className="flex-1 bg-transparent border-0 outline-none resize-none text-sm py-1.5 placeholder:text-slate-500 max-h-[200px]"
          disabled={isStreaming}
        />

        {isStreaming ? (
          <Button
            variant="secondary"
            size="icon"
            onClick={cancelStream}
            className="flex-shrink-0"
          >
            <Square className="w-4 h-4" />
          </Button>
        ) : (
          <Button
            size="icon"
            onClick={handleSubmit}
            disabled={!input.trim()}
            className="flex-shrink-0 bg-saffron-500 hover:bg-saffron-400 disabled:opacity-50"
          >
            <ArrowUp className="w-4 h-4" />
          </Button>
        )}
      </div>
      <p className="text-[10px] text-slate-600 text-center mt-2">
        Responses are AI-generated. Verify official details before applying.
      </p>
    </div>
  );
}
