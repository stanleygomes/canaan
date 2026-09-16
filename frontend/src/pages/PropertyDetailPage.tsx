import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router-dom'
import { apiUrl } from '../lib/api/client'
import { getProperty } from '../lib/api/properties'

function formatPrice(value: number | null, currency: string) {
  if (value === null) return 'Preço sob consulta'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: currency || 'BRL',
    maximumFractionDigits: 0,
  }).format(value)
}

function addressLabel(address: Record<string, unknown>) {
  return String(address.locality ?? address.raw_text ?? 'Localização não informada')
}

export function PropertyDetailPage() {
  const { propertyId } = useParams()
  const id = Number(propertyId)
  const query = useQuery({ queryKey: ['property', id], queryFn: () => getProperty(id), enabled: Number.isInteger(id) && id > 0 })

  if (query.isLoading) return <div className="mx-auto max-w-5xl px-6 py-16 text-slate-500">Carregando imóvel...</div>
  if (query.isError || !query.data) return <div className="mx-auto max-w-5xl px-6 py-16"><p className="text-rose-600">Não foi possível carregar este imóvel.</p><Link className="mt-5 inline-block text-sm font-semibold underline" to="/">Voltar para imóveis</Link></div>

  const property = query.data
  const images = property.images.slice(0, 5)
  const advertiserName = property.advertiser.name ? String(property.advertiser.name) : null
  const attributes = [
    property.bedrooms !== null && [`${property.bedrooms}`, 'quartos'],
    property.bathrooms !== null && [`${property.bathrooms}`, 'banheiros'],
    property.useful_area_m2 !== null && [`${property.useful_area_m2} m²`, 'área útil'],
    property.garages !== null && [`${property.garages}`, 'vagas'],
  ].filter(Boolean) as string[][]

  return (
    <div className="mx-auto max-w-5xl px-4 py-6 sm:px-6 sm:py-8 lg:px-10 lg:py-10">
      <Link to="/" className="text-sm font-semibold text-slate-500 transition hover:text-slate-950">← Voltar para imóveis</Link>
      <div className="mt-6 grid gap-2 overflow-hidden rounded-2xl bg-slate-100 md:mt-7 md:grid-cols-2">
        {images.length > 0 ? images.map((image, index) => (
          <img key={image} src={apiUrl(`/api/v1/images?url=${encodeURIComponent(image)}`)} alt={`${property.title || 'Imóvel'} - foto ${index + 1}`} className={`h-64 w-full object-cover md:h-80 ${index === 0 ? 'md:row-span-2 md:h-full' : ''}`} />
        )) : <div className="flex h-80 items-center justify-center text-slate-400 md:row-span-2">Sem fotos disponíveis</div>}
      </div>
      <div className="mt-8 grid gap-10 lg:grid-cols-[1fr_280px]">
        <section>
          <div className="flex flex-col items-start justify-between gap-3 sm:flex-row sm:gap-5">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.14em] text-rose-500">{property.portal}</p>
              <h1 className="mt-2 text-3xl font-semibold tracking-[-0.04em] text-slate-950">{property.title || 'Imóvel sem título'}</h1>
              <p className="mt-3 text-base text-slate-500">{addressLabel(property.address)}</p>
            </div>
            <p className="text-xl font-semibold text-slate-950 sm:whitespace-nowrap">{formatPrice(property.price, property.currency)}</p>
          </div>
          <div className="mt-8 grid grid-cols-2 gap-3 sm:grid-cols-4">
            {attributes.map(([value, label]) => <div key={label} className="rounded-xl border border-slate-200 bg-white p-4"><p className="font-semibold text-slate-950">{value}</p><p className="mt-1 text-xs text-slate-500">{label}</p></div>)}
          </div>
          {property.description && <div className="mt-9 border-t border-slate-200 pt-7"><h2 className="text-lg font-semibold">Sobre este imóvel</h2><p className="mt-3 whitespace-pre-line leading-7 text-slate-600">{property.description}</p></div>}
        </section>
        <aside className="h-fit rounded-2xl border border-slate-200 bg-white p-5 lg:sticky lg:top-6">
          <p className="text-sm text-slate-500">Anunciado em</p>
          <p className="mt-1 font-semibold text-slate-950">{property.portal}</p>
          <a href={property.url} target="_blank" rel="noreferrer" className="button-primary mt-6 block text-center">Ver anúncio original</a>
          {advertiserName && <p className="mt-5 border-t border-slate-200 pt-5 text-sm text-slate-500">Anunciante<br /><strong className="text-slate-950">{advertiserName}</strong></p>}
        </aside>
      </div>
    </div>
  )
}
