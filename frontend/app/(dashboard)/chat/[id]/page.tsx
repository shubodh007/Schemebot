"use client";

import { useEffect } from "react";
import { useParams } from "next/navigation";
import { ChatInterface } from "@/components/chat/ChatInterface";
import { chatApi } from "@/lib/api/chat";
import { useChatStore } from "@/lib/store/chat-store";

export default function ChatSessionPage() {
  const params = useParams();
  const { setActiveSession, setMessages, activeSessionId } = useChatStore();
  const sessionId = params.id as string;

  useEffect(() => {
    if (sessionId && sessionId !== activeSessionId) {
      setActiveSession(sessionId);
      chatApi.getSession(sessionId).then((res) => {
        setMessages(res.session.messages || []);
      }).catch(() => {
        // handle error
      });
    }
  }, [sessionId, activeSessionId, setActiveSession, setMessages]);

  return <ChatInterface />;
}
