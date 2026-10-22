import { useState } from "react";

export default function IssueDetail({ issue, onClose, onNote, onStatus }) {
  const [note, setNote] = useState("");
  const [busy, setBusy] = useState(false);

  const submit = async (e) => {
    e.preventDefault();
    if (!note.trim()) return;
    setBusy(true);
    try {
      await onNote(issue.id, note.trim());
      setNote("");
    } finally {
      setBusy(false);
    }
  };

  return (
    <aside className="detail">
      <header className="detail-head">
        <div>
          <small className="muted">Issue #{issue.id}</small>
          <h2>{issue.title}</h2>
        </div>
        <button className="btn small" onClick={onClose}>Close</button>
      </header>

      <dl className="meta">
        <div><dt>Location</dt><dd>{issue.building}{issue.room ? ` · ${issue.room}` : ""}</dd></div>
        <div><dt>Category</dt><dd>{issue.category}</dd></div>
        <div><dt>Priority</dt><dd><span className={`badge p-${issue.priority}`}>{issue.priority}</span></dd></div>
        <div><dt>Status</dt><dd><span className={`pill s-${issue.status}`}>{issue.status.replace("_", " ")}</span></dd></div>
        <div><dt>Reported by</dt><dd>{issue.reported_by}</dd></div>
        {issue.assigned_to && <div><dt>Assigned</dt><dd>{issue.assigned_to}</dd></div>}
      </dl>

      {issue.description && <p className="description">{issue.description}</p>}

      <div className="status-actions">
        {["open", "in_progress", "resolved"].map((s) => (
          <button
            key={s}
            className={`btn small ${issue.status === s ? "primary" : ""}`}
            onClick={() => onStatus(issue.id, s)}
            disabled={issue.status === s}
          >
            {s.replace("_", " ")}
          </button>
        ))}
      </div>

      <h4>Worklog</h4>
      {issue.updates?.length ? (
        <ul className="worklog">
          {issue.updates.map((u) => (
            <li key={u.id}>
              <p>{u.note}</p>
              <small className="muted">
                {u.author} · {new Date(u.created_at).toLocaleString()}
              </small>
            </li>
          ))}
        </ul>
      ) : (
        <p className="muted">Nothing logged yet.</p>
      )}

      <form className="note-form" onSubmit={submit}>
        <input
          value={note}
          onChange={(e) => setNote(e.target.value)}
          placeholder="Add a note…"
        />
        <button className="btn primary" disabled={busy || !note.trim()}>
          {busy ? "Saving…" : "Add"}
        </button>
      </form>
    </aside>
  );
}
