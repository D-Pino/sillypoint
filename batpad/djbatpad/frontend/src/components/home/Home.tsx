import { Container, Stack, Title, Text, Button, Group, Paper } from '@mantine/core'

export default function Home() {
  return (
    <Container size="md" py={60}>
      <Stack gap="xl" align="center">
        <Paper shadow="sm" p="xl" radius="md" withBorder>
          <Stack gap="lg" align="center">
            <RobotIcon />
            <Title order={1}>SillyPoint Robotics</Title>
            <Text size="lg" c="dimmed">
              Build, catalog, and explore your robot fleet.
            </Text>
            <Group justify="center" mt="md">
              <Button component="a" href="/sim/" variant="outline">
                MuJoCo Generator
              </Button>
              <Button component="a" href="/robots/" variant="light">
                View Robots
              </Button>
              <Button component="a" href="/admin/" variant="light">
                Admin
              </Button>
            </Group>
          </Stack>
        </Paper>
        <Text size="sm" c="dimmed">
          Powered by Django + React
        </Text>
      </Stack>
    </Container>
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


