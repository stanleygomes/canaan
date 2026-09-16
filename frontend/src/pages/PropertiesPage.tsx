import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PropertyCard } from '../components/PropertyCard'
import { PropertyMap } from '../components/PropertyMap'
import { listProperties } from '../lib/api/properties'
import type { PropertyListParams } from '../lib/api/types'

const initialFilters: PropertyListParams = { page: 1, page_size: 50, sort_by: 'last_seen_at', sort_order: 'desc' }

export function PropertiesPage() {
  const [filters, setFilters] = useState<PropertyListParams>(initialFilters)
  const [selectedId, setSelectedId] = useState<number>()
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list')
  const queryFilters = viewMode === 'map' ? { ...filters, page: 1, page_size: 100 } : filters
  const query = useQuery({ queryKey: ['properties', queryFilters], queryFn: () => listProperties(queryFilters) })
  const properties = query.data?.items ?? []
  const selected = useMemo(() => properties.find((item) => item.id === selectedId), [properties, selectedId])
  const currentPage = filters.page ?? 1
  const pageSize = filters.page_size ?? 50
  const totalPages = Math.max(1, Math.ceil((query.data?.total ?? 0) / pageSize))

  const updateFilter = (key: keyof PropertyListParams, value: string) => {
    setFilters((current) => ({ ...current, page: 1, [key]: value || undefined }))
  }

  return (
    <div className="mx-auto max-w-[1440px] px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
      <section className="mb-6 flex flex-col justify-between gap-5 sm:mb-8 lg:flex-row lg:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-rose-500">Busca inteligente</p>
          <h1 className="text-3xl font-semibold tracking-[-0.04em] text-slate-950 sm:text-4xl lg:text-5xl">Encontre seu próximo imóvel.</h1>
          <p className="mt-3 max-w-xl text-base leading-7 text-slate-500">Anúncios reunidos em um só lugar, com filtros simples e uma visão clara do que importa.</p>
        </div>
        <div className="flex flex-wrap items-center justify-between gap-3 sm:justify-start sm:gap-4">
          <p className="text-sm text-slate-500">{query.data?.total ?? 0} imóveis cadastrados</p>
          <div className="flex rounded-full border border-slate-200 bg-white p-1 text-sm font-semibold">
            <button type="button" className={`rounded-full px-4 py-2 transition ${viewMode === 'list' ? 'bg-slate-950 text-white' : 'text-slate-500 hover:text-slate-950'}`} onClick={() => setViewMode('list')}>
              Lista
            </button>
            <button type="button" className={`rounded-full px-4 py-2 transition ${viewMode === 'map' ? 'bg-slate-950 text-white' : 'text-slate-500 hover:text-slate-950'}`} onClick={() => setViewMode('map')}>
              Mapa
            </button>
          </div>
        </div>
      </section>

      <div className="mb-5 grid gap-3 rounded-2xl border border-slate-200 bg-white p-3 sm:mb-6 sm:p-4 md:grid-cols-2 xl:grid-cols-6">
        <input className="field" placeholder="Cidade" value={filters.city ?? ''} onChange={(event) => updateFilter('city', event.target.value)} />
        <input className="field" placeholder="Bairro" value={filters.neighborhood ?? ''} onChange={(event) => updateFilter('neighborhood', event.target.value)} />
        <input className="field" type="number" placeholder="Preço máximo" value={filters.price_max ?? ''} onChange={(event) => updateFilter('price_max', event.target.value)} />
        <input className="field" type="number" placeholder="Quartos mínimos" value={filters.bedrooms_min ?? ''} onChange={(event) => updateFilter('bedrooms_min', event.target.value)} />
        <select className="field" value={filters.sort_by} onChange={(event) => updateFilter('sort_by', event.target.value)}>
          <option value="last_seen_at">Mais recentes</option>
          <option value="price">Preço</option>
          <option value="useful_area_m2">Área</option>
          <option value="bedrooms">Quartos</option>
        </select>
        <select className="field" value={filters.sort_order} onChange={(event) => updateFilter('sort_order', event.target.value)}>
          <option value="desc">Maior para menor</option>
          <option value="asc">Menor para maior</option>
        </select>
      </div>

      {viewMode === 'map' ? (
        <section className="space-y-4">
          <div className="h-[60vh] min-h-[360px] rounded-2xl border border-slate-200 bg-white p-2 sm:h-[520px] lg:h-[calc(100vh-19rem)] lg:min-h-[520px]">
            <PropertyMap properties={properties} selectedId={selectedId} onSelect={setSelectedId} />
          </div>
          <p className="text-sm text-slate-500">Os marcadores exibem apenas imóveis com coordenadas geográficas.</p>
        </section>
      ) : (
        <div className="grid gap-6">
          <section>
          {query.isLoading && <p className="py-12 text-center text-slate-500">Carregando imóveis...</p>}
          {query.isError && <p className="rounded-2xl bg-rose-50 p-5 text-sm text-rose-700">Não foi possível carregar os imóveis.</p>}
          {!query.isLoading && !query.isError && properties.length === 0 && <p className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500">Nenhum imóvel encontrado com esses filtros.</p>}
          <div className="grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {properties.map((property) => (
              <PropertyCard key={property.id} property={property} selected={selected?.id === property.id} onSelect={() => setSelectedId(property.id)} />
            ))}
          </div>
          {totalPages > 1 && (
            <div className="mt-8 flex items-center justify-between gap-3 border-t border-slate-200 pt-5">
              <button
                type="button"
                className="button-secondary"
                disabled={currentPage === 1 || query.isFetching}
                onClick={() => setFilters((current) => ({ ...current, page: currentPage - 1 }))}
              >
                Anterior
              </button>
              <span className="text-sm text-slate-500">
                Página {currentPage} de {totalPages}
              </span>
              <button
                type="button"
                className="button-secondary"
                disabled={currentPage >= totalPages || query.isFetching}
                onClick={() => setFilters((current) => ({ ...current, page: currentPage + 1 }))}
              >
                Próxima
              </button>
            </div>
          )}
          </section>
        </div>
      )}
    </div>
  )
}
