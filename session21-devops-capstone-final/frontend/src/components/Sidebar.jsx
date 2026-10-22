export default function Sidebar({ stats }) {
  return (
    <aside className="sidebar">
      <div className="brand">
        <span className="logo">CD</span>
        <div>
          <strong>CampusDesk</strong>
          <small>Facilities</small>
        </div>
      </div>

      <nav className="nav">
        <a className="nav-item active" href="#issues">Issues</a>
        <a className="nav-item" href="#issues">Buildings</a>
        <a className="nav-item" href="#issues">Reports</a>
      </nav>

      {stats && Object.keys(stats.by_building).length > 0 && (
        <div className="side-block">
          <h4>By building</h4>
          <ul className="side-list">
            {Object.entries(stats.by_building)
              .sort((a, b) => b[1] - a[1])
              .slice(0, 6)
              .map(([name, count]) => (
                <li key={name}>
                  <span>{name}</span>
                  <b>{count}</b>
                </li>
              ))}
          </ul>
        </div>
      )}

      {stats?.avg_resolution_hours != null && (
        <div className="side-block">
          <h4>Avg resolution</h4>
          <p className="big">{stats.avg_resolution_hours}h</p>
        </div>
      )}
    </aside>
  );
}
