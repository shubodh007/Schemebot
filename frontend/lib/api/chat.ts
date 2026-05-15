import { api } from "./client";

export interface Citation {
  scheme_id?: string;
  document_id?: string;
  title?: string;
  relevance?: number;
  source_url?: string;
}

export interface MessageResponse {
  id: string;
  role: string;
  content: string;
  content_hi?: string;
  content_te?: string;
  ai_provider?: string;
  model_name?: string;
  prompt_tokens?: number;
  completion_tokens?: number;
  latency_ms?: number;
  confidence_score?: number;
  citations: Citation[];
  is_partial: boolean;
  feedback_score?: number;
  created_at: string;
}

export interface ConversationSummary {
  id: string;
  title?: string;
  message_count: number;
  ai_provider?: string;
  is_archived: boolean;
  created_at: string;
  updated_at: string;
}

export const chatApi = {
  sessions: (params?: { page?: number; limit?: number }) =>
    api.get<{ sessions: ConversationSummary[]; total: number }>("/chat/sessions", { params: params as Record<string, string | number | boolean | undefined> }),

  createSession: (data?: { provider?: string }) =>
    api.post<{ session: ConversationSummary }>("/chat/sessions", data),

  getSession: (id: string) =>
    api.get<{ session: { id: string; title?: string; messages: MessageResponse[] } }>(`/chat/sessions/${id}`),

  deleteSession: (id: string) => api.delete(`/chat/sessions/${id}`),

  sendMessage: (sessionId: string, data: { content: string; language?: string }) =>
    api.post<Response>(`/chat/sessions/${sessionId}/messages`, data),

  addFeedback: (messageId: string, data: { score: number; comment?: string }) =>
    api.post(`/chat/messages/${messageId}/feedback`, data),
};

export function streamMessage(
  sessionId: string,
  body: { content: string; language?: string },
  onToken: (token: string) => void,
  onCitation: (citations: Citation[]) => void,
  onDone: (messageId: string) => void,
  onError: (error: string) => void,
  signal?: AbortSignal
): Promise<void> {
  const token = localStorage.getItem("access_token");

  return fetch(`/api/chat/sessions/${sessionId}/messages`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify(body),
    credentials: "include",
    signal,
  }).then(async (response) => {
    if (!response.ok) {
      const error = await response.text();
      onError(error || `HTTP ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    if (!reader) {
      onError("No response stream");
      return;
    }

    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.startsWith("data: ")) continue;
        const data = line.slice(6).trim();
        if (!data) continue;

        try {
          const parsed = JSON.parse(data);

          if (parsed.token) {
            onToken(parsed.token);
          }
          if (parsed.citations) {
            onCitation(parsed.citations);
          }
          if (parsed.done) {
            onDone(parsed.message_id);
          }
          if (parsed.error) {
            onError(parsed.error);
          }
        } catch {
          // partial JSON — skip
        }
      }
    }
  }).catch((err) => {
    if (err.name !== "AbortError") {
      onError(err.message || "Connection error");
    }
  });
}
