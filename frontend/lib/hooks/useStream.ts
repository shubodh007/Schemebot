"use client";

import { useCallback, useRef } from "react";
import { useChatStore } from "@/lib/store/chat-store";
import { streamMessage } from "@/lib/api/chat";

export function useStream() {
  const abortRef = useRef<AbortController | null>(null);
  const {
    setActiveSession,
    addMessage,
    setIsStreaming,
    setAbortController,
    appendStreamToken,
    clearStream,
    setCitations,
    activeSessionId,
  } = useChatStore();

  const sendMessage = useCallback(
    async (content: string, language = "en") => {
      if (!activeSessionId) return;

      const abortController = new AbortController();
      abortRef.current = abortController;
      setAbortController(abortController);
      setIsStreaming(true);
      clearStream();

      addMessage({
        id: crypto.randomUUID(),
        role: "user",
        content,
        citations: [],
        is_partial: false,
        created_at: new Date().toISOString(),
      });

      const currentContent = "";

      await streamMessage(
        activeSessionId,
        { content, language },
        (token) => {
          appendStreamToken(token);
        },
        (citations) => {
          setCitations(citations);
        },
        (messageId) => {
          addMessage({
            id: messageId,
            role: "assistant",
            content: currentContent,
            citations: [],
            is_partial: false,
            created_at: new Date().toISOString(),
          });
          setIsStreaming(false);
          clearStream();
        },
        (error) => {
          console.error("Stream error:", error);
          setIsStreaming(false);
        },
        abortController.signal
      );
    },
    [
      activeSessionId,
      setActiveSession,
      addMessage,
      setIsStreaming,
      setAbortController,
      appendStreamToken,
      clearStream,
      setCitations,
    ]
  );

  const cancelStream = useCallback(() => {
    abortRef.current?.abort();
    setIsStreaming(false);
    clearStream();
  }, [setIsStreaming, clearStream]);

  return { sendMessage, cancelStream };
}
