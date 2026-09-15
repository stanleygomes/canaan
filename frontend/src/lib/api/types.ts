export type Geo = {
  latitude?: number
  longitude?: number
  precision?: string
  provider?: string
  [key: string]: unknown
}

export type Property = {
  id: number
  portal: string
  url: string
  title: string
  description: string
  price: number | null
  condominium_fee: number | null
  iptu_fee: number | null
  currency: string
  property_type: string | null
  bedrooms: number | null
  suites: number | null
  bathrooms: number | null
  garages: number | null
  useful_area_m2: number | null
  total_area_m2: number | null
  address: Record<string, unknown>
  geo: Geo
  advertiser: Record<string, unknown>
  amenities: unknown[]
  images: string[]
  collected_at: string | null
  first_seen_at: string
  last_seen_at: string
}

export type PropertyListResponse = {
  items: Property[]
  page: number
  page_size: number
  total: number
}

export type PropertyListParams = {
  page?: number
  page_size?: number
  portal?: string
  city?: string
  neighborhood?: string
  price_max?: number
  bedrooms_min?: number
  min_lat?: number
  min_lon?: number
  max_lat?: number
  max_lon?: number
}
