// All calls are relative. nginx (Docker) or the Ingress (Kubernetes) routes
// /api to the backend, so no hostname is ever baked into the bundle.
const BASE = "/api";

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = `${res.status} ${res.statusText}`;
    try {
      const body = await res.json();
      if (body.detail) detail = typeof body.detail === "string" ? body.detail : detail;
    } catch {
      // Error body was not JSON; the status line is enough.
    }
    throw new Error(detail);
  }
  return res.status === 204 ? null : res.json();
}

export const listIssues = (params = {}) => {
  const q = new URLSearchParams(
    Object.entries(params).filter(([, v]) => v !== "" && v != null)
  ).toString();
  return request(`/issues${q ? `?${q}` : ""}`);
};

export const getIssue = (id) => request(`/issues/${id}`);
export const createIssue = (data) =>
  request("/issues", { method: "POST", body: JSON.stringify(data) });
export const updateIssue = (id, data) =>
  request(`/issues/${id}`, { method: "PUT", body: JSON.stringify(data) });
export const deleteIssue = (id) => request(`/issues/${id}`, { method: "DELETE" });
export const addNote = (id, data) =>
  request(`/issues/${id}/updates`, { method: "POST", body: JSON.stringify(data) });
export const getStats = () => request("/stats");
