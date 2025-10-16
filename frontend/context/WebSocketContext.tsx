import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

type WebSocketContextValue = {
  connected: boolean;
  clientId: string;
  send: (obj: any) => void;
  setHandler: (handler: (data: any) => void) => void;
};

const WebSocketContext = createContext<WebSocketContextValue | null>(null);

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimerRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef(true);
  const sendQueueRef = useRef<any[]>([]);
  const messageHandlerRef = useRef<null | ((data: any) => void)>(null);

  const clientId = useMemo(() => {
    if (typeof window === 'undefined') return `client-${Date.now()}`;
    const key = 'integro_client_id';
    const existing = window.localStorage.getItem(key);
    if (existing) return existing;
    const id = `client-${Date.now()}`;
    window.localStorage.setItem(key, id);
    return id;
  }, []);

  const connect = useCallback(() => {
    const isHttps = API_BASE.startsWith('https');
    const protocol = isHttps ? 'wss:' : 'ws:';
    const backendHost = API_BASE.replace('http://', '').replace('https://', '');
    const url = `${protocol}//${backendHost}/ws/${clientId}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => {
      setConnected(true);
      const queue = sendQueueRef.current;
      sendQueueRef.current = [];
      for (const msg of queue) {
        try { ws.send(JSON.stringify(msg)); } catch {}
      }
    };
    ws.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data);
        messageHandlerRef.current && messageHandlerRef.current(data);
      } catch {}
    };
    ws.onclose = () => {
      setConnected(false);
      if (shouldReconnectRef.current && typeof window !== 'undefined') {
        if (reconnectTimerRef.current) window.clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = window.setTimeout(connect, 1500) as unknown as number;
      }
    };
    ws.onerror = () => {
      try { ws.close(); } catch {}
    };
  }, [clientId]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();
    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current && typeof window !== 'undefined') window.clearTimeout(reconnectTimerRef.current);
      try { wsRef.current?.close(); } catch {}
      wsRef.current = null;
    };
  }, [connect]);

  const setHandler = useCallback((handler: (data: any) => void) => {
    messageHandlerRef.current = handler;
    const ws = wsRef.current;
    if (ws) {
      ws.onmessage = (event: MessageEvent) => {
        try {
          const data = JSON.parse(event.data);
          messageHandlerRef.current && messageHandlerRef.current(data);
        } catch {}
      };
    }
  }, []);

  const send = useCallback((obj: any) => {
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(obj));
      return;
    }
    sendQueueRef.current.push(obj);
  }, []);

  const value = useMemo<WebSocketContextValue>(() => ({ connected, clientId, send, setHandler }), [connected, clientId, send, setHandler]);

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const ctx = useContext(WebSocketContext);
  if (!ctx) throw new Error('useWebSocketContext must be used within WebSocketProvider');
  return ctx;
}


