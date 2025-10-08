import React from 'react'

export default function Home() {
  return (
    <div style={styles.page}>
      <div style={styles.glow} />
      <section style={styles.card}>
        <RobotIcon />
        <h1 style={styles.title}>SillyPoint Robotics</h1>
        <p style={styles.subtitle}>Build, catalog, and explore your robot fleet.</p>
        <div style={styles.actions}>
          <a style={{ ...styles.button, ...styles.primary }} href="/sim/">MuJoCo Generator</a>
          <a style={{ ...styles.button, ...styles.ghost }} href="/robots/">View Robots</a>
          <a style={{ ...styles.button, ...styles.ghost }} href="/admin/">Admin</a>
        </div>
      </section>
      <footer style={styles.footer}>
        <span>Powered by Django + React</span>
      </footer>
    </div>
  )
}

function RobotIcon() {
  return (
    <svg width="96" height="96" viewBox="0 0 96 96" fill="none" aria-hidden>
      <rect x="12" y="26" width="72" height="48" rx="10" fill="#1f2937" stroke="#374151" />
      <circle cx="36" cy="46" r="8" fill="#60a5fa" />
      <circle cx="60" cy="46" r="8" fill="#60a5fa" />
      <rect x="32" y="62" width="32" height="6" rx="3" fill="#10b981" />
      <rect x="44" y="12" width="8" height="10" rx="2" fill="#6b7280" />
      <rect x="28" y="16" width="40" height="10" rx="5" fill="#9ca3af" />
      <circle cx="8" cy="40" r="4" fill="#ef4444" />
      <circle cx="88" cy="40" r="4" fill="#22c55e" />
    </svg>
  )
}

const styles: { [k: string]: React.CSSProperties } = {
  page: {
    position: 'relative',
    minHeight: 'calc(100dvh - 0px)',
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 24,
    padding: '48px 16px',
    background: 'linear-gradient(135deg, #0b1020 0%, #0a0f1a 60%, #0e1426 100%)',
    color: '#e5e7eb',
  },
  glow: {
    position: 'absolute',
    inset: -200,
    background: 'radial-gradient(600px 300px at 50% 10%, rgba(59,130,246,0.20), transparent 60%), radial-gradient(500px 250px at 20% 80%, rgba(16,185,129,0.18), transparent 60%), radial-gradient(500px 250px at 80% 80%, rgba(236,72,153,0.14), transparent 60%)',
    filter: 'blur(10px)',
    pointerEvents: 'none',
  },
  card: {
    position: 'relative',
    width: 'min(840px, 96%)',
    padding: '36px 28px',
    borderRadius: 16,
    background: 'rgba(17, 24, 39, 0.7)',
    border: '1px solid rgba(148, 163, 184, 0.2)',
    boxShadow: '0 10px 30px rgba(0,0,0,0.35)',
    textAlign: 'center',
    backdropFilter: 'blur(6px)',
  },
  title: {
    margin: '18px 0 8px',
    fontSize: 40,
    lineHeight: 1.1,
    letterSpacing: 0.3,
  },
  subtitle: {
    margin: 0,
    color: '#cbd5e1',
    fontSize: 18,
  },
  actions: {
    display: 'flex',
    gap: 12,
    justifyContent: 'center',
    marginTop: 24,
    flexWrap: 'wrap',
  },
  button: {
    padding: '10px 16px',
    borderRadius: 10,
    border: '1px solid rgba(148, 163, 184, 0.25)',
    textDecoration: 'none',
    fontWeight: 600,
    letterSpacing: 0.2,
    transition: 'all .2s ease',
  },
  primary: {
    background: 'linear-gradient(135deg, #2563eb, #22c55e)',
    color: '#0b1020',
  },
  ghost: {
    background: 'rgba(2,6,23,0.6)',
    color: '#e5e7eb',
  },
  footer: {
    marginTop: 20,
    opacity: 0.7,
    fontSize: 13,
  },
}


