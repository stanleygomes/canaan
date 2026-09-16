import type { Property } from '../lib/api/types'
import { Link } from 'react-router-dom'

function formatPrice(value: number | null, currency: string) {
  if (value === null) return 'Preço sob consulta'
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: currency || 'BRL',
    maximumFractionDigits: 0,
  }).format(value)
}

function addressLabel(property: Property) {
  const address = property.address
  return String(address.locality ?? address.raw_text ?? 'Localização não informada')
}

function portalLabel(portal: string) {
  const labels: Record<string, string> = {
    chavesnamao: 'Chaves na Mão',
    imovelweb: 'Imovelweb',
    mercadolivre: 'Mercado Livre',
    quintoandar: 'QuintoAndar',
    vivareal: 'Viva Real',
    zapimoveis: 'ZAP Imóveis',
  }
  return labels[portal] ?? portal
}

export function PropertyCard({ property, selected, onSelect }: { property: Property; selected?: boolean; onSelect: () => void }) {
  const image = property.images[0]
  return (
    <article
      className={`group overflow-hidden rounded-2xl border bg-white transition ${selected ? 'border-slate-950 ring-2 ring-slate-950/10' : 'border-slate-200 hover:border-slate-400'}`}
      onClick={onSelect}
    >
      <div className="relative aspect-[4/3] overflow-hidden bg-slate-100">
        {image ? (
          <img src={image} alt={property.title || 'Imóvel'} className="h-full w-full object-cover transition duration-500 group-hover:scale-[1.03]" />
        ) : (
          <div className="flex h-full items-center justify-center text-sm text-slate-400">Sem foto disponível</div>
        )}
        <span className="absolute left-3 top-3 rounded-full bg-white/95 px-3 py-1 text-xs font-semibold text-slate-700">
          {portalLabel(property.portal)}
        </span>
      </div>
      <div className="space-y-2 p-4">
        <p className="line-clamp-1 text-sm font-medium text-slate-500">{addressLabel(property)}</p>
        <Link to={`/imoveis/${property.id}`} className="block rounded-sm focus:outline-none focus:ring-2 focus:ring-slate-950/20">
          <h2 className="line-clamp-2 min-h-12 text-[17px] font-semibold leading-6 tracking-[-0.01em] text-slate-950">
            {property.title || 'Imóvel sem título'}
          </h2>
        </Link>
        <p className="text-lg font-semibold text-slate-950">{formatPrice(property.price, property.currency)}</p>
        <div className="flex gap-4 pt-1 text-sm text-slate-500">
          {property.bedrooms !== null && <span>{property.bedrooms} quartos</span>}
          {property.useful_area_m2 !== null && <span>{property.useful_area_m2} m²</span>}
          {property.garages !== null && <span>{property.garages} vagas</span>}
        </div>
        <a
          href={property.url}
          target="_blank"
          rel="noreferrer"
          onClick={(event) => event.stopPropagation()}
          className="inline-flex pt-1 text-sm font-semibold text-slate-700 underline decoration-slate-300 underline-offset-4 transition hover:text-slate-950 hover:decoration-slate-950"
        >
          Ver anúncio no {portalLabel(property.portal)} ↗
        </a>
      </div>
    </article>
  )
}
