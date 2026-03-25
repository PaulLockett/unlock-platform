"use client";

export default function TypingIndicator() {
  return (
    <div className="flex items-center gap-1 px-3 py-2">
      <div
        className="w-1.5 h-1.5 rounded-full bg-white/30 animate-bounce"
        style={{ animationDelay: "0ms" }}
      />
      <div
        className="w-1.5 h-1.5 rounded-full bg-white/30 animate-bounce"
        style={{ animationDelay: "150ms" }}
      />
      <div
        className="w-1.5 h-1.5 rounded-full bg-white/30 animate-bounce"
        style={{ animationDelay: "300ms" }}
      />
    </div>
  );
}
