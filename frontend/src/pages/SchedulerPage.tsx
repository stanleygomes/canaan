import { useEffect, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getSearchFilters, updateSearchFilters } from '../lib/api/search'
import type { SearchFilters } from '../lib/api/types'

function splitList(value: string) {
  return value.split(',').map((item) => item.trim()).filter(Boolean)
}

export function SchedulerPage() {
  const queryClient = useQueryClient()
  const filtersQuery = useQuery({ queryKey: ['search-filters', 'default'], queryFn: () => getSearchFilters() })
  const [form, setForm] = useState<SearchFilters | null>(null)
  const filters = form ?? filtersQuery.data
  const saveMutation = useMutation({
    mutationFn: (payload: SearchFilters) => updateSearchFilters('default', payload),
    onSuccess: (data) => { setForm(data); queryClient.invalidateQueries({ queryKey: ['search-filters', 'default'] }) },
  })

  useEffect(() => {
    if (filtersQuery.data && !form) setForm(filtersQuery.data)
  }, [filtersQuery.data, form])

  function setField<K extends keyof SearchFilters>(key: K, value: SearchFilters[K]) {
    setForm((current) => current ? { ...current, [key]: value } : current)
  }

  if (filtersQuery.isLoading || !filters) return <div className="mx-auto max-w-3xl px-6 py-16 text-slate-500">Carregando configuração...</div>
  if (filtersQuery.isError) return <div className="mx-auto max-w-3xl px-6 py-16 text-rose-600">Não foi possível carregar a configuração.</div>

  return (
    <div className="mx-auto max-w-4xl px-4 py-7 sm:px-6 sm:py-10 lg:px-10">
      <div className="mb-8">
        <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-rose-500">Filtros</p>
        <h1 className="text-3xl font-semibold tracking-[-0.04em] sm:text-4xl">Configure sua busca.</h1>
        <p className="mt-3 max-w-xl leading-7 text-slate-500">Essas regras controlam as próximas coletas automáticas. Acompanhe e dispare execuções na tela de Integrações.</p>
      </div>
      <form className="space-y-6" onSubmit={(event) => { event.preventDefault(); saveMutation.mutate(filters) }}>
        <section className="grid gap-4 rounded-2xl border border-slate-200 bg-white p-4 sm:p-6 md:grid-cols-2">
          <label className="label">Cidade<input className="field mt-2" value={filters.city} onChange={(event) => setField('city', event.target.value)} /></label>
          <label className="label">Estado<input className="field mt-2" maxLength={2} value={filters.state} onChange={(event) => setField('state', event.target.value.toUpperCase())} /></label>
          <label className="label">Finalidade<select className="field mt-2" value={filters.purpose} onChange={(event) => setField('purpose', event.target.value)}><option value="sale">Compra</option><option value="rent">Aluguel</option></select></label>
          <label className="label md:col-span-2">Bairros <span className="font-normal text-slate-400">separados por vírgula</span><input className="field mt-2" value={filters.neighborhoods.join(', ')} onChange={(event) => setField('neighborhoods', splitList(event.target.value))} /></label>
          <label className="label">Preço máximo<input className="field mt-2" type="number" value={filters.max_price ?? ''} onChange={(event) => setField('max_price', event.target.value ? Number(event.target.value) : null)} /></label>
          <label className="label">Quartos mínimos<input className="field mt-2" type="number" min={0} value={filters.bedrooms_min ?? ''} onChange={(event) => setField('bedrooms_min', event.target.value ? Number(event.target.value) : null)} /></label>
          <label className="label md:col-span-2">Fontes <span className="font-normal text-slate-400">separadas por vírgula</span><input className="field mt-2" value={filters.sources.join(', ')} onChange={(event) => setField('sources', splitList(event.target.value))} /></label>
          <label className="flex items-center gap-3 text-sm font-medium"><input type="checkbox" checked={filters.geocoding_enabled} onChange={(event) => setField('geocoding_enabled', event.target.checked)} /> Geocodificar anúncios sem coordenadas</label>
          <label className="label">Máximo de páginas<input className="field mt-2" type="number" min={1} value={filters.max_pages} onChange={(event) => setField('max_pages', Number(event.target.value))} /></label>
        </section>
        <div className="flex items-center justify-end">
          <button className="button-secondary w-full sm:w-auto" type="submit" disabled={saveMutation.isPending}>{saveMutation.isPending ? 'Salvando...' : 'Salvar configuração'}</button>
        </div>
      </form>
    </div>
  )
}
