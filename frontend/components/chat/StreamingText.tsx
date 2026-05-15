"use client";

interface StreamingTextProps {
  content: string;
}

export function StreamingText({ content }: StreamingTextProps) {
  return (
    <div className="text-sm leading-relaxed">
      <span>{content}</span>
      <span className="typing-cursor" />
    </div>
  );
}
