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
  return <div className="rounded-2xl border-2 border-slate-200 bg-slate-50 p-3"><dt className="text-[11px] font-extrabold uppercase tracking-wide text-slate-500">{label}</dt><dd className="mt-1 text-base font-bold leading-5 text-slate-950">{content}</dd></div>
}

export function PropertyCard({ property, selected, onSelect }: { property: Property; selected?: boolean; onSelect: () => void }) {
  const [currentImage, setCurrentImage] = useState(0)
  const images = property.images
  const image = images[currentImage]
  const imageUrl = image ? apiUrl(`/api/v1/images?url=${encodeURIComponent(image)}`) : undefined
  const address = addressParts(property)
  const amenities = property.amenities.map(textValue).filter(Boolean) as string[]
  const location = textValue(property.address.locality) ?? textValue(property.address.raw_text) ?? 'Localização não informada'
  const neighborhood = textValue(property.address.locality) ?? textValue(property.address.raw_text)
  const agency = textValue(property.advertiser.name)
  const previousImage = () => setCurrentImage((current) => (current - 1 + images.length) % images.length)
  const nextImage = () => setCurrentImage((current) => (current + 1) % images.length)

  return (
    <article className={`group overflow-hidden rounded-[2rem] border-2 bg-white shadow-[5px_5px_0_#0f172a] transition hover:-translate-y-1 hover:shadow-[8px_8px_0_#0f172a] ${selected ? 'border-rose-500 ring-4 ring-rose-500/20' : 'border-slate-950'}`} onClick={onSelect}>
      <div className="relative aspect-[5/4] overflow-hidden bg-slate-100">
        {imageUrl ? <img src={imageUrl} alt={`${property.title || 'Imóvel'} - foto ${currentImage + 1}`} className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]" /> : <div className="flex h-full items-center justify-center text-sm text-slate-400">Sem foto disponível</div>}
        {images.length > 1 && <>
          <button type="button" aria-label="Foto anterior" onClick={(event) => { event.stopPropagation(); previousImage() }} className="absolute left-4 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-xl border-2 border-slate-950 bg-white text-xl font-extrabold text-slate-950 shadow-[2px_2px_0_#0f172a] transition hover:bg-rose-100 focus:outline-none focus:ring-4 focus:ring-rose-300">‹</button>
          <button type="button" aria-label="Próxima foto" onClick={(event) => { event.stopPropagation(); nextImage() }} className="absolute right-4 top-1/2 flex h-10 w-10 -translate-y-1/2 items-center justify-center rounded-xl border-2 border-slate-950 bg-white text-xl font-extrabold text-slate-950 shadow-[2px_2px_0_#0f172a] transition hover:bg-rose-100 focus:outline-none focus:ring-4 focus:ring-rose-300">›</button>
          <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 gap-1.5 rounded-xl border-2 border-slate-950 bg-slate-950/80 px-2 py-1.5">{images.slice(0, 6).map((_, index) => <button key={index} type="button" aria-label={`Ir para foto ${index + 1}`} onClick={(event) => { event.stopPropagation(); setCurrentImage(index) }} className={`h-2 rounded-full transition ${index === currentImage ? 'w-5 bg-white' : 'w-2 bg-white/60'}`} />)}</div>
        </>}
      </div>

      <div className="space-y-5 p-5">
        <div>
          <div className="flex flex-wrap gap-2">
            {neighborhood && <span className="max-w-full truncate rounded-full border-2 border-rose-200 bg-rose-50 px-3 py-1 text-xs font-extrabold text-rose-800">Bairro · {neighborhood}</span>}
            <span className="max-w-full truncate rounded-full border-2 border-slate-200 bg-slate-100 px-3 py-1 text-xs font-extrabold text-slate-800">Imobiliária · {agency ?? portalLabel(property.portal)}</span>
          </div>
          <p className="mt-3 text-sm font-extrabold uppercase tracking-wide text-slate-500">{location}</p>
          <h2 className="mt-2 line-clamp-2 text-2xl font-extrabold leading-7 tracking-[-0.04em] text-slate-950">{property.title || 'Imóvel sem título'}</h2>
          <div className="mt-4 rounded-2xl bg-slate-950 px-4 py-3 text-white"><p className="text-[11px] font-extrabold uppercase tracking-[0.16em] text-slate-300">Preço anunciado</p><p className="mt-1 text-2xl font-extrabold tracking-[-0.04em]">{formatPrice(property.price, property.currency)}</p></div>
        </div>
        <dl className="grid grid-cols-2 gap-2 sm:grid-cols-3">
          <Detail label="Tipo" value={property.property_type} /><Detail label="Quartos" value={property.bedrooms} /><Detail label="Suítes" value={property.suites} /><Detail label="Banheiros" value={property.bathrooms} /><Detail label="Vagas" value={property.garages} /><Detail label="Área útil" value={property.useful_area_m2 ? `${property.useful_area_m2} m²` : null} /><Detail label="Área total" value={property.total_area_m2 ? `${property.total_area_m2} m²` : null} /><Detail label="Condomínio" value={property.condominium_fee !== null ? formatPrice(property.condominium_fee, property.currency) : null} /><Detail label="IPTU" value={property.iptu_fee !== null ? formatPrice(property.iptu_fee, property.currency) : null} />
        </dl>
        {address.length > 0 && <div className="rounded-2xl border-2 border-slate-200 p-4"><p className="text-[11px] font-extrabold uppercase tracking-wide text-slate-500">Endereço informado</p><p className="mt-1 text-base font-bold leading-6 text-slate-950">{address.join(' · ')}</p></div>}
        {property.description && <div className="rounded-2xl bg-amber-100 p-4"><p className="text-[11px] font-extrabold uppercase tracking-wide text-amber-900">Sobre o imóvel</p><p className="mt-1 line-clamp-4 text-sm font-semibold leading-6 text-slate-900">{property.description}</p></div>}
        {amenities.length > 0 && <div><p className="text-[11px] font-extrabold uppercase tracking-wide text-slate-500">Características</p><p className="mt-1 text-sm font-semibold leading-6 text-slate-800">{amenities.join(' · ')}</p></div>}
        <dl className="grid grid-cols-2 gap-2"><Detail label="Anunciante" value={property.advertiser.name} /><Detail label="Coletado em" value={formatDate(property.collected_at)} /><Detail label="Visto pela primeira vez" value={formatDate(property.first_seen_at)} /><Detail label="Visto por último" value={formatDate(property.last_seen_at)} /></dl>
        <a href={property.url} target="_blank" rel="noreferrer" onClick={(event) => event.stopPropagation()} className="flex w-full items-center justify-center gap-2 rounded-2xl border-2 border-rose-600 bg-rose-500 px-4 py-4 text-base font-extrabold text-white shadow-[3px_3px_0_#9f1239] transition hover:bg-rose-600 focus:outline-none focus:ring-4 focus:ring-rose-300">Abrir anúncio no {portalLabel(property.portal)} <span aria-hidden="true">↗</span></a>
      </div>
    </article>
  )
}
