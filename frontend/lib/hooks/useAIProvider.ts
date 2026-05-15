"use client";

import { useChatStore } from "@/lib/store/chat-store";

const PROVIDERS = [
  { id: "openrouter", name: "OpenRouter", label: "Multi-Model", speed: 4, quality: 4, cost: "free" },
  { id: "gemini", name: "Gemini", label: "Flash 2.0", speed: 5, quality: 3, cost: "free" },
  { id: "claude", name: "Claude", label: "Sonnet 4", speed: 3, quality: 5, cost: "paid" },
  { id: "gpt4o", name: "GPT-4o", label: "Mini", speed: 4, quality: 4, cost: "paid" },
  { id: "groq", name: "Groq", label: "LLaMA 70B", speed: 5, quality: 3, cost: "free" },
] as const;

export function useAIProvider() {
  const { provider, setProvider } = useChatStore();

  const currentProvider = PROVIDERS.find((p) => p.id === provider) || PROVIDERS[0];

  return {
    currentProvider,
    providers: PROVIDERS,
    setProvider,
  };
}
