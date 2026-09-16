import { useEffect, useRef } from 'react'
import maplibregl, { type Map } from 'maplibre-gl'
import type { Property } from '../lib/api/types'

const styleUrl = import.meta.env.VITE_MAP_STYLE_URL ?? 'https://tiles.openfreemap.org/styles/positron'

export function PropertyMap({ properties, selectedId, onSelect }: { properties: Property[]; selectedId?: number; onSelect: (id: number) => void }) {
  const containerRef = useRef<HTMLDivElement>(null)
  const mapRef = useRef<Map | null>(null)
  const onSelectRef = useRef(onSelect)

  useEffect(() => {
    onSelectRef.current = onSelect
  }, [onSelect])

  useEffect(() => {
    if (!containerRef.current || mapRef.current) return
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: styleUrl,
      center: [-48.2772, -18.9186],
      zoom: 11,
    })
    map.addControl(new maplibregl.NavigationControl(), 'top-right')

    map.on('load', () => {
      map.addSource('properties', {
        type: 'geojson',
        data: { type: 'FeatureCollection', features: [] },
        cluster: true,
        clusterMaxZoom: 14,
        clusterRadius: 48,
      })
      map.addLayer({
        id: 'property-clusters',
        type: 'circle',
        source: 'properties',
        filter: ['has', 'point_count'],
        paint: {
          'circle-color': ['step', ['get', 'point_count'], '#0f172a', 10, '#334155', 30, '#e11d48'],
          'circle-radius': ['step', ['get', 'point_count'], 18, 10, 23, 30, 29],
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
      })
      map.addLayer({
        id: 'property-cluster-count',
        type: 'symbol',
        source: 'properties',
        filter: ['has', 'point_count'],
        layout: {
          'text-field': '{point_count_abbreviated}',
          'text-size': 12,
        },
        paint: { 'text-color': '#ffffff' },
      })
      map.addLayer({
        id: 'property-points',
        type: 'circle',
        source: 'properties',
        filter: ['!', ['has', 'point_count']],
        paint: {
          'circle-color': '#0f172a',
          'circle-radius': 7,
          'circle-stroke-width': 2,
          'circle-stroke-color': '#ffffff',
        },
      })
      map.addLayer({
        id: 'property-selected-point',
        type: 'circle',
        source: 'properties',
        filter: ['==', ['get', 'propertyId'], -1],
        paint: {
          'circle-color': '#e11d48',
          'circle-radius': 11,
          'circle-stroke-width': 3,
          'circle-stroke-color': '#ffffff',
        },
      })

      map.on('click', 'property-clusters', async (event) => {
        const features = map.queryRenderedFeatures(event.point, { layers: ['property-clusters'] })
        const clusterId = features[0]?.properties?.cluster_id
        const source = map.getSource('properties') as maplibregl.GeoJSONSource
        if (clusterId === undefined || !source) return
        const zoom = await source.getClusterExpansionZoom(clusterId)
        const geometry = features[0]?.geometry
        if (geometry?.type === 'Point') map.easeTo({ center: geometry.coordinates as [number, number], zoom })
      })
      map.on('click', 'property-points', (event) => {
        const propertyId = featuresPropertyId(map.queryRenderedFeatures(event.point, { layers: ['property-points'] })[0])
        if (propertyId !== undefined) onSelectRef.current(propertyId)
      })
      map.on('mouseenter', 'property-clusters', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseenter', 'property-points', () => { map.getCanvas().style.cursor = 'pointer' })
      map.on('mouseleave', 'property-clusters', () => { map.getCanvas().style.cursor = '' })
      map.on('mouseleave', 'property-points', () => { map.getCanvas().style.cursor = '' })
    })
    mapRef.current = map
    return () => {
      map.remove()
      mapRef.current = null
    }
  }, [])

  useEffect(() => {
    const map = mapRef.current
    if (!map) return
    const updateSource = () => {
      const source = map.getSource('properties') as maplibregl.GeoJSONSource | undefined
      if (!source) return
      source.setData({
        type: 'FeatureCollection',
        features: properties.flatMap((property) => {
          const latitude = property.geo.latitude
          const longitude = property.geo.longitude
          if (latitude === undefined || longitude === undefined) return []
          return [{
            type: 'Feature' as const,
            geometry: { type: 'Point' as const, coordinates: [longitude, latitude] },
            properties: { propertyId: property.id, title: property.title },
          }]
        }),
      })
      if (map.getLayer('property-selected-point')) {
        map.setFilter('property-selected-point', ['==', ['get', 'propertyId'], selectedId ?? -1])
      }
    }
    if (map.isStyleLoaded()) updateSource()
    else map.once('load', updateSource)
    return () => { map.off('load', updateSource) }
  }, [properties, selectedId])

  return <div ref={containerRef} className="h-full min-h-[520px] w-full overflow-hidden rounded-2xl" />
}

function featuresPropertyId(feature?: maplibregl.MapGeoJSONFeature) {
  const propertyId = feature?.properties?.propertyId
  return propertyId === undefined ? undefined : Number(propertyId)
}
