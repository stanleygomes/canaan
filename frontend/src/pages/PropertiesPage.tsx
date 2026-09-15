import { useMemo, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { PropertyCard } from '../components/PropertyCard'
import { PropertyMap } from '../components/PropertyMap'
import { listProperties } from '../lib/api/properties'
import type { PropertyListParams } from '../lib/api/types'

const initialFilters: PropertyListParams = { page: 1, page_size: 24, sort_by: 'last_seen_at', sort_order: 'desc' }

export function PropertiesPage() {
  const [filters, setFilters] = useState<PropertyListParams>(initialFilters)
  const [selectedId, setSelectedId] = useState<number>()
  const query = useQuery({ queryKey: ['properties', filters], queryFn: () => listProperties(filters) })
  const properties = query.data?.items ?? []
  const selected = useMemo(() => properties.find((item) => item.id === selectedId), [properties, selectedId])

  const updateFilter = (key: keyof PropertyListParams, value: string) => {
    setFilters((current) => ({ ...current, page: 1, [key]: value || undefined }))
  }

  return (
    <div className="mx-auto max-w-[1440px] px-6 py-8 lg:px-10 lg:py-10">
      <section className="mb-8 flex flex-col justify-between gap-5 lg:flex-row lg:items-end">
        <div>
          <p className="mb-2 text-sm font-semibold uppercase tracking-[0.18em] text-rose-500">Busca inteligente</p>
          <h1 className="text-4xl font-semibold tracking-[-0.04em] text-slate-950 lg:text-5xl">Encontre seu próximo imóvel.</h1>
          <p className="mt-3 max-w-xl text-base leading-7 text-slate-500">Anúncios reunidos em um só lugar, com filtros simples e uma visão clara do que importa.</p>
        </div>
        <p className="text-sm text-slate-500">{query.data?.total ?? 0} imóveis cadastrados</p>
      </section>

      <div className="mb-6 grid gap-3 rounded-2xl border border-slate-200 bg-white p-4 md:grid-cols-2 xl:grid-cols-6">
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

      <div className="grid gap-6 xl:grid-cols-[minmax(0,0.9fr)_minmax(520px,1.1fr)]">
        <section>
          {query.isLoading && <p className="py-12 text-center text-slate-500">Carregando imóveis...</p>}
          {query.isError && <p className="rounded-2xl bg-rose-50 p-5 text-sm text-rose-700">Não foi possível carregar os imóveis.</p>}
          {!query.isLoading && !query.isError && properties.length === 0 && <p className="rounded-2xl border border-dashed border-slate-300 p-10 text-center text-slate-500">Nenhum imóvel encontrado com esses filtros.</p>}
          <div className="grid gap-5 md:grid-cols-2">
            {properties.map((property) => (
              <a key={property.id} href={property.url} target="_blank" rel="noreferrer" onClick={(event) => { event.preventDefault(); setSelectedId(property.id) }}>
                <PropertyCard property={property} selected={selected?.id === property.id} onSelect={() => setSelectedId(property.id)} />
              </a>
            ))}
          </div>
        </section>
        <aside className="sticky top-6 hidden h-[calc(100vh-8rem)] min-h-[520px] xl:block">
          <PropertyMap properties={properties} selectedId={selectedId} onSelect={setSelectedId} />
        </aside>
      </div>
    </div>
  )
}
