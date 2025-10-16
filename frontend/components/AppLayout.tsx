import { AppShell, Group, Tabs, Title, Container } from '@mantine/core';
import { useRouter } from 'next/router';
import { IconMessages, IconUsers, IconBrain, IconScale } from '@tabler/icons-react';
import { ReactNode } from 'react';

type TabValue = 'chat' | 'agents' | 'knowledge' | 'compare';

export default function AppLayout({ active, children }: { active: TabValue; children: ReactNode }) {
  const router = useRouter();

  const handleChange = (val: string | null) => {
    if (!val) return;
    switch (val as TabValue) {
      case 'chat':
        router.push('/chat');
        break;
      case 'agents':
        router.push('/agents');
        break;
      case 'knowledge':
        router.push('/knowledge-bases');
        break;
      case 'compare':
        router.push('/compare');
        break;
    }
  };

  return (
    <Tabs value={active} onChange={handleChange} keepMounted={false}>
      <AppShell header={{ height: 64 }}>
        <AppShell.Header>
          <Group px="md" h="100%" justify="space-between">
            <Title order={3} style={{ cursor: 'pointer' }} onClick={() => router.push('/chat')}>Integro Labs</Title>
            <Tabs.List>
              <Tabs.Tab value="chat" leftSection={<IconMessages size={16} />}>Chat</Tabs.Tab>
              <Tabs.Tab value="agents" leftSection={<IconUsers size={16} />}>Agents</Tabs.Tab>
              <Tabs.Tab value="knowledge" leftSection={<IconBrain size={16} />}>Knowledge Bases</Tabs.Tab>
              <Tabs.Tab value="compare" leftSection={<IconScale size={16} />}>Compare</Tabs.Tab>
            </Tabs.List>
          </Group>
        </AppShell.Header>
        <AppShell.Main>
          <Container size="lg" py="md">
            {children}
          </Container>
        </AppShell.Main>
      </AppShell>
    </Tabs>
  );
}


