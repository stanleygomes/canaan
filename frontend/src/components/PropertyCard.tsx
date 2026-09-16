import { useState } from 'react'
import type { Property } from '../lib/api/types'
import { apiUrl } from '../lib/api/client'

function formatPrice(value: number | null, currency: string) {
  if (value === null) return 'Preço sob consulta'
  return new Intl.NumberFormat('pt-BR', { style: 'currency', currency: currency || 'BRL', maximumFractionDigits: 0 }).format(value)
}

function formatDate(value: string | null) {
  if (!value) return null
  return new Intl.DateTimeFormat('pt-BR', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
}

function textValue(value: unknown) {
  return value === null || value === undefined || value === '' ? null : String(value)
}

function portalLabel(portal: string) {
  const labels: Record<string, string> = { chavesnamao: 'Chaves na Mão', imovelweb: 'Imovelweb', mercadolivre: 'Mercado Livre', quintoandar: 'QuintoAndar', vivareal: 'Viva Real', zapimoveis: 'ZAP Imóveis' }
  return labels[portal] ?? portal
}

function addressParts(property: Property) {
  const address = property.address
  return [textValue(address.street), textValue(address.locality), textValue(address.region), textValue(address.postal_code)].filter(Boolean) as string[]
}

function Detail({ label, value }: { label: string; value: unknown }) {
  const content = textValue(value)
  if (!content) return null
  return <div><dt className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">{label}</dt><dd className="mt-0.5 text-sm text-slate-700">{content}</dd></div>
}

export function PropertyCard({ property, selected, onSelect }: { property: Property; selected?: boolean; onSelect: () => void }) {
  const [currentImage, setCurrentImage] = useState(0)
  const images = property.images
  const image = images[currentImage]
  const imageUrl = image ? apiUrl(`/api/v1/images?url=${encodeURIComponent(image)}`) : undefined
  const address = addressParts(property)
  const amenities = property.amenities.map(textValue).filter(Boolean) as string[]
  const location = textValue(property.address.locality) ?? textValue(property.address.raw_text) ?? 'Localização não informada'
  const previousImage = () => setCurrentImage((current) => (current - 1 + images.length) % images.length)
  const nextImage = () => setCurrentImage((current) => (current + 1) % images.length)

  return (
    <article className={`group overflow-hidden rounded-2xl border bg-white transition ${selected ? 'border-slate-950 ring-2 ring-slate-950/10' : 'border-slate-200 hover:border-slate-400'}`} onClick={onSelect}>
      <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
        {imageUrl ? <img src={imageUrl} alt={`${property.title || 'Imóvel'} - foto ${currentImage + 1}`} className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]" /> : <div className="flex h-full items-center justify-center text-sm text-slate-400">Sem foto disponível</div>}
        <span className="absolute left-3 top-3 rounded-full bg-white/95 px-3 py-1 text-xs font-semibold text-slate-700">{portalLabel(property.portal)}</span>
        {images.length > 1 && <>
          <button type="button" aria-label="Foto anterior" onClick={(event) => { event.stopPropagation(); previousImage() }} className="absolute left-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-xl text-slate-950 shadow-sm transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-slate-950">‹</button>
          <button type="button" aria-label="Próxima foto" onClick={(event) => { event.stopPropagation(); nextImage() }} className="absolute right-3 top-1/2 flex h-9 w-9 -translate-y-1/2 items-center justify-center rounded-full bg-white/90 text-xl text-slate-950 shadow-sm transition hover:bg-white focus:outline-none focus:ring-2 focus:ring-slate-950">›</button>
          <div className="absolute bottom-3 left-1/2 flex -translate-x-1/2 gap-1.5 rounded-full bg-slate-950/55 px-2 py-1">{images.slice(0, 6).map((_, index) => <button key={index} type="button" aria-label={`Ir para foto ${index + 1}`} onClick={(event) => { event.stopPropagation(); setCurrentImage(index) }} className={`h-1.5 rounded-full transition ${index === currentImage ? 'w-4 bg-white' : 'w-1.5 bg-white/60'}`} />)}</div>
        </>}
      </div>

      <div className="space-y-4 p-4">
        <div>
          <p className="text-sm font-medium text-slate-500">{location}</p>
          <h2 className="mt-1 line-clamp-2 text-[17px] font-semibold leading-6 tracking-[-0.01em] text-slate-950">{property.title || 'Imóvel sem título'}</h2>
          <p className="mt-2 text-xl font-semibold text-slate-950">{formatPrice(property.price, property.currency)}</p>
        </div>
        <dl className="grid grid-cols-2 gap-x-4 gap-y-3 border-y border-slate-100 py-3 sm:grid-cols-3">
          <Detail label="Tipo" value={property.property_type} /><Detail label="Quartos" value={property.bedrooms} /><Detail label="Suítes" value={property.suites} /><Detail label="Banheiros" value={property.bathrooms} /><Detail label="Vagas" value={property.garages} /><Detail label="Área útil" value={property.useful_area_m2 ? `${property.useful_area_m2} m²` : null} /><Detail label="Área total" value={property.total_area_m2 ? `${property.total_area_m2} m²` : null} /><Detail label="Condomínio" value={property.condominium_fee !== null ? formatPrice(property.condominium_fee, property.currency) : null} /><Detail label="IPTU" value={property.iptu_fee !== null ? formatPrice(property.iptu_fee, property.currency) : null} />
        </dl>
        {address.length > 0 && <div><p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Endereço informado</p><p className="mt-1 text-sm text-slate-700">{address.join(' · ')}</p></div>}
        {property.description && <p className="line-clamp-4 text-sm leading-6 text-slate-600">{property.description}</p>}
        {amenities.length > 0 && <div><p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">Características</p><p className="mt-1 text-sm leading-6 text-slate-700">{amenities.join(' · ')}</p></div>}
        <dl className="grid grid-cols-2 gap-3 text-xs"><Detail label="Anunciante" value={property.advertiser.name} /><Detail label="Coletado em" value={formatDate(property.collected_at)} /><Detail label="Visto pela primeira vez" value={formatDate(property.first_seen_at)} /><Detail label="Visto por último" value={formatDate(property.last_seen_at)} /></dl>
        <a href={property.url} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()} className="flex w-full items-center justify-center gap-2 rounded-xl bg-slate-950 px-4 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-rose-600 focus:outline-none focus:ring-2 focus:ring-rose-500 focus:ring-offset-2">Abrir anúncio no {portalLabel(property.portal)} <span aria-hidden="true">↗</span></a>
      </div>
    </article>
  )
}
