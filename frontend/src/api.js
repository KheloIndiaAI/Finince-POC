// Thin fetch wrapper for the backend's comparison endpoints.
// Default is same-origin (/api/...): in production nginx proxies it to the
// backend, and in dev the vite proxy does. Set VITE_API_BASE_URL only to point
// the app at a backend on a different host.
const BASE_URL = import.meta.env.VITE_API_BASE_URL || "";

async function request(path, options = {}) {
  const response = await fetch(`${BASE_URL}${path}`, options);
  if (!response.ok) {
    const body = await response.text();
    throw new Error(`${response.status}: ${body}`);
  }
  if (response.status === 204) return null; // e.g. DELETE, no body
  return response.json();
}

export function createComparison(sanctionFile, expenditureFile) {
  const form = new FormData();
  form.append("sanction_file", sanctionFile);
  form.append("expenditure_file", expenditureFile);
  return request("/api/comparisons", { method: "POST", body: form });
}

export function getComparison(id) {
  return request(`/api/comparisons/${id}`);
}

export function confirmComparison(id, body) {
  return request(`/api/comparisons/${id}/confirm`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

export function regenerateSummary(id) {
  return request(`/api/comparisons/${id}/summary/regenerate`, { method: "POST" });
}

export function listSummaries(id) {
  return request(`/api/comparisons/${id}/summaries`);
}

export function listComparisons({ q = "", dateFrom = "", dateTo = "" } = {}) {
  const params = new URLSearchParams();
  if (q) params.set("q", q);
  if (dateFrom) params.set("date_from", dateFrom);
  if (dateTo) params.set("date_to", dateTo);
  const query = params.toString();
  return request(`/api/comparisons${query ? `?${query}` : ""}`);
}

export function deleteComparison(id) {
  return request(`/api/comparisons/${id}`, { method: "DELETE" });
}
