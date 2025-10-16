import { useEffect, useMemo, useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import { Button, Group, NumberInput, Select, Switch, Text, TextInput, Title, Anchor } from '@mantine/core';
import Link from 'next/link';
import { notifications } from '@mantine/notifications';
import AppLayout from '../../components/AppLayout';

const SimpleMDE = dynamic(() => import('react-simplemde-editor'), { ssr: false });
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

export default function EditAgentPage() {
  const router = useRouter();
  const { id } = router.query as { id?: string };
  const [loading, setLoading] = useState(true);

  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [userId, setUserId] = useState('default');
  const [instructionsMD, setInstructionsMD] = useState<string>('');
  const [stream, setStream] = useState(false);
  const [markdown, setMarkdown] = useState(true);
  const [enableMemory, setEnableMemory] = useState(true);
  const [enableStorage, setEnableStorage] = useState(true);
  const [toolCallLimit, setToolCallLimit] = useState(20);
  const [temperature, setTemperature] = useState(0.7);
  const [models, setModels] = useState<any[]>([]);
  const [kbId, setKbId] = useState('none');
  const [kbs, setKbs] = useState<any[]>([]);

  useEffect(() => {
    fetch(`${API_BASE}/api/knowledge-bases`).then(r => r.json()).then(setKbs).catch(() => {});
  }, []);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const res = await fetch(`${API_BASE}/api/agents/${id}`);
        const agent = await res.json();
        setName(agent.name || '');
        setDescription(agent.description || '');
        setUserId(agent.user_id || 'default');
        setInstructionsMD((agent.instructions || []).join('\n'));
        setStream(Boolean(agent.stream));
        setMarkdown(agent.markdown !== false);
        setEnableMemory(agent.enable_memory !== false);
        setEnableStorage(agent.enable_storage !== false);
        setToolCallLimit(agent.tool_call_limit ?? 20);
        setTemperature(agent.temperature ?? 0.7);
        setModels(agent.models || []);
        setKbId(agent.knowledge_base_id || 'none');
      } catch {
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  const mdeOptions = useMemo(() => ({
    spellChecker: false,
    placeholder: 'Enter one instruction per line...',
    status: false,
    minHeight: '220px',
    maxHeight: '500px',
    autofocus: true,
  }), []);

  const save = async () => {
    if (!id) return;
    const body = {
      name,
      description,
      user_id: userId,
      // Preserve blank lines as empty strings to retain formatting
      instructions: (instructionsMD ?? '').split('\n'),
      models,
      stream,
      markdown,
      enable_memory: enableMemory,
      enable_storage: enableStorage,
      knowledge_base_id: kbId === 'none' ? null : kbId,
      tool_call_limit: toolCallLimit,
      temperature,
    };
    const res = await fetch(`${API_BASE}/api/agents/${id}`, { method: 'PUT', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      notifications.show({ color: 'red', title: 'Error', message: err.detail || res.statusText });
      return;
    }
    notifications.show({ color: 'green', title: 'Saved', message: 'Agent updated successfully.' });
  };

  if (!id || loading) return <AppLayout active="agents"><Text>Loading…</Text></AppLayout>;

  return (
    <AppLayout active="agents">
      <Group justify="space-between" mb="md">
        <Title order={2}>Edit Agent</Title>
        <Group>
          <Anchor component={Link} href="/agents" underline="always">Back to agents</Anchor>
          <Button onClick={save}>Save</Button>
        </Group>
      </Group>

      <Group grow>
        <TextInput label="Name" value={name} onChange={(e) => setName(e.currentTarget.value)} required />
        <TextInput label="User ID" value={userId} onChange={(e) => setUserId(e.currentTarget.value)} />
      </Group>
      <TextInput mt="sm" label="Description" value={description} onChange={(e) => setDescription(e.currentTarget.value)} />

      <div style={{ marginTop: 12 }}>
        <Text fw={600} mb={6}>Instructions (Markdown)</Text>
        <SimpleMDE value={instructionsMD} onChange={(v: string) => setInstructionsMD(v || '')} options={mdeOptions} />
        <Text size="xs" c="dimmed" mt={6}>Each line becomes a separate instruction.</Text>
      </div>

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
    </AppLayout>
  );
}


