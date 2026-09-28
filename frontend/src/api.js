const BASE = '/api/auth'

/** Error carrying the backend's {"errors": {...}} envelope. */
export class ApiError extends Error {
  constructor(status, errors) {
    super('Request failed')
    this.status = status
    this.errors = errors ?? {}
  }

  /** Messages for one field, as a flat array. */
  for(field) {
    const value = this.errors[field]
    if (!value) return []
    return Array.isArray(value) ? value : [String(value)]
  }

  /** Messages that do not belong to a specific form field. */
  get general() {
    return [...this.for('detail'), ...this.for('non_field_errors')]
  }
}

function readCookie(name) {
  const match = document.cookie.match(new RegExp(`(^|;\\s*)${name}=([^;]*)`))
  return match ? decodeURIComponent(match[2]) : null
}

/** Ask the backend to set a csrftoken cookie if we do not have one yet. */
export async function ensureCsrfToken() {
  if (!readCookie('csrftoken')) {
    await fetch(`${BASE}/csrf/`, { credentials: 'same-origin' })
  }
  return readCookie('csrftoken')
}

async function request(path, { method = 'GET', body } = {}) {
  const headers = {}
  if (body !== undefined) headers['Content-Type'] = 'application/json'

  // Django requires the token on every unsafe method.
  if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
    const token = await ensureCsrfToken()
    if (token) headers['X-CSRFToken'] = token
  }

  const response = await fetch(`${BASE}${path}`, {
    method,
    headers,
    credentials: 'same-origin',
    body: body === undefined ? undefined : JSON.stringify(body),
  })

  if (response.status === 204) return null

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, data?.errors ?? { detail: ['Something went wrong.'] })
  }
  return data
}

export const getCurrentUser = () => request('/me/')
export const register = (payload) => request('/register/', { method: 'POST', body: payload })
export const login = (credentials) => request('/login/', { method: 'POST', body: credentials })
export const logout = () => request('/logout/', { method: 'POST' })
export const updateProfile = (changes) => request('/me/', { method: 'PATCH', body: changes })
