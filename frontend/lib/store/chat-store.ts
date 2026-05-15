import { create } from "zustand";
import type { ConversationSummary, MessageResponse, Citation } from "@/lib/api/chat";

interface ChatState {
  sessions: ConversationSummary[];
  activeSessionId: string | null;
  messages: MessageResponse[];
  isStreaming: boolean;
  abortController: AbortController | null;
  streamingContent: string;
  citations: Citation[];
  provider: string;

  setSessions: (sessions: ConversationSummary[]) => void;
  addSession: (session: ConversationSummary) => void;
  removeSession: (id: string) => void;
  setActiveSession: (id: string | null) => void;
  setMessages: (messages: MessageResponse[]) => void;
  addMessage: (message: MessageResponse) => void;
  setIsStreaming: (streaming: boolean) => void;
  setAbortController: (controller: AbortController | null) => void;
  appendStreamToken: (token: string) => void;
  clearStream: () => void;
  setCitations: (citations: Citation[]) => void;
  setProvider: (provider: string) => void;
}

export const useChatStore = create<ChatState>()((set) => ({
  sessions: [],
  activeSessionId: null,
  messages: [],
  isStreaming: false,
  abortController: null,
  streamingContent: "",
  citations: [],
  provider: "openrouter",

  setSessions: (sessions) => set({ sessions }),
  addSession: (session) =>
    set((state) => ({ sessions: [session, ...state.sessions] })),
  removeSession: (id) =>
    set((state) => ({
      sessions: state.sessions.filter((s) => s.id !== id),
      activeSessionId: state.activeSessionId === id ? null : state.activeSessionId,
    })),
  setActiveSession: (id) => set({ activeSessionId: id }),
  setMessages: (messages) => set({ messages }),
  addMessage: (message) =>
    set((state) => ({ messages: [...state.messages, message] })),
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  setAbortController: (controller) => set({ abortController: controller }),
  appendStreamToken: (token) =>
    set((state) => ({ streamingContent: state.streamingContent + token })),
  clearStream: () => set({ streamingContent: "", citations: [] }),
  setCitations: (citations) => set({ citations }),
  setProvider: (provider) => set({ provider }),
}));
