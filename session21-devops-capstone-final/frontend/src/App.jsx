import { useCallback, useEffect, useState } from "react";
import * as api from "./api.js";
import Sidebar from "./components/Sidebar.jsx";
import StatCards from "./components/StatCards.jsx";
import Filters from "./components/Filters.jsx";
import IssueTable from "./components/IssueTable.jsx";
import IssueDetail from "./components/IssueDetail.jsx";
import NewIssueModal from "./components/NewIssueModal.jsx";

export default function App() {
  const [issues, setIssues] = useState([]);
  const [stats, setStats] = useState(null);
  const [filters, setFilters] = useState({ status: "", priority: "", category: "", building: "" });
  const [selected, setSelected] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    try {
      setError(null);
      const [list, s] = await Promise.all([api.listIssues(filters), api.getStats()]);
      setIssues(list);
      setStats(s);
    } catch (e) {
      setError(e.message);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    load();
  }, [load]);

  const openDetail = async (id) => {
    try {
      setSelected(await api.getIssue(id));
    } catch (e) {
      setError(e.message);
    }
  };

  const handleCreate = async (data) => {
    await api.createIssue(data);
    setShowModal(false);
    await load();
  };

  const handleStatus = async (id, status) => {
    await api.updateIssue(id, { status });
    await load();
    // Keep the detail panel in sync if it is showing the issue just changed.
    if (selected?.id === id) await openDetail(id);
  };

  const handleDelete = async (id) => {
    await api.deleteIssue(id);
    if (selected?.id === id) setSelected(null);
    await load();
  };

  const handleNote = async (id, note) => {
    await api.addNote(id, { note, author: "staff" });
    await openDetail(id);
  };

  return (
    <div className="layout">
      <Sidebar stats={stats} />

      <main className="main">
        <header className="header">
          <div>
            <h1>Facility Issues</h1>
            <p className="subtitle">Report and track campus maintenance</p>
          </div>
          <button className="btn primary" onClick={() => setShowModal(true)}>
            + Report an issue
          </button>
        </header>

        {error && (
          <div className="banner error">
            Could not reach the backend: {error}
            <button className="btn small" onClick={load}>Retry</button>
          </div>
        )}

        <StatCards stats={stats} />
        <Filters filters={filters} onChange={setFilters} />

        {loading ? (
          <div className="banner">Loading issues…</div>
        ) : (
          <IssueTable
            issues={issues}
            onSelect={openDetail}
            onStatus={handleStatus}
            onDelete={handleDelete}
          />
        )}
      </main>

      {selected && (
        <IssueDetail
          issue={selected}
          onClose={() => setSelected(null)}
          onNote={handleNote}
          onStatus={handleStatus}
        />
      )}

      {showModal && (
        <NewIssueModal onClose={() => setShowModal(false)} onSubmit={handleCreate} />
      )}
    </div>
  );
}
