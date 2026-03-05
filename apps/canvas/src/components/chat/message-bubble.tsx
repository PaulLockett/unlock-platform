"use client";

interface MessageBubbleProps {
  author: string;
  content: string;
  timestamp: string;
  isOwn: boolean;
}

export default function MessageBubble({
  author,
  content,
  timestamp,
  isOwn,
}: MessageBubbleProps) {
  const initial = author.charAt(0).toUpperCase();

  return (
    <div className={`flex gap-3 ${isOwn ? "flex-row-reverse" : ""}`}>
      {/* Avatar */}
      <div
        className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-mono shrink-0 ${
          isOwn
            ? "bg-coral/20 text-coral border border-coral/30"
            : "bg-white/[0.06] text-white/60 border border-white/10"
        }`}
      >
        {initial}
      </div>

      {/* Content */}
      <div className={`max-w-[75%] ${isOwn ? "text-right" : ""}`}>
        <div className="flex items-center gap-2 mb-1">
          <span className="text-[10px] font-mono text-white/40">
            {isOwn ? "You" : author}
          </span>
          <span className="text-[9px] font-mono text-white/20">
            {timestamp}
          </span>
        </div>
        <div
          className={`px-3 py-2 text-xs font-mono ${
            isOwn
              ? "bg-coral/10 border border-coral/20 text-offwhite"
              : "bg-white/[0.04] border border-white/[0.06] text-white/80"
          }`}
        >
          {content}
        </div>
      </div>
    </div>
  );
}
