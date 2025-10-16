import { useState } from 'react';
import { Anchor, Button, Group, Text, TextInput, Title } from '@mantine/core';
import Link from 'next/link';
import { notifications } from '@mantine/notifications';
import AppLayout from '../../components/AppLayout';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

export default function NewKBPage() {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [collectionName, setCollectionName] = useState('');

  const save = async () => {
    const body = { name, description, collection_name: collectionName };
    const res = await fetch(`${API_BASE}/api/knowledge-bases`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) });
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      notifications.show({ color: 'red', title: 'Error', message: err.detail || res.statusText });
      return;
    }
    notifications.show({ color: 'green', title: 'Saved', message: 'Knowledge base created.' });
  };

  return (
    <AppLayout active="knowledge">
      <Group justify="space-between" mb="md">
        <Title order={2}>Create Knowledge Base</Title>
        <Group>
          <Anchor component={Link} href="/knowledge-bases" underline="always">Back to knowledge</Anchor>
          <Button onClick={save}>Save</Button>
        </Group>
      </Group>

      <TextInput label="Name" value={name} onChange={(e) => setName(e.currentTarget.value)} required />
      <TextInput mt="sm" label="Description" value={description} onChange={(e) => setDescription(e.currentTarget.value)} />
      <TextInput mt="sm" label="Collection Name (optional)" value={collectionName} onChange={(e) => setCollectionName(e.currentTarget.value)} />

      <Text size="sm" c="dimmed" mt={12}>You can upload documents after creating the knowledge base.</Text>
    </AppLayout>
  );
}


