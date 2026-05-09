import axios from 'axios'
import { useAppStore } from '@shared/stores/appStore'

export function apiAuthHeaders(extra?: HeadersInit): Headers {
  const headers = new Headers(extra)
  const token = useAppStore.getState().apiToken
  if (token) headers.set('Authorization', `Bearer ${token}`)
  return headers
}

export function createApiClient(baseURL: string) {
  const token = useAppStore.getState().apiToken
  return axios.create({
    baseURL,
    headers: token ? { Authorization: `Bearer ${token}` } : undefined,
  })
}

export function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  return fetch(input, {
    ...init,
    headers: apiAuthHeaders(init.headers),
  })
}
