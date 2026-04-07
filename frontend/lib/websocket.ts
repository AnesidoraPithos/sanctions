"use client";

import { useEffect, useRef, useState } from "react";

export interface ProgressState {
  step: string;
  percent: number;
  done: boolean;
  error?: string;
}

const WS_BASE =
  process.env.NEXT_PUBLIC_WS_URL ||
  (typeof window !== "undefined"
    ? `ws://${window.location.hostname}:8000`
    : "ws://localhost:8000");

/**
 * useProgress — subscribe to live search progress via WebSocket.
 *
 * @param searchId  The search UUID returned by the API when a search starts.
 *                  Pass null/undefined to disable the hook.
 */
export function useProgress(searchId: string | null | undefined): ProgressState {
  const [state, setState] = useState<ProgressState>({
    step: "Initialising…",
    percent: 0,
    done: false,
  });

  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    if (!searchId) return;

    const url = `${WS_BASE}/ws/progress/${searchId}`;
    let ws: WebSocket;

    try {
      ws = new WebSocket(url);
    } catch {
      // WebSocket not supported or URL invalid — silently degrade
      return;
    }

    wsRef.current = ws;

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data) as ProgressState;
        setState(data);
      } catch {
        // ignore malformed frames
      }
    };

    ws.onerror = () => {
      // Silently degrade — results will still load via HTTP
      setState((prev) => ({ ...prev, done: true }));
    };

    ws.onclose = () => {
      // Nothing to do
    };

    return () => {
      ws.close();
      wsRef.current = null;
    };
  }, [searchId]);

  return state;
}
