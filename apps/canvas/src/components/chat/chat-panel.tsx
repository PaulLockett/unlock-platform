"use client";

import { useState, useCallback, useRef, useEffect } from "react";
import { X, Send } from "lucide-react";
import MessageBubble from "./message-bubble";
import OnlinePresence from "./online-presence";

interface ChatMessage {
  id: string;
  author: string;
  content: string;
  timestamp: string;
  isOwn: boolean;
}

interface ChatPanelProps {
  open: boolean;
  onClose: () => void;
  viewName: string;
  currentUserEmail: string;
}

export default function ChatPanel({
  open,
  onClose,
  viewName,
  currentUserEmail,
}: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = useCallback(() => {
    if (!input.trim()) return;

    const newMessage: ChatMessage = {
      id: crypto.randomUUID(),
      author: currentUserEmail.split("@")[0],
      content: input.trim(),
      timestamp: new Date().toLocaleTimeString([], {
        hour: "2-digit",
        minute: "2-digit",
      }),
      isOwn: true,
    };

    setMessages((prev) => [...prev, newMessage]);
    setInput("");

    // In production, this would go through Liveblocks
    // For now, messages are local only
  }, [input, currentUserEmail]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  if (!open) return null;

  return (
    <div className="fixed top-0 right-0 bottom-0 w-full max-w-sm z-[80] bg-charcoal-light border-l border-white/10 flex flex-col">
      {/* Corner accents */}
      <div className="absolute -top-px -left-px w-6 h-6 border-t-2 border-l-2 border-coral" />
      <div className="absolute -bottom-px -left-px w-6 h-6 border-b-2 border-l-2 border-coral" />

      {/* Header */}
      <div className="p-4 border-b border-white/10 flex items-center justify-between shrink-0">
        <div>
          <div className="text-[10px] font-mono tracking-widest text-coral uppercase">
            Live Chat
          </div>
          <div className="text-sm font-display text-sage uppercase mt-0.5">
            {viewName}
          </div>
        </div>
        <div className="flex items-center gap-4">
          <OnlinePresence count={1} />
          <button
            onClick={onClose}
            className="text-white/40 hover:text-white transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto no-scrollbar p-4 space-y-4">
        {messages.length === 0 && (
          <div className="flex items-center justify-center h-full text-white/20 text-xs font-mono tracking-widest text-center">
            No messages yet.
            <br />
            Start the conversation.
          </div>
        )}

        {/* Date divider */}
        {messages.length > 0 && (
          <div className="flex items-center gap-3">
            <div className="flex-1 h-px bg-white/10" />
            <span className="text-[10px] font-mono text-white/30 tracking-widest">
              Today
            </span>
            <div className="flex-1 h-px bg-white/10" />
          </div>
        )}

        {messages.map((msg) => (
          <MessageBubble key={msg.id} {...msg} />
        ))}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="p-4 border-t border-white/10 shrink-0">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-coral/20 flex items-center justify-center text-xs font-mono text-coral border border-coral/30 shrink-0">
            {currentUserEmail.charAt(0).toUpperCase()}
          </div>
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Message the team..."
              rows={2}
              className="w-full bg-charcoal border border-white/10 px-3 py-2 text-xs font-mono text-offwhite placeholder-white/20 focus:outline-none focus:border-coral transition-colors resize-none"
            />
            <div className="flex items-center justify-between mt-2">
              <span className="text-[9px] font-mono text-white/20">
                Enter to send
              </span>
              <button
                onClick={handleSend}
                disabled={!input.trim()}
                className="w-7 h-7 flex items-center justify-center bg-coral text-charcoal hover:bg-coral/90 transition-colors disabled:opacity-30"
              >
                <Send className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
