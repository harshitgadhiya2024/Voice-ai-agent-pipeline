"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import type { ClientControlMessage, ConnectionStatus, ServerMessage } from "@/types";

interface UseWebSocketOptions {
  url: string;
  onAudioChunk?: (data: ArrayBuffer) => void;
  onMessage?: (msg: ServerMessage) => void;
  autoConnect?: boolean;
  maxReconnectAttempts?: number;
}

interface UseWebSocketReturn {
  sendAudio: (pcm: ArrayBuffer | ArrayBufferView) => void;
  sendJSON: (obj: ClientControlMessage) => void;
  connectionStatus: ConnectionStatus;
  connect: () => void;
  disconnect: () => void;
}

export function useWebSocket({
  url,
  onAudioChunk,
  onMessage,
  autoConnect = true,
  maxReconnectAttempts = 5,
}: UseWebSocketOptions): UseWebSocketReturn {
  const wsRef = useRef<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] =
    useState<ConnectionStatus>("disconnected");
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const manuallyClosedRef = useRef(false);

  // Stable refs for callbacks so we don't re-create the socket on every render.
  const onAudioChunkRef = useRef(onAudioChunk);
  const onMessageRef = useRef(onMessage);
  useEffect(() => {
    onAudioChunkRef.current = onAudioChunk;
  }, [onAudioChunk]);
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  const clearReconnectTimer = () => {
    if (reconnectTimerRef.current) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
  };

  const connect = useCallback(() => {
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return;
    }
    manuallyClosedRef.current = false;
    setConnectionStatus(
      reconnectAttemptsRef.current > 0 ? "reconnecting" : "connecting",
    );

    let ws: WebSocket;
    try {
      ws = new WebSocket(url);
    } catch (e) {
      console.error("[ws] failed to construct WebSocket", e);
      setConnectionStatus("error");
      scheduleReconnect();
      return;
    }
    ws.binaryType = "arraybuffer";
    wsRef.current = ws;

    ws.onopen = () => {
      console.log("[ws] connected");
      reconnectAttemptsRef.current = 0;
      setConnectionStatus("connected");
    };

    ws.onmessage = (ev: MessageEvent) => {
      if (ev.data instanceof ArrayBuffer) {
        onAudioChunkRef.current?.(ev.data);
        return;
      }
      if (typeof ev.data === "string") {
        try {
          const parsed = JSON.parse(ev.data) as ServerMessage;
          onMessageRef.current?.(parsed);
        } catch (e) {
          console.warn("[ws] non-JSON text frame", ev.data);
        }
      }
    };

    ws.onerror = (ev) => {
      console.error("[ws] error", ev);
      setConnectionStatus("error");
    };

    ws.onclose = (ev) => {
      console.log("[ws] closed", ev.code, ev.reason);
      wsRef.current = null;
      if (manuallyClosedRef.current) {
        setConnectionStatus("disconnected");
        return;
      }
      scheduleReconnect();
    };
  }, [url]);

  const scheduleReconnect = useCallback(() => {
    if (reconnectAttemptsRef.current >= maxReconnectAttempts) {
      console.warn("[ws] max reconnect attempts reached");
      setConnectionStatus("error");
      return;
    }
    const attempt = reconnectAttemptsRef.current + 1;
    reconnectAttemptsRef.current = attempt;
    const delay = Math.min(500 * 2 ** (attempt - 1), 8000);
    console.log(`[ws] reconnecting in ${delay}ms (attempt ${attempt})`);
    setConnectionStatus("reconnecting");
    clearReconnectTimer();
    reconnectTimerRef.current = setTimeout(() => {
      connect();
    }, delay);
  }, [connect, maxReconnectAttempts]);

  const disconnect = useCallback(() => {
    manuallyClosedRef.current = true;
    clearReconnectTimer();
    reconnectAttemptsRef.current = 0;
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {
        // ignore
      }
      wsRef.current = null;
    }
    setConnectionStatus("disconnected");
  }, []);

  const sendAudio = useCallback((pcm: ArrayBuffer | ArrayBufferView) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    try {
      ws.send(pcm as ArrayBuffer);
    } catch (e) {
      console.warn("[ws] sendAudio failed", e);
    }
  }, []);

  const sendJSON = useCallback((obj: ClientControlMessage) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) return;
    try {
      ws.send(JSON.stringify(obj));
    } catch (e) {
      console.warn("[ws] sendJSON failed", e);
    }
  }, []);

  useEffect(() => {
    if (autoConnect) connect();
    return () => {
      disconnect();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [url]);

  return {
    sendAudio,
    sendJSON,
    connectionStatus,
    connect,
    disconnect,
  };
}
