const STATUS = ["", "open", "in_progress", "resolved"];
const PRIORITY = ["", "low", "medium", "high", "urgent"];
const CATEGORY = ["", "electrical", "plumbing", "network", "furniture", "other"];

const label = (v) => (v === "" ? "All" : v.replace("_", " "));

export default function Filters({ filters, onChange }) {
  const set = (key) => (e) => onChange({ ...filters, [key]: e.target.value });

  return (
    <section className="filters">
      <label>
        Status
        <select value={filters.status} onChange={set("status")}>
          {STATUS.map((v) => <option key={v} value={v}>{label(v)}</option>)}
        </select>
      </label>
      <label>
        Priority
        <select value={filters.priority} onChange={set("priority")}>
          {PRIORITY.map((v) => <option key={v} value={v}>{label(v)}</option>)}
        </select>
      </label>
      <label>
        Category
        <select value={filters.category} onChange={set("category")}>
          {CATEGORY.map((v) => <option key={v} value={v}>{label(v)}</option>)}
        </select>
      </label>
      <label>
        Building
        <input
          type="text"
          placeholder="Any building"
          value={filters.building}
          onChange={set("building")}
        />
      </label>
    </section>
  );
}
