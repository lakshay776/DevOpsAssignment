const CARDS = [
  { key: "open", label: "Open", tone: "open" },
  { key: "in_progress", label: "In progress", tone: "progress" },
  { key: "resolved", label: "Resolved", tone: "resolved" },
  { key: "urgent_open", label: "Urgent open", tone: "urgent" },
];

export default function StatCards({ stats }) {
  return (
    <section className="cards">
      {CARDS.map(({ key, label, tone }) => (
        <div className={`card ${tone}`} key={key}>
          <span className="card-label">{label}</span>
          {/* em dash until the first load lands, so the layout does not jump */}
          <span className="card-value">{stats ? stats[key] : "—"}</span>
        </div>
      ))}
    </section>
  );
}
