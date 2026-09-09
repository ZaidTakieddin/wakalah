"use client";

import { useEffect, useEffectEvent, useState } from "react";
import type { ConnectionStatus, WsEvent } from "@/lib/types";

const STREAM_URL =
  process.env.NEXT_PUBLIC_WAKALAH_WS_URL ?? "ws://127.0.0.1:8000/ws";

export function useWakalahStream(onEvent: (event: WsEvent) => void) {
  const [status, setStatus] = useState<ConnectionStatus>("connecting");

  const handleEvent = useEffectEvent((event: WsEvent) => {
    if (event.type !== "ping") onEvent(event);
  });

  useEffect(() => {
    let socket: WebSocket | undefined;
    let retryTimeout: number | undefined;
    let unmounted = false;

    const connect = () => {
      if (unmounted) return;

      setStatus("connecting");
      socket = new WebSocket(STREAM_URL);

      socket.onopen = () => setStatus("connected");

      socket.onmessage = (message) => {
        try {
          handleEvent(JSON.parse(message.data) as WsEvent);
        } catch {
          // Ignore malformed events and keep the stream connected.
        }
      };

      socket.onerror = () => socket?.close();
    
      socket.onclose = () => {
        if (unmounted) return;
        setStatus("disconnected");
        retryTimeout = window.setTimeout(connect, 1_500);
      };
    };

    connect();

    return () => {
      unmounted = true;
      window.clearTimeout(retryTimeout);
      socket?.close();
    };
  }, []);

  return status;
}
