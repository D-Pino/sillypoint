import { useEffect, useRef, useState } from 'react'

export default function MujocoGen() {
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
    <div style={{ display: 'grid', gap: 12 }}>
      <h1 style={{ margin: 0 }}>MuJoCo Scene Generator</h1>
      <p style={{ margin: 0, opacity: 0.85 }}>Describe a scene, stream the result.</p>
      <form onSubmit={handleGenerate} style={{ display: 'grid', gap: 12, marginTop: 8 }}>
        <input
          value={prompt}
          onChange={(e) => setPrompt(e.target.value)}
          placeholder="Describe the MuJoCo scene"
          style={{
            padding: '10px 12px',
            borderRadius: 8,
            border: '1px solid rgba(148, 163, 184, 0.35)',
            background: 'rgba(2,6,23,0.6)',
            color: '#e5e7eb',
          }}
        />
        <button type="submit" style={{
          padding: '10px 16px', borderRadius: 10, fontWeight: 600,
          background: 'linear-gradient(135deg, #2563eb, #22c55e)', color: '#0b1020',
          border: '1px solid rgba(148, 163, 184, 0.25)'
        }} disabled={status === 'generating'}>
          {status === 'generating' ? 'Generating…' : 'Generate & Stream'}
        </button>
      </form>
      <div style={{ marginTop: 8 }}>
        <img ref={imgRef} alt="stream" style={{ maxWidth: '100%', background: '#000', borderRadius: 8 }} />
      </div>
      <p style={{ marginTop: 4, opacity: 0.8, fontSize: 13 }}>
        Status: {status} {sessionId ? `(session ${sessionId.slice(0, 8)}…)` : ''}
      </p>
    </div>
  )
}


