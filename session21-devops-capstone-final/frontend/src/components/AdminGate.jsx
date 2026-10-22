import { useState } from "react";

// Demo gate only. The password is compared in the browser, so anyone can
// bypass it with devtools - it hides the staff controls, it does not protect
// them. The API accepts the same requests either way. Real protection would
// mean accounts, a session or token, and role checks on every endpoint.
const DEMO_PASSWORD = "1234";

export default function AdminGate({ admin, onChange }) {
  const [asking, setAsking] = useState(false);
  const [value, setValue] = useState("");
  const [error, setError] = useState(false);

  if (admin) {
    return (
      <button className="btn small" onClick={() => onChange(false)}>
        Exit admin
      </button>
    );
  }

  if (!asking) {
    return (
      <button className="btn small" onClick={() => setAsking(true)}>
        Admin mode
      </button>
    );
  }

  const submit = (e) => {
    e.preventDefault();
    if (value === DEMO_PASSWORD) {
      onChange(true);
      setAsking(false);
      setValue("");
      setError(false);
    } else {
      setError(true);
    }
  };

  return (
    <form className="admin-gate" onSubmit={submit}>
      <input
        type="password"
        autoFocus
        value={value}
        onChange={(e) => { setValue(e.target.value); setError(false); }}
        placeholder="Admin password"
        className={error ? "bad" : ""}
      />
      <button className="btn small primary">Unlock</button>
      <button type="button" className="btn small" onClick={() => { setAsking(false); setError(false); setValue(""); }}>
        Cancel
      </button>
      {error && <span className="gate-error">Wrong password</span>}
    </form>
  );
}
