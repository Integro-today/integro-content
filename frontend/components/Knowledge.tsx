import { useEffect, useRef, useState } from 'react';
import { ActionIcon, Badge, Box, Button, FileInput, Group, Modal, Text, TextInput, Title } from '@mantine/core';
import { IconTrash, IconTools } from '@tabler/icons-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

function CreateKBModal({ opened, onClose, onSaved }: { opened: boolean; onClose: () => void; onSaved: () => void; }) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [collectionName, setCollectionName] = useState('');

  const save = async () => {
    const body = { name, description, collection_name: collectionName };
    const res = await fetch(`${API_BASE}/api/knowledge-bases`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(`Error: ${err.detail || res.statusText}`);
      return;
    }
    onSaved();
    onClose();
  };

  return (
    <Modal opened={opened} onClose={onClose} title="Create Knowledge Base">
      <TextInput label="Name" value={name} onChange={(e) => setName(e.currentTarget.value)} required />
      <TextInput mt="sm" label="Description" value={description} onChange={(e) => setDescription(e.currentTarget.value)} />
      <TextInput mt="sm" label="Collection Name (optional)" value={collectionName} onChange={(e) => setCollectionName(e.currentTarget.value)} />
      <Group justify="flex-end" mt="md">
        <Button variant="default" onClick={onClose}>Cancel</Button>
        <Button onClick={save}>Create</Button>
      </Group>
    </Modal>
  );
}

function ManageKBModal({ opened, onClose, kb }: { opened: boolean; onClose: () => void; kb: any; }) {
  const [documents, setDocuments] = useState<any[]>([]);
  const [health, setHealth] = useState<any | null>(null);
  const [files, setFiles] = useState<File[] | null>(null);
  const [uploading, setUploading] = useState(false);

  const loadDocs = async () => {
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${kb.id}/documents`);
    setDocuments(await res.json());
  };
  const loadHealth = async () => {
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${kb.id}/health`);
    setHealth(await res.json());
  };

  useEffect(() => {
    if (!opened) return;
    loadDocs();
    loadHealth();
  }, [opened]);

  const repair = async () => {
    if (!confirm('Regenerate missing embeddings?')) return;
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${kb.id}/repair`, { method: 'POST' });
    const data = await res.json();
    if (!res.ok) {
      alert(`Error: ${data.detail || 'Repair failed'}`);
    } else {
      alert(`Repaired: ${data.repaired} | Failed: ${data.failed}`);
    }
    await loadDocs();
    await loadHealth();
  };

  const clearAll = async () => {
    if (!confirm('Delete ALL documents from this knowledge base?')) return;
    await fetch(`${API_BASE}/api/knowledge-bases/${kb.id}/documents`, { method: 'DELETE' });
    await loadDocs();
  };

  const upload = async () => {
    if (!files || files.length === 0) { alert('Select files first'); return; }
    setUploading(true);
    const form = new FormData();
    files.forEach((f) => form.append('files', f));
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${kb.id}/documents`, { method: 'POST', body: form });
    const data = await res.json();
    if (!res.ok) alert(`Error: ${data.detail || 'Upload failed'}`);
    else alert(`Processed ${data.success} file(s). ${data.failed > 0 ? `Failed: ${data.failed}` : ''}`);
    setUploading(false);
    await loadDocs();
  };

  return (
    <Modal opened={opened} onClose={onClose} title={`Manage Knowledge Base: ${kb.name}`} size="lg">
      {health && health.needs_repair && (
        <Box p="sm" mb="sm" style={{ background: '#fff9db', border: '1px solid #ffe066', borderRadius: 8 }}>
          <Group justify="space-between">
            <div>
              <Text fw={600}>Embeddings Need Repair</Text>
              <Text size="sm" c="dimmed">{health.chunks_without_embeddings} / {health.total_chunks} chunks are missing embeddings.</Text>
            </div>
            <Button leftSection={<IconTools size={16} />} color="yellow" variant="filled" onClick={repair} loading={uploading}>Repair Embeddings</Button>
          </Group>
        </Box>
      )}

      <Box mb="md">
        <Text fw={600} mb={6}>Upload Documents</Text>
        <Group>
          <FileInput accept={['.txt','.md','.pdf','.docx','.xlsx','.pptx','.html','.epub','.py','.js','.json','.csv'].join(',')} multiple placeholder="Choose files" value={files} onChange={setFiles} />
          <Button onClick={upload} loading={uploading}>Upload & Process</Button>
        </Group>
      </Box>

      <Group justify="space-between" mb="xs">
        <Text fw={600}>Documents ({documents.length})</Text>
        {documents.length > 0 && <Button color="red" variant="light" onClick={clearAll} leftSection={<IconTrash size={16} />}>Clear All</Button>}
      </Group>

      {documents.length === 0 ? (
        <Box p="lg" style={{ background: 'var(--mantine-color-gray-1)', borderRadius: 8 }}>
          <Text c="dimmed">No documents uploaded yet</Text>
        </Box>
      ) : (
        <Box>
          {documents.map((doc, idx) => (
            <Group key={idx} justify="space-between" p="sm" mb="xs" style={{ background: 'white', borderRadius: 8, border: '1px solid var(--mantine-color-gray-3)' }}>
              <Box>
                <Text size="sm" fw={500}>{doc.file_path} {doc.needs_repair && <Badge color="yellow" ml="xs">Missing embeddings</Badge>}</Text>
                <Text size="xs" c="dimmed">{doc.chunks} chunks{doc.chunks_with_embeddings !== undefined && ` (${doc.chunks_with_embeddings} with embeddings)`}</Text>
              </Box>
              <ActionIcon variant="subtle" color="red" aria-label="delete" onClick={() => alert('Delete per-file coming soon')}>
                <IconTrash size={16} />
              </ActionIcon>
            </Group>
          ))}
        </Box>
      )}
    </Modal>
  );
}

export default function Knowledge() {
  const [kbs, setKbs] = useState<any[]>([]);
  const [opened, setOpened] = useState(false);
  const [manage, setManage] = useState<any | null>(null);

  const load = async () => {
    const res = await fetch(`${API_BASE}/api/knowledge-bases`);
    const data = await res.json();
    setKbs(data);
  };

  useEffect(() => { load(); }, []);

  const remove = async (id: string) => {
    if (!confirm('Delete this knowledge base?')) return;
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${id}`, { method: 'DELETE' });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      alert(`Error: ${err.detail || res.statusText}`);
      return;
    }
    await load();
  };

  return (
    <>
      <Group justify="space-between" mb="md">
        <Title order={2}>Knowledge Base Management</Title>
        <Button onClick={() => setOpened(true)}>Create Knowledge Base</Button>
      </Group>

      {kbs.length === 0 ? (
        <Box p="lg" style={{ background: 'var(--mantine-color-gray-1)', borderRadius: 8 }}>
          <Text c="dimmed">No knowledge bases yet. Create your first knowledge base!</Text>
        </Box>
      ) : (
        <Box>
          {kbs.map((kb) => (
            <Group key={kb.id} justify="space-between" p="md" mb="sm" style={{ background: 'white', borderRadius: 8, border: '1px solid var(--mantine-color-gray-3)' }}>
              <Box>
                <Text fw={600}>{kb.name}</Text>
                <Text size="sm" c="dimmed">{kb.description}</Text>
                {kb.collection_name && <Text size="xs" c="dimmed" mt={6}>Collection: {kb.collection_name}</Text>}
              </Box>
              <Group>
                <Button variant="light" onClick={() => setManage(kb)}>Manage</Button>
                <Button color="red" variant="light" onClick={() => remove(kb.id)} leftSection={<IconTrash size={16} />}>Delete</Button>
              </Group>
            </Group>
          ))}
        </Box>
      )}

      <CreateKBModal opened={opened} onClose={() => setOpened(false)} onSaved={load} />
      {manage && <ManageKBModal opened={!!manage} onClose={() => setManage(null)} kb={manage} />}
    </>
  );
}
