import { useCallback, useEffect, useState } from 'react';
import {
  LiveKitRoom,
  RoomAudioRenderer,
  useLocalParticipant,
  useConnectionState,
  ConnectionState,
  useTracks,
  useDataChannel,
} from '@livekit/components-react';
import { Room, RoomEvent, Track, createLocalAudioTrack, LocalAudioTrack } from 'livekit-client';
import { Box, Button, Group, Text, Badge, Loader, Stack } from '@mantine/core';
import { IconMicrophone, IconMicrophoneOff, IconPhone, IconPhoneOff } from '@tabler/icons-react';

const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8888';

interface VoiceChatProps {
  clientId: string;
  agentId: string | null;
  agentName?: string;
  kbId: string | null;
  onClose?: () => void;
  onTranscript?: (evt: { speaker: 'user'|'assistant'; text: string }) => void;
}

export function VoiceChat({ clientId, agentId, agentName, kbId, onClose, onTranscript }: VoiceChatProps) {
  const [token, setToken] = useState<string>('');
  const [roomName, setRoomName] = useState<string>('');
  const [livekitUrl, setLivekitUrl] = useState<string>('');
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function initializeVoiceSession() {
      try {
        // Preflight microphone permission
        try {
          const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
          // Release the preflight stream so LiveKit can create its own track
          stream.getTracks().forEach((t) => t.stop());
        } catch (permErr) {
          throw new Error('Microphone access is required for voice mode. Please allow mic permission and try again.');
        }

        // Helper: start voice session with brief retry to avoid race with agent load on live
        const startVoiceWithRetry = async (attempts: number = 4): Promise<any> => {
          let lastErr: any = null;
          for (let i = 0; i < attempts; i++) {
            const res = await fetch(`${API_BASE}/api/voice-session/start?client_id=${clientId}`, { method: 'POST' });
            if (res.ok) {
              return await res.json();
            }
            try {
              const errJson = await res.json();
              const detail = (errJson && errJson.detail) ? String(errJson.detail) : '';
              const isRace = res.status === 400 && detail.toLowerCase().includes('no agent loaded');
              if (isRace && i < attempts - 1) {
                // Exponential backoff: 150ms, 300ms, 600ms
                const delay = 150 * Math.pow(2, i);
                await new Promise(r => setTimeout(r, delay));
                continue;
              }
              lastErr = new Error(detail || 'Failed to start voice session');
            } catch {
              lastErr = new Error('Failed to start voice session');
            }
            break;
          }
          throw lastErr || new Error('Failed to start voice session');
        };

        // Start voice session (with retry protection)
        const sessionData = await startVoiceWithRetry();
        setRoomName(sessionData.room_name);

        // Get LiveKit token
        const tokenRes = await fetch(`${API_BASE}/api/livekit-token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            room_name: sessionData.room_name,
            participant_name: clientId,
            agent_id: sessionData.agent_id || agentId,
            kb_id: sessionData.kb_id || kbId,
            agent_name: sessionData.agent_name || agentName || 'AI Assistant',
          }),
        });

        if (!tokenRes.ok) {
          const error = await tokenRes.json();
          throw new Error(error.detail || 'Failed to get LiveKit token');
        }

        const tokenData = await tokenRes.json();
        setToken(tokenData.token);
        setLivekitUrl(tokenData.livekit_url || 'wss://integro-srj80gdl.livekit.cloud');
        setIsLoading(false);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to initialize voice session');
        setIsLoading(false);
      }
    }

    if (agentId) {
      initializeVoiceSession();
    } else {
      setError('Please load an agent first');
      setIsLoading(false);
    }
  }, [clientId, agentId, agentName, kbId]);

  if (isLoading) {
    return (
      <Box p="md" style={{ textAlign: 'center', background: 'var(--mantine-color-gray-0)', borderRadius: 8 }}>
        <Loader size="sm" />
        <Text size="sm" c="dimmed" mt="xs">Initializing voice session...</Text>
      </Box>
    );
  }

  if (error) {
    return (
      <Box p="md" style={{ textAlign: 'center', background: 'var(--mantine-color-gray-0)', borderRadius: 8 }}>
        <Text c="red" size="sm">{error}</Text>
        <Button size="xs" mt="xs" onClick={onClose}>Close Voice Mode</Button>
      </Box>
    );
  }

  return (
    <LiveKitRoom
      token={token}
      serverUrl={livekitUrl}
      connect={true}
      audio={true}
      video={false}
      onConnected={() => {
        // Connection established
      }}
      onError={(e) => {
        console.error('LiveKit error', e);
      }}
      onDisconnected={(reason) => {
        console.warn('LiveKit disconnected', reason);
        onClose?.();
      }}
    >
      <VoiceControls roomName={roomName} agentName={agentName} onEnd={onClose} onTranscript={onTranscript} />
      <RoomAudioRenderer />
    </LiveKitRoom>
  );
}

function VoiceControls({ roomName, agentName, onEnd, onTranscript }: { roomName: string; agentName?: string; onEnd?: () => void; onTranscript?: (evt: { speaker: 'user'|'assistant'; text: string }) => void }) {
  const { localParticipant } = useLocalParticipant();
  const connectionState = useConnectionState();
  const [isMuted, setIsMuted] = useState(false);
  const [micOpen, setMicOpen] = useState(false);
  const [agentConnected, setAgentConnected] = useState(false);
  const [agentSpeaking, setAgentSpeaking] = useState(false);
  const [lastUserText, setLastUserText] = useState('');
  const [lastAssistantText, setLastAssistantText] = useState('');

  // Use LiveKit's data channel hook to receive transcript data
  const { send, isSending } = useDataChannel('', (msg) => {
    try {
      const decoded = new TextDecoder().decode(msg.payload);
      
      let text: string | undefined;
      let type: string | undefined;
      let role: string | undefined;
      let speaker: string | undefined;
      
      try {
        const data = JSON.parse(decoded);
        if (data && typeof data === 'object') {
          type = typeof data.type === 'string' ? data.type : undefined;
          role = typeof data.role === 'string' ? data.role : undefined;
          speaker = typeof data.speaker === 'string' ? data.speaker : undefined;
          if (typeof data.text === 'string') text = data.text;
          else if (typeof data.transcript === 'string') text = data.transcript;
          else if (typeof data.message === 'string') text = data.message;
          else if (typeof data.content === 'string') text = data.content;
          else if (Array.isArray((data as any).segments)) {
            const segs = (data as any).segments.filter((s: any) => typeof s?.text === 'string').map((s: any) => s.text);
            if (segs.length) text = segs.join(' ');
          }
        }
      } catch {
        text = decoded;
      }
      
      if (!text) return;

      const isAssistant = role === 'assistant' || speaker === 'assistant' || type === 'assistant_transcript';
      
      // Handle agent connected event
      if (type === 'agent_connected') {
        setAgentConnected(true);
        return; // Don't process as transcript
      }
      
      if (isAssistant) {
        setLastAssistantText(text);
        setAgentSpeaking(true);
        setTimeout(() => setAgentSpeaking(false), 1500);
        // Mark agent as connected when we receive assistant data
        setAgentConnected(true);
      } else if (type === 'user_transcript' || role === 'user' || speaker === 'user') {
        setLastUserText(text);
      }
      
      onTranscript?.({ speaker: isAssistant ? 'assistant' : 'user', text });
    } catch (error) {
      console.error('Error processing data channel message:', error);
    }
  });

  // Monitor speaking state and participant changes
  useEffect(() => {
    if (!localParticipant) return;
    
    const room = (localParticipant as any).room;

    const handleMicState = () => {
      setIsMuted(!localParticipant.isMicrophoneEnabled);
      setMicOpen(localParticipant.isMicrophoneEnabled);
    };

    const recomputeAgentPresence = () => {
      if (!room) return setAgentConnected(false);
      // Check for remote participants OR if we've received agent data
      const hasRemoteParticipants = room.remoteParticipants.size > 0;
      const hasReceivedAgentData = Boolean(lastAssistantText) || agentSpeaking;
      setAgentConnected(hasRemoteParticipants || hasReceivedAgentData);
    };

    const handleActiveSpeakers = () => {
      if (!room) return;
      // agent speaking if any remote participant is in active speakers
      const speaking = room.activeSpeakers.some((p) => !p.isLocal);
      setAgentSpeaking(speaking);
    };


    // Track/mic state
    localParticipant.on(RoomEvent.LocalTrackPublished, handleMicState);
    localParticipant.on(RoomEvent.LocalTrackUnpublished, handleMicState);
    localParticipant.on(RoomEvent.TrackMuted, handleMicState);
    localParticipant.on(RoomEvent.TrackUnmuted, handleMicState);

    // Room-level events for presence and speakers
    room?.on(RoomEvent.ParticipantConnected, recomputeAgentPresence);
    room?.on(RoomEvent.ParticipantDisconnected, recomputeAgentPresence);
    room?.on(RoomEvent.ActiveSpeakersChanged, handleActiveSpeakers as any);

    // Initial state
    recomputeAgentPresence();
    handleMicState();
    
    // Fallback: mark agent as connected after a reasonable timeout
    const agentTimeout = setTimeout(() => {
      if (!agentConnected && isConnected) {
        setAgentConnected(true);
      }
    }, 5000); // 5 seconds

    return () => {
      clearTimeout(agentTimeout);
      localParticipant.off(RoomEvent.LocalTrackPublished, handleMicState);
      localParticipant.off(RoomEvent.LocalTrackUnpublished, handleMicState);
      localParticipant.off(RoomEvent.TrackMuted, handleMicState);
      localParticipant.off(RoomEvent.TrackUnmuted, handleMicState);
      room?.off(RoomEvent.ParticipantConnected, recomputeAgentPresence);
      room?.off(RoomEvent.ParticipantDisconnected, recomputeAgentPresence);
      room?.off(RoomEvent.ActiveSpeakersChanged, handleActiveSpeakers as any);
    };
  }, [localParticipant, onTranscript]);

  const toggleMicrophone = useCallback(async () => {
    if (!localParticipant) return;

    try {
      const newMuteState = !isMuted;
      await localParticipant.setMicrophoneEnabled(!newMuteState);
      setIsMuted(newMuteState);
    } catch (error) {
      console.error('Failed to toggle microphone:', error);
    }
  }, [localParticipant, isMuted]);

  const isConnected = connectionState === 'connected';

  return (
    <Box p="md" style={{ background: 'var(--mantine-color-gray-0)', borderRadius: 8 }}>
      <Stack gap="sm">
        <Group justify="space-between">
          <Group gap="xs">
            <Badge color={isConnected ? 'green' : 'yellow'} size="sm">
              {isConnected ? 'Connected' : 'Connecting...'}
            </Badge>
            <Badge color={agentConnected ? 'blue' : 'gray'} size="sm">
              {agentConnected ? 'Agent Connected' : 'Agent Pending'}
            </Badge>
            {micOpen && (
              <Badge color="indigo" size="sm" variant="dot">
                Mic On
              </Badge>
            )}
            {agentSpeaking && (
              <Badge color="cyan" size="sm" variant="dot">
                Agent Speaking
              </Badge>
            )}
          </Group>
          <Text size="sm" fw={500}>Voice Mode</Text>
        </Group>

        {agentName && (
          <Text size="sm" c="dimmed" ta="center">
            Speaking with {agentName}
          </Text>
        )}

        <Group justify="center" gap="md">
          <Button
            onClick={toggleMicrophone}
            color={!isMuted ? 'blue' : 'gray'}
            leftSection={!isMuted ? <IconMicrophone size={18} /> : <IconMicrophoneOff size={18} />}
            variant={!isMuted ? 'filled' : 'light'}
            disabled={!isConnected}
          >
            {!isMuted ? 'Mute' : 'Unmute'}
          </Button>

          <Button
            onClick={onEnd}
            color="red"
            variant="light"
            leftSection={<IconPhoneOff size={18} />}
          >
            End Voice
          </Button>
        </Group>

        <Stack gap={4}>
          {!agentConnected && isConnected && (
            <Text size="xs" c="dimmed" ta="center">
              Waiting for agent to join...
            </Text>
          )}
          {(lastUserText || lastAssistantText) && (
            <Box style={{ background: 'var(--mantine-color-gray-1)', borderRadius: 6, padding: 8 }}>
              {lastUserText && (
                <Text size="xs"><b>You:</b> {lastUserText}</Text>
              )}
              {lastAssistantText && (
                <Text size="xs"><b>Assistant:</b> {lastAssistantText}</Text>
              )}
            </Box>
          )}
        </Stack>
      </Stack>
    </Box>
  );
}