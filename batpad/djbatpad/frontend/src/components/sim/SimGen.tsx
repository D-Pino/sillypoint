import { useEffect, useRef, useState } from 'react'
import { Container, Stack, Title, Text, TextInput, Button } from '@mantine/core'

export default function SimGen() {
  const [prompt, setPrompt] = useState('a simple box on a plane')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [status, setStatus] = useState<'idle' | 'generating' | 'streaming' | 'error'>('idle')
  const imgRef = useRef<HTMLImageElement | null>(null)
  const wsRef = useRef<WebSocket | null>(null)
  const lastUrlRef = useRef<string | null>(null)

  useEffect(() => {
    return () => {
      if (wsRef.current) wsRef.current.close()
      if (lastUrlRef.current) URL.revokeObjectURL(lastUrlRef.current)
    }
  }, [])

  async function handleGenerate(e: React.FormEvent) {
    e.preventDefault()
    setStatus('generating')
    setSessionId(null)
    try {
      const r = await fetch('http://localhost:8010/api/generate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
      })
      if (!r.ok) throw new Error(await r.text())
      const data = await r.json()
      const sid = data.session_id as string
      setSessionId(sid)

      if (wsRef.current) wsRef.current.close()
      const ws = new WebSocket(`ws://localhost:8010/ws/video?session_id=${encodeURIComponent(sid)}`)
      ws.binaryType = 'arraybuffer'
      ws.onopen = () => setStatus('streaming')
      ws.onmessage = (ev: MessageEvent<ArrayBuffer>) => {
        const blob = new Blob([ev.data], { type: 'image/jpeg' })
        if (lastUrlRef.current) URL.revokeObjectURL(lastUrlRef.current)
        const url = URL.createObjectURL(blob)
        lastUrlRef.current = url
        if (imgRef.current) imgRef.current.src = url
      }
      ws.onerror = () => setStatus('error')
      ws.onclose = () => setStatus('idle')
      wsRef.current = ws
    } catch (err) {
      console.error(err)
      setStatus('error')
    }
  }

  return (
    <Container size="md" py={40}>
      <Stack gap="md">
        <Title order={1}>MuJoCo Scene Generator</Title>
        <Text c="dimmed">Describe a scene, stream the result.</Text>
        <form onSubmit={handleGenerate}>
          <Stack gap="md" mt="xs">
            <TextInput
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              placeholder="Describe the MuJoCo scene"
              size="md"
            />
            <Button
              type="submit"
              variant="outline"
              disabled={status === 'generating'}
            >
              {status === 'generating' ? 'Generating…' : 'Generate & Stream'}
            </Button>
          </Stack>
        </form>
        <img ref={imgRef} alt="stream" style={{ maxWidth: '100%', borderRadius: 8 }} />
        <Text size="sm" c="dimmed">
          Status: {status} {sessionId ? `(session ${sessionId.slice(0, 8)}…)` : ''}
        </Text>
      </Stack>
    </Container>
  )
}



