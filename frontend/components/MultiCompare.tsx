import { useEffect, useMemo, useRef, useState } from 'react';
import { Badge, Box, Button, Group, Select, SimpleGrid, Text, TextInput, Title } from '@mantine/core';
import { parseMarkdown } from '../lib/markdown';

type ProviderKey = 'integro' | 'openai' | 'anthropic' | 'gemini';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

export default function MultiCompare() {
  const [agents, setAgents] = useState<any[]>([]);
  const [knowledgeBases, setKnowledgeBases] = useState<any[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<string | null>(null);
  const [selectedKB, setSelectedKB] = useState<string | null>(null);
  const [agentLoaded, setAgentLoaded] = useState(false);
  const [loadedAgentName, setLoadedAgentName] = useState('');
  const [loadedKBName, setLoadedKBName] = useState('');

  const [message, setMessage] = useState('');

  const [providerMessages, setProviderMessages] = useState<Record<ProviderKey, any[]>>({
    integro: [], openai: [], anthropic: [], gemini: []
  });
  const [sharedConversationHistory, setSharedConversationHistory] = useState<{ role: 'user' | 'assistant'; content: string }[]>([]);
  const [streamingMessages, setStreamingMessages] = useState<Record<ProviderKey, string>>({
    integro: '', openai: '', anthropic: '', gemini: ''
  });
  const [isStreaming, setIsStreaming] = useState<Record<ProviderKey, boolean>>({
    integro: false, openai: false, anthropic: false, gemini: false
  });
  const streamingBuffers = useRef<Record<ProviderKey, string>>({
    integro: '', openai: '', anthropic: '', gemini: ''
  });

  const [isConnected, setIsConnected] = useState(false);
  const [availableProviders, setAvailableProviders] = useState<Record<string, any>>({});
  const [enabledProviders, setEnabledProviders] = useState<Record<ProviderKey, boolean>>({
    integro: true, openai: true, anthropic: true, gemini: true
  });

  const wsRef = useRef<WebSocket | null>(null);
  const clientIdRef = useRef(`multi-agent-${Date.now()}`);
  const columnRefs = useRef<Record<ProviderKey, HTMLDivElement | null>>({
    integro: null, openai: null, anthropic: null, gemini: null
  });

  useEffect(() => {
    fetchAgents();
    fetchKnowledgeBases();
    connectWS();
    return () => { try { wsRef.current?.close(); } catch {} };
  }, []);

  const fetchAgents = async () => {
    try { const r = await fetch(`${API_BASE}/api/agents`); setAgents(await r.json()); } catch {}
  };
  const fetchKnowledgeBases = async () => {
    try { const r = await fetch(`${API_BASE}/api/knowledge-bases`); setKnowledgeBases(await r.json()); } catch {}
  };

  const connectWS = () => {
    const isHttps = API_BASE.startsWith('https');
    const protocol = isHttps ? 'wss:' : 'ws:';
    const backendHost = API_BASE.replace('http://', '').replace('https://', '');
    const url = `${protocol}//${backendHost}/ws/multi-agent/${clientIdRef.current}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;
    ws.onopen = () => setIsConnected(true);
    ws.onclose = () => { setIsConnected(false); setTimeout(connectWS, 1500); };
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      handleWSMessage(data);
    };
  };

  const handleWSMessage = (data: any) => {
    switch (data.type) {
      case 'multi_agent_ready':
        setAvailableProviders(data.providers || {});
        break;
      case 'agent_loaded': {
        setAgentLoaded(true);
        const agent = agents.find((a) => a.id === data.agent_id);
        const kb = knowledgeBases.find((k) => k.id === data.kb_id);
        setLoadedAgentName(agent?.name || data.agent_id);
        setLoadedKBName(kb?.name || '');
        break;
      }
      case 'typing_status': {
        const providers = data.providers || {};
        const next: Record<ProviderKey, boolean> = { ...isStreaming };
        (Object.keys(next) as ProviderKey[]).forEach((p) => {
          if (typeof providers[p] === 'boolean') next[p] = providers[p];
        });
        setIsStreaming(next);
        break;
      }
      case 'provider_chunk': {
        const provider: ProviderKey = data.provider;
        const content: string = data.content || '';
        streamingBuffers.current[provider] += content;
        setStreamingMessages((prev) => ({ ...prev, [provider]: streamingBuffers.current[provider] }));
        setIsStreaming((prev) => ({ ...prev, [provider]: true }));
        break;
      }
      case 'provider_complete': {
        const provider: ProviderKey = data.provider;
        const finalContent = streamingBuffers.current[provider] || data.content || '';
        if (finalContent) {
          setProviderMessages((prev) => ({
            ...prev,
            [provider]: [...prev[provider], { type: 'assistant', content: finalContent, timestamp: new Date() }]
          }));
          if (provider === 'integro') {
            setSharedConversationHistory((prev) => [...prev, { role: 'assistant', content: finalContent }]);
          }
        }
        streamingBuffers.current[provider] = '';
        setStreamingMessages((prev) => ({ ...prev, [provider]: '' }));
        setIsStreaming((prev) => ({ ...prev, [provider]: false }));
        break;
      }
      case 'provider_error': {
        const provider: ProviderKey = data.provider;
        setProviderMessages((prev) => ({
          ...prev,
          [provider]: [...prev[provider], { type: 'assistant', content: `Error: ${data.error}`, timestamp: new Date() }]
        }));
        setIsStreaming((prev) => ({ ...prev, [provider]: false }));
        break;
      }
      default:
        break;
    }
  };

  const loadIntegroAgent = () => {
    if (!selectedAgent || !wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) return;
    wsRef.current.send(JSON.stringify({ type: 'load_agent', agent_id: selectedAgent, kb_id: selectedKB }));
  };

  const sendCompare = () => {
    if (!message.trim() || !isConnected || !agentLoaded || !wsRef.current) return;
    const history = [...sharedConversationHistory, { role: 'user' as const, content: message }];
    setSharedConversationHistory(history);
    const userMsg = { type: 'user', content: message, timestamp: new Date() };
    setProviderMessages((prev) => ({
      integro: [...prev.integro, userMsg],
      openai: [...prev.openai, userMsg],
      anthropic: [...prev.anthropic, userMsg],
      gemini: [...prev.gemini, userMsg]
    }));
    streamingBuffers.current = { integro: '', openai: '', anthropic: '', gemini: '' };
    setIsStreaming({ integro: true, openai: true, anthropic: true, gemini: true });
    wsRef.current.send(JSON.stringify({ type: 'multi_agent_message', message, conversation_history: history }));
    setMessage('');
  };

  useEffect(() => {
    (Object.keys(columnRefs.current) as ProviderKey[]).forEach((provider) => {
      const ref = columnRefs.current[provider];
      if (ref && enabledProviders[provider]) ref.scrollTop = ref.scrollHeight;
    });
  }, [providerMessages, streamingMessages, enabledProviders]);

  const toggleProvider = (provider: ProviderKey) => {
    setEnabledProviders((prev) => {
      const next = { ...prev, [provider]: !prev[provider] };
      const count = (Object.values(next) as boolean[]).filter(Boolean).length;
      if (count === 0) return prev; // ensure at least one enabled
      return next;
    });
  };

  const renderProviderColumn = (provider: ProviderKey, displayName: string) => {
    const msgs = providerMessages[provider] || [];
    const streamingContent = streamingMessages[provider];
    const streaming = isStreaming[provider];
    const isAvailable = provider === 'integro' || availableProviders[provider] !== undefined;
    return (
      <Box key={provider} style={{ background: 'white', borderRadius: 8, border: '1px solid var(--mantine-color-gray-3)', overflow: 'hidden', display: 'flex', flexDirection: 'column' }}>
        <Box style={{ background: 'var(--mantine-color-gray-1)', padding: '10px 12px', borderBottom: '1px solid var(--mantine-color-gray-3)' }}>
          <Group justify="space-between">
            <Group>
              <Box style={{ width: 10, height: 10, borderRadius: 9999, background: isAvailable ? '#40c057' : '#fa5252' }} />
              <Text fw={600}>{displayName}</Text>
            </Group>
            {!isAvailable && <Text size="sm" c="red">API key not configured</Text>}
          </Group>
        </Box>
        <Box ref={(el: HTMLDivElement | null) => { columnRefs.current[provider] = el; }} style={{ padding: 12, overflowY: 'auto', flex: 1 }}>
          {msgs.map((m, idx) => (
            <Box key={idx} mb={8} style={{ textAlign: m.type === 'user' ? 'right' : 'left' }}>
              {m.type === 'user' ? (
                <Box style={{ display: 'inline-block', background: '#1c7ed6', color: 'white', padding: '8px 12px', borderRadius: 8 }}>
                  <Text size="sm">{m.content}</Text>
                </Box>
              ) : (
                <Box style={{ display: 'inline-block', background: '#f1f3f5', padding: '8px 12px', borderRadius: 8, maxWidth: 700 }}>
                  <div dangerouslySetInnerHTML={{ __html: parseMarkdown(m.content) }} />
                </Box>
              )}
            </Box>
          ))}
          {streaming && streamingContent && (
            <Box mb={8}>
              <Box style={{ display: 'inline-block', background: '#f1f3f5', padding: '8px 12px', borderRadius: 8, maxWidth: 700 }}>
                <div dangerouslySetInnerHTML={{ __html: parseMarkdown(streamingContent) }} />
                <Text span c="dimmed" ml="xs">…</Text>
              </Box>
            </Box>
          )}
          {streaming && !streamingContent && (
            <Text size="sm" c="dimmed">Typing…</Text>
          )}
        </Box>
      </Box>
    );
  };

  const gridCols = useMemo(() => {
    const count = (Object.values(enabledProviders) as boolean[]).filter(Boolean).length || 1;
    return Math.min(count, 4);
  }, [enabledProviders]);

  return (
    <Box>
      <Group mb="sm" justify="space-between">
        <Title order={2}>AI Model Comparison</Title>
        <Group gap="xs">
          <Text size="sm" c="dimmed">Compare:</Text>
          <Button size="xs" variant={enabledProviders.integro ? 'light' : 'default'} onClick={() => toggleProvider('integro')}>
            {enabledProviders.integro && <Badge mr={6} color="blue">on</Badge>}Integro
          </Button>
          <Button size="xs" variant={enabledProviders.openai ? 'light' : 'default'} onClick={() => toggleProvider('openai')}>
            {enabledProviders.openai && <Badge mr={6} color="green">on</Badge>}OpenAI
          </Button>
          <Button size="xs" variant={enabledProviders.anthropic ? 'light' : 'default'} onClick={() => toggleProvider('anthropic')}>
            {enabledProviders.anthropic && <Badge mr={6} color="grape">on</Badge>}Claude
          </Button>
          <Button size="xs" variant={enabledProviders.gemini ? 'light' : 'default'} onClick={() => toggleProvider('gemini')}>
            {enabledProviders.gemini && <Badge mr={6} color="yellow">on</Badge>}Gemini
          </Button>
        </Group>
      </Group>

      <Group mb="md" justify="space-between">
        <Group>
          <Badge color={isConnected ? 'green' : 'red'}>{isConnected ? 'Connected' : 'Disconnected'}</Badge>
          {agentLoaded && (
            <Badge color="teal" variant="light">
              {loadedAgentName}{loadedKBName ? ` + ${loadedKBName}` : ''}
            </Badge>
          )}
        </Group>
        <Group>
          <Select
            placeholder="Select Agent..."
            value={selectedAgent || ''}
            onChange={setSelectedAgent}
            data={agents.map((a) => ({ value: a.id, label: a.name }))}
            w={260}
          />
          <Select
            placeholder="KB (Optional)"
            value={selectedKB || ''}
            onChange={setSelectedKB}
            data={[{ value: '', label: 'No KB' }, ...knowledgeBases.map((k) => ({ value: k.id, label: k.name }))]}
            w={260}
          />
          <Button onClick={loadIntegroAgent} disabled={!selectedAgent || !isConnected}>Load Agent</Button>
        </Group>
      </Group>

      <Group mb="md">
        <TextInput style={{ flex: 1 }} placeholder={agentLoaded ? 'Type your message to compare responses...' : 'Load an agent first...'} value={message}
                   onChange={(e) => setMessage(e.currentTarget.value)} onKeyDown={(e) => { if (e.key === 'Enter') sendCompare(); }} />
        <Button onClick={sendCompare} disabled={!isConnected || !message.trim() || !agentLoaded}>Compare</Button>
      </Group>

      <SimpleGrid cols={gridCols} spacing="md">
        {enabledProviders.integro && renderProviderColumn('integro', 'Integro')}
        {enabledProviders.openai && renderProviderColumn('openai', 'OpenAI ChatGPT')}
        {enabledProviders.anthropic && renderProviderColumn('anthropic', 'Anthropic Claude')}
        {enabledProviders.gemini && renderProviderColumn('gemini', 'Google Gemini')}
      </SimpleGrid>
    </Box>
  );
}
