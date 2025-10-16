import { useEffect, useMemo, useState } from 'react';
import { ActionIcon, Badge, Box, Button, Group, Modal, NumberInput, Select, Switch, Text, TextInput, Title } from '@mantine/core';
import { IconEdit, IconTrash } from '@tabler/icons-react';
import dynamic from 'next/dynamic';
const SimpleMDE = dynamic(() => import('react-simplemde-editor'), { ssr: false });

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

function AgentModal({ opened, onClose, agent, onSaved }: { opened: boolean; onClose: () => void; agent?: any; onSaved: () => void; }) {
  const [name, setName] = useState(agent?.name || '');
  const [description, setDescription] = useState(agent?.description || '');
  const [userId, setUserId] = useState(agent?.user_id || 'default');
  const [instructionsMD, setInstructionsMD] = useState<string>((agent?.instructions || []).join('\n'));
  const [stream, setStream] = useState(Boolean(agent?.stream));
  const [markdown, setMarkdown] = useState(agent?.markdown !== false);
  const [enableMemory, setEnableMemory] = useState(agent?.enable_memory !== false);
  const [enableStorage, setEnableStorage] = useState(agent?.enable_storage !== false);
  const [toolCallLimit, setToolCallLimit] = useState(agent?.tool_call_limit ?? 20);
  const [temperature, setTemperature] = useState(agent?.temperature ?? 0.7);
  const [models, setModels] = useState<any[]>(agent?.models || [{ provider: 'groq', model_id: 'moonshotai/kimi-k2-instruct', params: { temperature: 0.7 } }]);
  const [kbId, setKbId] = useState(agent?.knowledge_base_id || 'none');
  const [kbs, setKbs] = useState<any[]>([]);
  const mdeOptions = useMemo(() => ({
    spellChecker: false,
    placeholder: 'Enter one instruction per line...',
    status: false,
    minHeight: '220px',
    maxHeight: '500px',
    autofocus: true,
  }), []);

  useEffect(() => {
    fetch(`${API_BASE}/api/knowledge-bases`).then(r => r.json()).then(setKbs).catch(() => {});
  }, []);

  useEffect(() => {
    setName(agent?.name || '');
    setDescription(agent?.description || '');
    setUserId(agent?.user_id || 'default');
    setInstructionsMD((agent?.instructions || []).join('\n'));
    setStream(Boolean(agent?.stream));
    setMarkdown(agent?.markdown !== false);
    setEnableMemory(agent?.enable_memory !== false);
    setEnableStorage(agent?.enable_storage !== false);
    setToolCallLimit(agent?.tool_call_limit ?? 20);
    setTemperature(agent?.temperature ?? 0.7);
    setModels(agent?.models || [{ provider: 'groq', model_id: 'moonshotai/kimi-k2-instruct', params: { temperature: 0.7 } }]);
    setKbId(agent?.knowledge_base_id || 'none');
  }, [agent]);

  const availableModels = [
    { provider: 'groq', model_id: 'llama-3.3-70b-versatile', name: 'Llama 3.3 70B Versatile (Groq)' },
    { provider: 'groq', model_id: 'llama-3.1-8b-instant', name: 'Llama 3.1 8B Instant (Groq)' },
    { provider: 'groq', model_id: 'moonshotai/kimi-k2-instruct', name: 'Kimi K2 Instruct (Groq Preview)' },
    { provider: 'anthropic', model_id: 'claude-3-5-sonnet-20241022', name: 'Claude 3.5 Sonnet' },
    { provider: 'openai', model_id: 'gpt-4o', name: 'GPT-4o' },
  ];

  const save = async () => {
    const body = {
      name,
      description,
      user_id: userId,
      instructions: (instructionsMD || '').split('\n').map((s) => s.trim()).filter(Boolean),
      models,
      stream,
      markdown,
      enable_memory: enableMemory,
      enable_storage: enableStorage,
      knowledge_base_id: kbId === 'none' ? null : kbId,
      tool_call_limit: toolCallLimit,
      temperature,
    };
    const method = agent ? 'PUT' : 'POST';
    const url = agent ? `${API_BASE}/api/agents/${agent.id}` : `${API_BASE}/api/agents`;
    const res = await fetch(url, { method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(`Error: ${err.detail || res.statusText}`);
      return;
    }
    onSaved();
    onClose();
  };

  return (
    <Modal
      opened={opened}
      onClose={onClose}
      title={agent ? 'Edit Agent' : 'Create Agent'}
      size="xl"
    >
      <Group grow>
        <TextInput label="Name" value={name} onChange={(e) => setName(e.currentTarget.value)} required />
        <TextInput label="User ID" value={userId} onChange={(e) => setUserId(e.currentTarget.value)} />
      </Group>
      <TextInput mt="sm" label="Description" value={description} onChange={(e) => setDescription(e.currentTarget.value)} />
      <Box mt="sm">
        <Text fw={600} mb={6}>Instructions (Markdown)</Text>
        <SimpleMDE
          value={instructionsMD}
          onChange={(v: string) => setInstructionsMD(v || '')}
          options={mdeOptions}
        />
        <Text size="xs" c="dimmed" mt={6}>Each line becomes a separate instruction.</Text>
      </Box>

      <Group mt="md">
        <Switch label="Streaming" checked={stream} onChange={(e) => setStream(e.currentTarget.checked)} />
        <Switch label="Markdown" checked={markdown} onChange={(e) => setMarkdown(e.currentTarget.checked)} />
        <Switch label="Memory" checked={enableMemory} onChange={(e) => setEnableMemory(e.currentTarget.checked)} />
        <Switch label="Storage" checked={enableStorage} onChange={(e) => setEnableStorage(e.currentTarget.checked)} />
      </Group>

      <Group mt="md" grow>
        <NumberInput label="Tool Call Limit" value={toolCallLimit} onChange={(v) => setToolCallLimit(Number(v) || 1)} min={1} max={100} />
        <NumberInput label="Temperature" value={temperature} onChange={(v) => setTemperature(Number(v) || 0)} min={0} max={1} step={0.1} />
      </Group>

      <Select mt="md" label="Knowledge Base" value={kbId || 'none'} onChange={(v) => setKbId(v || 'none')} data={[{ value: 'none', label: 'None' }, ...kbs.map((kb) => ({ value: kb.id, label: kb.name }))]} />

      <Group justify="flex-end" mt="lg">
        <Button variant="default" onClick={onClose}>Cancel</Button>
        <Button onClick={save}>Save</Button>
      </Group>
    </Modal>
  );
}

export default function Agents() {
  const [agents, setAgents] = useState<any[]>([]);
  const router = require('next/router').useRouter();

  const load = async () => {
    const res = await fetch(`${API_BASE}/api/agents`);
    const data = await res.json();
    setAgents(data);
  };

  useEffect(() => { load(); }, []);

  const remove = async (id: string) => {
    if (!confirm('Delete this agent?')) return;
    const res = await fetch(`${API_BASE}/api/agents/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(`Error: ${err.detail || res.statusText}`);
      return;
    }
    await load();
  };

  const openEdit = (agent: any) => {
    router.push(`/agents/${agent.id}`);
  };

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Agent Management</Title>
        <Button onClick={() => router.push('/agents/new')}>Create Agent</Button>
      </Group>

      {agents.length === 0 ? (
        <Box p="lg" style={{ background: 'var(--mantine-color-gray-1)', borderRadius: 8 }}>
          <Text c="dimmed">No agents yet. Create your first agent!</Text>
        </Box>
      ) : (
        <Box>
          {agents.map((agent) => (
            <Group key={agent.id} justify="space-between" p="md" mb="sm" style={{ background: 'white', borderRadius: 8, border: '1px solid var(--mantine-color-gray-3)' }}>
              <Box>
                <Text fw={600}>{agent.name}</Text>
                <Text size="sm" c="dimmed">{agent.description}</Text>
                <Group gap="xs" mt={6}>
                  <Badge color="gray">User: {agent.user_id || 'default'}</Badge>
                  {agent.knowledge_base_id && <Badge color="indigo">Has Knowledge Base</Badge>}
                </Group>
              </Box>
              <Group>
                <ActionIcon variant="default" onClick={() => openEdit(agent)}><IconEdit size={16} /></ActionIcon>
                <ActionIcon color="red" variant="light" onClick={() => remove(agent.id)}><IconTrash size={16} /></ActionIcon>
              </Group>
            </Group>
          ))}
        </Box>
      )}
      {/* Editor moved to route-based pages: /agents/new and /agents/[id] */}
    </>
  );
}
