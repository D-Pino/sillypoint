type Robot = { id: string; name: string; company: string; urdf: string }
export default function RobotsList({ robots }: { robots: Robot[] }) {
  return (
    <div>
      <h1>Robots</h1>
      {robots.length === 0 ? (
        <p>No robots found. Add some robots to see them here!</p>
      ) : (
        <ul>
          {robots.map(r => (
            <li key={r.id}>
              <a href={`/robots/${r.id}/`}>{r.name}</a> - {r.company}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
