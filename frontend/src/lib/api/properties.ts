import { apiFetch } from './client'
import type { Property, PropertyListParams, PropertyListResponse } from './types'

export function listProperties(params: PropertyListParams = {}) {
  const query = new URLSearchParams()
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== '') query.set(key, String(value))
  }
  const suffix = query.size > 0 ? `?${query.toString()}` : ''
  return apiFetch<PropertyListResponse>(`/api/v1/properties${suffix}`)
}

export function getProperty(id: number) {
  return apiFetch<Property>(`/api/v1/properties/${id}`)
}
