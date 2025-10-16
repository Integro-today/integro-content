import type { AppProps } from 'next/app';
import { MantineProvider, createTheme } from '@mantine/core';
import { Notifications } from '@mantine/notifications';
import '@mantine/core/styles.css';
import 'easymde/dist/easymde.min.css';
import '../styles/mde-overrides.css';
import AppLayout from '../components/AppLayout';
import { useRouter } from 'next/router';
import { WebSocketProvider } from '../context/WebSocketContext';

const theme = createTheme({
  colorScheme: 'light',
  defaultColorScheme: 'light',
});

export default function App({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const pathname = router.pathname;
  const active = pathname.startsWith('/agents') ? 'agents'
    : pathname.startsWith('/knowledge-bases') ? 'knowledge'
    : pathname.startsWith('/compare') ? 'compare'
    : 'chat';
  return (
    <MantineProvider theme={theme} defaultColorScheme="light">
      <Notifications position="top-right" autoClose={3000} />
      <WebSocketProvider>
        <AppLayout active={active as any}>
          <Component {...pageProps} />
        </AppLayout>
      </WebSocketProvider>
    </MantineProvider>
  );
}
