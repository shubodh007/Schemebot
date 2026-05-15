"use client";

import ReactMarkdown from "react-markdown";
import { cn } from "@/lib/utils";
import type { MessageResponse } from "@/lib/api/chat";
import { SourceCitations } from "./SourceCitations";
import { Bot, User } from "lucide-react";

interface MessageBubbleProps {
  message: MessageResponse;
}

export function MessageBubble({ message }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={cn("flex gap-3", isUser ? "flex-row-reverse" : "")}>
      <div
        className={cn(
          "w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0",
          isUser
            ? "bg-slate-700"
            : "bg-gradient-to-br from-saffron-500 to-saffron-400"
        )}
      >
        {isUser ? (
          <User className="w-4 h-4 text-slate-300" />
        ) : (
          <Bot className="w-4 h-4 text-white" />
        )}
      </div>

      <div
        className={cn(
          "max-w-[80%] space-y-2",
          isUser ? "items-end" : "items-start"
        )}
      >
        <div
          className={cn(
            "rounded-2xl px-4 py-3 text-sm leading-relaxed",
            isUser
              ? "bg-saffron-500 text-white rounded-tr-sm"
              : "bg-card border border-border rounded-tl-sm"
          )}
        >
          {isUser ? (
            <p className="whitespace-pre-wrap">{message.content}</p>
          ) : (
            <div className="prose prose-sm dark:prose-invert max-w-none">
              <ReactMarkdown
                components={{
                  a: ({ href, children }) => (
                    <a
                      href={href}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-saffron-500 hover:text-saffron-400 underline underline-offset-2"
                    >
                      {children}
                    </a>
                  ),
                  ul: ({ children }) => (
                    <ul className="list-disc pl-4 space-y-1">{children}</ul>
                  ),
                  ol: ({ children }) => (
                    <ol className="list-decimal pl-4 space-y-1">{children}</ol>
                  ),
                  code: ({ children }) => (
                    <code className="bg-secondary/50 px-1.5 py-0.5 rounded text-xs">
                      {children}
                    </code>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            </div>
          )}
        </div>

        {!isUser && message.citations && message.citations.length > 0 && (
          <SourceCitations citations={message.citations} />
        )}

        {message.confidence_score && !isUser && (
          <div className="flex items-center gap-2 px-1">
            <div className="h-1 flex-1 max-w-[100px] bg-secondary rounded-full overflow-hidden">
              <div
                className="h-full bg-jade-500 rounded-full transition-all"
                style={{ width: `${message.confidence_score * 100}%` }}
              />
            </div>
            <span className="text-[10px] text-slate-500">
              {Math.round(message.confidence_score * 100)}% confidence
            </span>
          </div>
        )}
      </div>
    </div>
  );
}
