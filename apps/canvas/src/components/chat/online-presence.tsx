"use client";

interface OnlinePresenceProps {
  count: number;
}

export default function OnlinePresence({ count }: OnlinePresenceProps) {
  return (
    <div className="flex items-center gap-2">
      <div className="w-2 h-2 rounded-full bg-sage animate-pulse" />
      <span className="text-[10px] font-mono tracking-widest text-white/40">
        {count} Online
      </span>
    </div>
  );
}
