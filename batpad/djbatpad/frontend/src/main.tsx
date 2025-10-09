import ReactDOM from 'react-dom/client'
import { MantineProvider, createTheme } from '@mantine/core'
import '@mantine/core/styles.css'
import RobotsList from './components/robots/RobotList.tsx'
import RobotDetail from './components/robots/RobotDetail.tsx'
import Home from './components/home/Home.tsx'
import SimGen from './components/sim/SimGen.tsx'

const link = document.createElement('link')
link.href = 'https://fonts.googleapis.com/css2?family=EB+Garamond:wght@400;500;600;700&display=swap'
link.rel = 'stylesheet'
document.head.appendChild(link)

const theme = createTheme({
  primaryColor: 'blue',
  defaultRadius: 'md',
  fontFamily: 'EB Garamond, serif',
})

function mount<T>(id: string, render: (el: HTMLElement, props: T) => void) {
  const el = document.getElementById(id)
  if (!el) return
  const propsId = el.getAttribute('data-props-id')
  const props = propsId
    ? JSON.parse(document.getElementById(propsId)!.textContent || '{}')
    : {}
  render(el, props as T)
}

mount<{ robots: { id: string; name: string; company: string; urdf: string }[] }>(
  "robots-list",
  (el, props) => {
  ReactDOM.createRoot(el).render(
    <MantineProvider theme={theme}>
      <RobotsList robots={props.robots} />
    </MantineProvider>
  )
})

mount<{ robot: { id: string; name: string; company: string; urdf: string } }>(
  'robot-detail',
  (el, props) => {
    ReactDOM.createRoot(el).render(
      <MantineProvider theme={theme}>
        <RobotDetail robot={props.robot} />
      </MantineProvider>
    )
  }
)

mount<{}>('home-root', (el) => {
  ReactDOM.createRoot(el).render(
    <MantineProvider theme={theme}>
      <Home />
    </MantineProvider>
  )
})

mount<{}>('sim-root', (el) => {
  ReactDOM.createRoot(el).render(
    <MantineProvider theme={theme}>
      <SimGen />
    </MantineProvider>
  )
})
