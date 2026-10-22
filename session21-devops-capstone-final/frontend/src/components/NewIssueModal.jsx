import { useState } from "react";

const BLANK = {
  title: "", description: "", building: "", room: "",
  category: "other", priority: "medium", reported_by: "",
};

export default function NewIssueModal({ onClose, onSubmit }) {
  const [form, setForm] = useState(BLANK);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const set = (key) => (e) => setForm({ ...form, [key]: e.target.value });

  const submit = async (e) => {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const payload = { ...form };
      // The backend defaults this; sending "" would fail validation.
      if (!payload.reported_by.trim()) delete payload.reported_by;
      await onSubmit(payload);
    } catch (err) {
      setError(err.message);
      // Only clear busy on failure - on success the modal unmounts.
      setBusy(false);
    }
  };

  return (
    <div className="backdrop" onClick={onClose}>
      {/* Stop clicks inside the dialog from reaching the backdrop handler */}
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Report an issue</h2>

        {error && <div className="banner error">{error}</div>}

        <form onSubmit={submit}>
          <label>
            Title
            <input required minLength={3} value={form.title} onChange={set("title")}
              placeholder="Projector not switching on" />
          </label>

          <div className="row">
            <label>
              Building
              <input required value={form.building} onChange={set("building")}
                placeholder="Science Block" />
            </label>
            <label>
              Room
              <input value={form.room} onChange={set("room")} placeholder="S-204" />
            </label>
          </div>

          <div className="row">
            <label>
              Category
              <select value={form.category} onChange={set("category")}>
                {["electrical", "plumbing", "network", "furniture", "other"].map((c) => (
                  <option key={c} value={c}>{c}</option>
                ))}
              </select>
            </label>
            <label>
              Priority
              <select value={form.priority} onChange={set("priority")}>
                {["low", "medium", "high", "urgent"].map((p) => (
                  <option key={p} value={p}>{p}</option>
                ))}
              </select>
            </label>
          </div>

          <label>
            Your name
            <input value={form.reported_by} onChange={set("reported_by")}
              placeholder="Optional" />
          </label>

          <label>
            Description
            <textarea rows={3} value={form.description} onChange={set("description")}
              placeholder="What is wrong?" />
          </label>

          <div className="modal-actions">
            <button type="button" className="btn" onClick={onClose}>Cancel</button>
            <button className="btn primary" disabled={busy}>
              {busy ? "Submitting…" : "Submit"}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
