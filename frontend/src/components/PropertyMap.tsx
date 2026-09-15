import { useEffect, useRef } from 'react'
import maplibregl, { type Map, type Marker } from 'maplibre-gl'
import type { Property } from '../lib/api/types'

const styleUrl = import.meta.env.VITE_MAP_STYLE_URL ?? 'https://demotiles.maplibre.org/style.json'

export function PropertyMap({ properties, selectedId, onSelect }: { properties: Property[]; selectedId?: number; onSelect: (id: number) => void }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const markersRef = useRef<Marker[]>([])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: [-48.2772, -18.9186],
      zoom: 11,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')
    mapRef.current = map
    return () => {
      markersRef.current.forEach((marker) => marker.remove())
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    markersRef.current.forEach((marker) => marker.remove())
    markersRef.current = properties.flatMap((property) => {
      const latitude = property.geo.latitude
      const longitude = property.geo.longitude
      if (latitude === undefined || longitude === undefined) return []
      const marker = new maplibregl.Marker({ color: property.id === selectedId ? '#e11d48' : '#0f172a' })
        .setLngLat([longitude, latitude])
        .addTo(map)
      marker.getElement().addEventListener('click', () => onSelect(property.id))
      return [marker]
    })
  }, [properties, selectedId, onSelect])

  return <div ref={containerRef} className="h-full min-h-[520px] w-full overflow-hidden rounded-2xl" />
}
