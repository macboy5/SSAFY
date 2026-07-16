const BASE_URL = '/api'
const TOKEN_KEY = 'seoulmates.auth-token'
const responseCache = new Map()
const pendingGets = new Map()

export function getAuthToken() {
  return typeof window === 'undefined' ? null : localStorage.getItem(TOKEN_KEY)
}

export function setAuthToken(token) {
  if (typeof window === 'undefined') return
  if (token) localStorage.setItem(TOKEN_KEY, token)
  else localStorage.removeItem(TOKEN_KEY)
}

function errorMessage(detail, fallback) {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) return detail.map((item) => item.msg || String(item)).join('\n')
  return fallback
}

async function request(path, options = {}) {
  const token = getAuthToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }
  const res = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (!res.ok) {
    let detail = `요청에 실패했습니다. (${res.status})`
    try {
      const body = await res.json()
      detail = errorMessage(body.detail, detail)
    } catch {
      // The status code still gives the caller a useful fallback message.
    }

    if (res.status === 401 && token && !path.startsWith('/auth/login')) {
      setAuthToken(null)
      window.dispatchEvent(new CustomEvent('seoulmates:auth-expired'))
    }
    const error = new Error(detail)
    error.status = res.status
    throw error
  }

  if (res.status === 204) return null
  return res.json()
}

async function cachedGet(path, options = {}) {
  const {
    ttl = 5 * 60 * 1000,
    staleTtl = 24 * 60 * 60 * 1000,
    force = false,
  } = options
  const now = Date.now()
  const cached = responseCache.get(path)

  if (!force && cached && now < cached.expiresAt) return cached.data
  if (!force && pendingGets.has(path)) return pendingGets.get(path)

  const pending = request(path, { cache: force ? 'reload' : 'default' })
    .then((data) => {
      const storedAt = Date.now()
      responseCache.set(path, {
        data,
        expiresAt: storedAt + ttl,
        staleUntil: storedAt + Math.max(ttl, staleTtl),
      })
      return data
    })
    .catch((error) => {
      if (cached && now < cached.staleUntil) return cached.data
      throw error
    })
    .finally(() => pendingGets.delete(path))

  pendingGets.set(path, pending)
  return pending
}

function clearGetCache(pathPrefix = '') {
  for (const path of responseCache.keys()) {
    if (!pathPrefix || path.startsWith(pathPrefix)) responseCache.delete(path)
  }
}

export const api = {
  get: (path) => request(path),
  getCached: cachedGet,
  clearGetCache,
  post: (path, data) =>
    request(path, { method: 'POST', body: data === undefined ? undefined : JSON.stringify(data) }),
  put: (path, data) =>
    request(path, { method: 'PUT', body: data === undefined ? undefined : JSON.stringify(data) }),
  delete: (path, data) =>
    request(path, { method: 'DELETE', body: data === undefined ? undefined : JSON.stringify(data) }),
  patch: (path, data) => request(path, { method: 'PATCH', body: JSON.stringify(data) }),
}

export function plannerApi() {
  let id = localStorage.getItem('seoulmates.planner-id')
  if (!id) {
    id = crypto.randomUUID()
    localStorage.setItem('seoulmates.planner-id', id)
  }
  const headers = { 'X-Planner-Id': id }
  return {
    get: () => request('/planner', { headers }),
    add: (data) => request('/planner', { method: 'POST', headers, body: JSON.stringify(data) }),
    update: (itemId, data) =>
      request(`/planner/${itemId}`, { method: 'PATCH', headers, body: JSON.stringify(data) }),
    remove: (itemId) => request(`/planner/${itemId}`, { method: 'DELETE', headers }),
  }
}
