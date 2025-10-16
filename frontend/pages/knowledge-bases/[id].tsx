import { useEffect, useRef, useState } from 'react';
import { Anchor, Badge, Box, Button, FileInput, Group, Text, Title } from '@mantine/core';
import Link from 'next/link';
import { notifications } from '@mantine/notifications';
import { useRouter } from 'next/router';
import { IconTrash, IconTools } from '@tabler/icons-react';
import AppLayout from '../../components/AppLayout';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

export default function ManageKBPage() {
  const router = useRouter();
  const { id } = router.query as { id?: string };
  const [kb, setKb] = useState<any | null>(null);
  const [documents, setDocuments] = useState<any[]>([]);
  const [kbHealth, setKbHealth] = useState<any | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[] | null>(null);
  const [uploading, setUploading] = useState(false);
  const [repairing, setRepairing] = useState(false);

  useEffect(() => {
    if (!id) return;
    (async () => {
      try {
        const kbRes = await fetch(`${API_BASE}/api/knowledge-bases/${id}`);
        setKb(await kbRes.json());
        await reloadDocs();
        await reloadHealth();
      } catch {}
    })();
  }, [id]);

  const reloadDocs = async () => {
    if (!id) return;
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${encodeURIComponent(id)}/documents`);
    const data = await res.json();
    // Some backends could return raw docs instead of grouped-by-file. Normalize here.
    if (Array.isArray(data) && data.length > 0 && data[0] && data[0].doc_id) {
      const files: Record<string, any> = {};
      for (const d of data) {
        const fp = d.file_path || 'unknown';
        files[fp] = files[fp] || { file_path: fp, chunks: 0, chunks_with_embeddings: 0, chunks_without_embeddings: 0 };
        files[fp].chunks += 1;
        if (d.embedding) files[fp].chunks_with_embeddings += 1;
        else files[fp].chunks_without_embeddings += 1;
      }
      setDocuments(Object.values(files));
    } else {
      setDocuments(data || []);
    }
  };

  const reloadHealth = async () => {
    if (!id) return;
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${id}/health`);
    setKbHealth(await res.json());
  };

  const upload = async () => {
    if (!id || !selectedFiles || selectedFiles.length === 0) {
      notifications.show({ color: 'yellow', title: 'No files', message: 'Select files first.' });
      return;
    }
    setUploading(true);
    const form = new FormData();
    selectedFiles.forEach((f) => form.append('files', f));
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${id}/documents`, { method: 'POST', body: form });
    const data = await res.json();
    setUploading(false);
    if (!res.ok) {
      notifications.show({ color: 'red', title: 'Upload failed', message: data.detail || 'Upload error' });
      return;
    }
    notifications.show({ color: 'green', title: 'Uploaded', message: `Processed ${data.success} file(s).` });
    setSelectedFiles(null);
    await reloadDocs();
  };

  const clearAll = async () => {
    if (!id) return;
    if (!confirm('Delete ALL documents from this knowledge base?')) return;
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${id}/documents`, { method: 'DELETE' });
    if (!res.ok) {
      notifications.show({ color: 'red', title: 'Error', message: 'Failed to clear documents.' });
      return;
    }
    notifications.show({ color: 'green', title: 'Cleared', message: 'All documents removed.' });
    await reloadDocs();
  };

  const repair = async () => {
    if (!id) return;
    if (!confirm('Regenerate embeddings for missing chunks?')) return;
    setRepairing(true);
    const res = await fetch(`${API_BASE}/api/knowledge-bases/${id}/repair`, { method: 'POST' });
    const data = await res.json();
    setRepairing(false);
    if (!res.ok) {
      notifications.show({ color: 'red', title: 'Repair failed', message: data.detail || 'Error' });
      return;
    }
    notifications.show({ color: 'green', title: 'Repaired', message: `Repaired: ${data.repaired}, Failed: ${data.failed}` });
    await reloadDocs();
    await reloadHealth();
  };

  if (!id || !kb) return <AppLayout active="knowledge"><Text>Loading…</Text></AppLayout>;

  return (
    <AppLayout active="knowledge">
      <Group justify="space-between" mb="md">
        <Title order={2}>Manage Knowledge Base: {kb.name}</Title>
        <Anchor component={Link} href="/knowledge-bases" underline="always">Back to knowledge</Anchor>
      </Group>

      {kbHealth && kbHealth.needs_repair && (
        <Box p="sm" mb="sm" style={{ background: '#fff9db', border: '1px solid #ffe066', borderRadius: 8 }}>
          <Group justify="space-between">
            <div>
              <Text fw={600}>Embeddings Need Repair</Text>
              <Text size="sm" c="dimmed">{kbHealth.chunks_without_embeddings} / {kbHealth.total_chunks} missing.</Text>
            </div>
            <Button leftSection={<IconTools size={16} />} color="yellow" onClick={repair} loading={repairing}>Repair Embeddings</Button>
          </Group>
        </Box>
      )}

      <Box mb="md">
        <Text fw={600} mb={6}>Upload Documents</Text>
        <Group>
          <FileInput accept={[ '.txt','.md','.pdf','.docx','.xlsx','.pptx','.html','.epub','.py','.js','.json','.csv' ].join(',')} multiple placeholder="Choose files" value={selectedFiles} onChange={setSelectedFiles} />
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
            </Group>
          ))}
        </Box>
      )}
    </AppLayout>
  );
}


