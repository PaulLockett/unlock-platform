"use client";

import { ReactNode } from "react";
import { RoomProvider as LiveblocksRoomProvider } from "@liveblocks/react";

interface RoomProviderProps {
  roomId: string;
  children: ReactNode;
}

export default function RoomProvider({ roomId, children }: RoomProviderProps) {
  return (
    <LiveblocksRoomProvider id={roomId}>
      {children}
    </LiveblocksRoomProvider>
  );
}
