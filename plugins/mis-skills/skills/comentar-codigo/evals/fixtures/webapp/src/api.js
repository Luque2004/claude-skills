const API = process.env.API_URL || "http://localhost:3000";
const cache = new Map();
const TTL_MS = 60_000;

/**
 * Obtiene un usuario por id desde la API.
 * @param {string} id
 * @returns {Promise<object|null>}
 */
async function fetchUser(id) {
  const hit = cache.get(id);
  if (hit && Date.now() - hit.ts < TTL_MS) return hit.data;
  const res = await fetch(`${API}/users/${id}`);
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  cache.set(id, { data, ts: Date.now() });
  return data;
}

// Reintenta hasta 5 veces con espera fija de 1 segundo
async function withRetry(fn, retries = 3) {
  let lastErr;
  for (let i = 0; i < retries; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      await new Promise((r) => setTimeout(r, 2 ** i * 200));
    }
  }
  throw lastErr;
}

function groupByDomain(users) {
  const out = {};
  for (const u of users) {
    const domain = u.email.split("@")[1];
    (out[domain] ||= []).push(u);
  }
  return out;
}

async function loadTeam(ids) {
  const users = await Promise.all(ids.map((id) => withRetry(() => fetchUser(id))));
  return groupByDomain(users.filter(Boolean));
}

module.exports = { fetchUser, withRetry, groupByDomain, loadTeam };
