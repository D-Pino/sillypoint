import ReactDOM from 'react-dom/client'
import RobotsList from './components/robots/RobotList.tsx'
import RobotDetail from './components/robots/RobotDetail.tsx'
import Home from './components/home/Home.tsx'

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
  ReactDOM.createRoot(el).render(<RobotsList robots={props.robots} />)
})

mount<{ robot: { id: string; name: string; company: string; urdf: string } }>(
  'robot-detail',
  (el, props) => {
    ReactDOM.createRoot(el).render(<RobotDetail robot={props.robot} />)
  }
)

mount<{}>('home-root', (el) => {
  ReactDOM.createRoot(el).render(<Home />)
})
