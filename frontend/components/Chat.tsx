import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import { Badge, Box, Button, Group, Select, Text, TextInput, Title } from '@mantine/core';
import { IconMicrophone } from '@tabler/icons-react';
import { parseMarkdown } from '../lib/markdown';
import { useWebSocketContext } from '../context/WebSocketContext';
import { VoiceChat } from './VoiceChat';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

export default function Chat() {
  const [agents, setAgents] = useState<any[]>([]);
  const [kbs, setKbs] = useState<any[]>([]);
  const [agentId, setAgentId] = useState<string | null>(null);
  const [kbId, setKbId] = useState<string | null>(null);
  const [messages, setMessages] = useState<{ type: 'user'|'assistant'|'system'; content: string }[]>([]);
  const [input, setInput] = useState('');
  const [typing, setTyping] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const streamingBufferRef = useRef('');
  const [voiceMode, setVoiceMode] = useState(false);
  const [currentAgentName, setCurrentAgentName] = useState<string>('');
  const [agentReady, setAgentReady] = useState(false);
  const { connected, clientId, send, setHandler } = useWebSocketContext();

  useEffect(() => {
    fetch(`${API_BASE}/api/agents`).then(r => r.json()).then(setAgents).catch(() => {});
    fetch(`${API_BASE}/api/knowledge-bases`).then(r => r.json()).then(setKbs).catch(() => {});
  }, []);

  const handleMessage = useCallback((data: any) => {
    switch (data.type) {
      case 'agent_loaded':
        setAgentReady(true);
        setMessages((m) => [...m, { type: 'system', content: 'Agent loaded successfully' }]);
        // Get agent name for voice mode
        const selectedAgent = agents.find(a => a.id === agentId);
        if (selectedAgent) {
          setCurrentAgentName(selectedAgent.name);
        }
        break;
      case 'workflow_loaded':
        setMessages((m) => [...m, { type: 'system', content: data.message || 'Therapeutic session started' }]);
        break;
      case 'workflow_chunk': {
        if (!isStreaming) {
          setIsStreaming(true);
          setTyping(true);
          streamingBufferRef.current ||= '';
        }
        streamingBufferRef.current += data.content || '';
        setStreamingMessage(streamingBufferRef.current);
        break;
      }
      case 'workflow_complete': {
        const hasStream = streamingBufferRef.current && streamingBufferRef.current.trim();
        const finalContent = hasStream ? streamingBufferRef.current : (data.content || '');
        if (finalContent) setMessages((m) => [...m, { type: 'assistant', content: finalContent }]);
        setStreamingMessage('');
        streamingBufferRef.current = '';
        setIsStreaming(false);
        setTyping(false);
        break;
      }
      case 'chat_response':
        setMessages((m) => [...m, { type: 'assistant', content: data.content }]);
        setTyping(false);
        break;
      case 'typing':
        setTyping(Boolean(data.status));
        break;
      case 'error':
        setMessages((m) => [...m, { type: 'system', content: `Error: ${data.message}` }]);
        setTyping(false);
        setIsStreaming(false);
        setStreamingMessage('');
        streamingBufferRef.current = '';
        break;
    }
  }, [isStreaming]);

  useEffect(() => { setHandler(handleMessage); }, [handleMessage, setHandler]);

  // Reset readiness whenever agent selection changes
  useEffect(() => {
    setAgentReady(false);
  }, [agentId, kbId]);

  const loadAgent = () => {
    if (!agentId) return;
    setAgentReady(false);
    send({ type: 'load_agent', agent_id: agentId, kb_id: kbId });
  };

  const sendMessage = () => {
    if (!input.trim()) return;
    if (!agentId && !typing) {
      // allow therapeutic mode without agent
    }
    setMessages((m) => [...m, { type: 'user', content: input }]);
    send({ type: 'chat_message', message: input });
    setInput('');
  };

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Chat</Title>
        <Badge color={connected ? 'green' : 'red'}>{connected ? 'Connected' : 'Disconnected'}</Badge>
      </Group>

      <Group align="end" gap="sm">
        <Select label="Agent" placeholder="Select agent" data={agents.map(a => ({ value: a.id, label: a.name }))} value={agentId}
                onChange={setAgentId} w={260} />
        <Select label="Knowledge Base" placeholder="Optional" data={[{ value: '', label: 'None' }, ...kbs.map(k => ({ value: k.id, label: k.name }))]}
                value={kbId || ''} onChange={(v) => setKbId(v || null)} w={260} />
        <Button onClick={loadAgent} disabled={!agentId || !connected}>Load Agent</Button>
        <Button
          variant="light"
          color="violet"
          leftSection={<IconMicrophone size={16} />}
          onClick={() => setVoiceMode(true)}
          disabled={!connected || !agentId || !agentReady || voiceMode}
        >
          Voice Mode
        </Button>
      </Group>

      {voiceMode && agentId && (
        <Box mt="lg">
          <VoiceChat
            clientId={clientId}
            agentId={agentId}
            agentName={currentAgentName}
            kbId={kbId}
            onClose={() => setVoiceMode(false)}
            onTranscript={(evt) => {
              if (!evt?.text) return;
              if (evt.speaker === 'user') {
                setMessages((m) => [...m, { type: 'user', content: evt.text }]);
              } else if (evt.speaker === 'assistant') {
                setMessages((m) => [...m, { type: 'assistant', content: evt.text }]);
              }
            }}
          />
        </Box>
      )}

      <Box mt="lg" p="md" style={{ background: 'var(--mantine-color-gray-1)', borderRadius: 8, minHeight: 300 }}>
        {messages.length === 0 ? (
          <Text c="dimmed">No messages yet</Text>
        ) : (
          messages.map((m, i) => (
            <Box key={i} mb={8} style={{ textAlign: m.type === 'user' ? 'right' : m.type === 'system' ? 'center' : 'left' }}>
              {m.type === 'system' ? (
                <Box style={{ display: 'inline-block', background: '#fff3bf', color: '#845a00', padding: '6px 10px', borderRadius: 8 }}>
                  <Text size="sm">{m.content}</Text>
                </Box>
              ) : m.type === 'user' ? (
                <Box style={{ display: 'inline-block', background: '#1c7ed6', color: 'white', padding: '8px 12px', borderRadius: 8 }}>
                  <Text size="sm">{m.content}</Text>
                </Box>
              ) : (
                <Box style={{ display: 'inline-block', background: '#f1f3f5', padding: '8px 12px', borderRadius: 8, maxWidth: 700 }}>
                  <div dangerouslySetInnerHTML={{ __html: parseMarkdown(m.content) }} />
                </Box>
              )}
            </Box>
          ))
        )}

        {isStreaming && streamingMessage && (
          <Box mt={8}>
            <Box style={{ display: 'inline-block', background: '#f1f3f5', padding: '8px 12px', borderRadius: 8, maxWidth: 700 }}>
              <div dangerouslySetInnerHTML={{ __html: parseMarkdown(streamingMessage) }} />
              <Text span c="dimmed" ml="xs">…</Text>
            </Box>
          </Box>
        )}

        {typing && !isStreaming && (
          <Text size="sm" c="dimmed" mt="xs">Assistant is typing…</Text>
        )}
      </Box>

      <Group mt="md">
        <TextInput style={{ flex: 1 }} placeholder="Type your message…" value={input} onChange={(e) => setInput(e.currentTarget.value)}
                   onKeyDown={(e) => { if (e.key === 'Enter') sendMessage(); }} />
        <Button onClick={sendMessage} disabled={!connected || (!agentId && !typing) || !input.trim()}>Send</Button>
      </Group>
    </>
  );
}
