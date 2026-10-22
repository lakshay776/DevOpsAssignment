const NEXT = { open: "in_progress", in_progress: "resolved", resolved: "open" };
const NEXT_LABEL = { open: "Start", in_progress: "Resolve", resolved: "Reopen" };

const when = (iso) =>
  new Date(iso).toLocaleString(undefined, {
    day: "numeric", month: "short", hour: "2-digit", minute: "2-digit",
  });

export default function IssueTable({ issues, admin, onSelect, onStatus, onDelete }) {
  if (issues.length === 0) {
    return <div className="banner">No issues match these filters.</div>;
  }

  return (
    <div className="table-wrap">
      <table className="table">
        <thead>
          <tr>
            <th>#</th><th>Title</th><th>Location</th><th>Category</th>
            <th>Priority</th><th>Status</th><th>Reported</th>{admin && <th></th>}
          </tr>
        </thead>
        <tbody>
          {issues.map((i) => (
            <tr key={i.id}>
              <td className="muted">{i.id}</td>
              <td>
                <button className="link" onClick={() => onSelect(i.id)}>{i.title}</button>
              </td>
              <td className="muted">{i.building}{i.room ? ` · ${i.room}` : ""}</td>
              <td className="muted">{i.category}</td>
              <td><span className={`badge p-${i.priority}`}>{i.priority}</span></td>
              <td><span className={`pill s-${i.status}`}>{i.status.replace("_", " ")}</span></td>
              <td className="muted">{when(i.created_at)}</td>
              {admin && (
                <td className="row-actions">
                  <button className="btn small" onClick={() => onStatus(i.id, NEXT[i.status])}>
                    {NEXT_LABEL[i.status]}
                  </button>
                  <button className="btn small danger" onClick={() => onDelete(i.id)}>
                    Delete
                  </button>
                </td>
              )}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
