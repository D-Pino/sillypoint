type Robot = { id: string; name: string; company: string; urdf: string }
export default function RobotDetail({ robot }: { robot: Robot }) {
  return (
    <article>
      <h1>{robot.name}</h1>
      <p><strong>Company:</strong> {robot.company}</p>
      <p><strong>URDF:</strong></p>
      <pre>{robot.urdf}</pre>
      <p><a href="/robots/">Back to list</a></p>
    </article>
  )
}
