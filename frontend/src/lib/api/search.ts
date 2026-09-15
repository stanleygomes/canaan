import { apiFetch } from './client'
import type { SearchFilters, ScrapeRun } from './types'

export function getSearchFilters(name = 'default') {
  return apiFetch<SearchFilters>(`/api/v1/search-filters/${name}`)
}

export function updateSearchFilters(name: string, filters: SearchFilters) {
  const { name: _name, active: _active, updated_at: _updatedAt, ...payload } = filters
  return apiFetch<SearchFilters>(`/api/v1/search-filters/${name}`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export function startScrape(source = 'all') {
  return apiFetch<ScrapeRun>('/api/v1/scrape-runs', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source }),
  })
}

export function getScrapeRun(runId: string) {
  return apiFetch<ScrapeRun>(`/api/v1/scrape-runs/${runId}`)
}
