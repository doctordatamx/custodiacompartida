import { useEffect, useRef, useState } from 'react'
import * as maplibregl from 'maplibre-gl'
import type { FeatureCollection, MultiPolygon, Polygon } from 'geojson'
import 'maplibre-gl/dist/maplibre-gl.css'
import workerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url'

maplibregl.setWorkerUrl(new URL(workerUrl, document.baseURI).href)

type Annual = { total: number | null; share: number | null; both: number | null; eligible: number | null; matched: boolean }
type Municipality = Annual & {
  code: string; name: string; comparable: boolean; otherYear: Annual | null
  totalChange: number | null; shareChange: number | null
}
type MunicipalMap = FeatureCollection<Polygon | MultiPolygon, Municipality>
type Metric = 'total' | 'share' | 'totalChange' | 'shareChange'
const colors = ['#dcefe7', '#a9d6c8', '#68b0a0', '#288979', '#145d53']
const changeColors = ['#9a4b2b', '#e9a47e', '#f4efe4', '#80bbae', '#145d53']
const breaks = { total: [1, 25, 100, 500], share: [10, 20, 30, 40],
  totalChange: [-24, 0, 1, 25], shareChange: [-4.9, 0, 0.1, 5] }
const labels = {
  total: ['0', '1–24', '25–99', '100–499', '500 o más'],
  share: ['<10%', '10–19.9%', '20–29.9%', '30–39.9%', '40% o más'],
  totalChange: ['−25 o menos', '−24 a −1', '0', '+1 a +24', '+25 o más'],
  shareChange: ['−5 pp o menos', '−4.9 a −0.1 pp', '0 pp', '+0.1 a +4.9 pp', '+5 pp o más'],
}
const number = new Intl.NumberFormat('es-MX', { maximumFractionDigits: 1 })

function bounds(data: MunicipalMap): maplibregl.LngLatBoundsLike {
  const bounds = new maplibregl.LngLatBounds()
  for (const { geometry } of data.features) {
    const polygons = geometry.type === 'Polygon' ? [geometry.coordinates] : geometry.coordinates
    for (const polygon of polygons) {
      for (const [longitude, latitude] of polygon[0]) bounds.extend([longitude, latitude])
    }
  }
  return bounds
}

function fillColor(metric: Metric): maplibregl.ExpressionSpecification {
  const [a, b, c, d] = breaks[metric]
  const palette = metric.endsWith('Change') ? changeColors : colors
  return ['case', ['==', ['get', metric], null], '#d4d9d7',
    ['step', ['number', ['get', metric], 0], palette[0], a, palette[1], b, palette[2], c, palette[3], d, palette[4]]]
}

function Map({ data, metric, selected, onSelect }: {
  data: MunicipalMap; metric: Metric; selected: string; onSelect: (code: string) => void
}) {
  const element = useRef<HTMLDivElement>(null)
  const [ready, setReady] = useState<maplibregl.Map | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    let map: maplibregl.Map
    try {
      map = new maplibregl.Map({
        container: element.current!,
        bounds: bounds(data), fitBoundsOptions: { padding: 22 },
        scrollZoom: false, attributionControl: false,
        style: {
          version: 8,
          sources: { municipalities: { type: 'geojson', data } },
          layers: [
            { id: 'background', type: 'background', paint: { 'background-color': '#f1f5f3' } },
            { id: 'municipalities', type: 'fill', source: 'municipalities', paint: { 'fill-color': '#d4d9d7' } },
            { id: 'borders', type: 'line', source: 'municipalities', paint: { 'line-color': '#fff', 'line-width': 1 } },
            { id: 'selected', type: 'line', source: 'municipalities', filter: ['==', ['get', 'code'], ''],
              paint: { 'line-color': '#70470e', 'line-width': 3 } },
          ],
        },
      })
    } catch {
      setFailed(true)
      return
    }
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }))
    map.on('load', () => setReady(map))
    map.on('click', 'municipalities', event => {
      const code = event.features?.[0]?.properties.code
      if (typeof code === 'string') onSelect(code)
    })
    map.on('mouseenter', 'municipalities', () => { map.getCanvas().style.cursor = 'pointer' })
    map.on('mouseleave', 'municipalities', () => { map.getCanvas().style.cursor = '' })
    const observer = new ResizeObserver(() => map.resize())
    observer.observe(element.current!)
    return () => { observer.disconnect(); map.remove() }
  }, [data, onSelect])
  useEffect(() => {
    if (ready) {
      ready.setPaintProperty('municipalities', 'fill-color', fillColor(metric))
      ready.setFilter('selected', ['==', ['get', 'code'], selected])
    }
  }, [ready, metric, selected])
  return <><div className="atlas-map" ref={element} aria-label="Mapa interactivo de municipios" />
    {failed && <p role="status">El mapa requiere WebGL. Puedes consultar los datos con el selector de municipios.</p>}</>
}

export default function MunicipalAtlas({ state, year }: { state: string; year: string }) {
  const [data, setData] = useState<MunicipalMap | null>(null)
  const [failed, setFailed] = useState(false)
  const [metric, setMetric] = useState<Metric>('total')
  const [selected, setSelected] = useState('')
  useEffect(() => {
    const controller = new AbortController()
    fetch(`${import.meta.env.BASE_URL}atlas/${year === '2024' ? '2024/' : ''}${state}.geojson`, { signal: controller.signal }).then(response => {
      if (!response.ok) throw new Error(String(response.status))
      return response.json()
    }).then(setData).catch(() => { if (!controller.signal.aborted) setFailed(true) })
    return () => controller.abort()
  }, [state, year])
  if (!data) return <p role="status">{failed ? 'No se pudo cargar la cartografía. Recarga la página para reintentar.' : 'Cargando municipios…'}</p>
  const municipalities = data.features.map(feature => feature.properties)
    .sort((a, b) => a.name.localeCompare(b.name, 'es-MX'))
  const municipality = municipalities.find(item => item.code === selected)
  const comparing = metric.endsWith('Change')
  const palette = comparing ? changeColors : colors
  const annualRows = year === '2024'
    ? [municipality, municipality?.otherYear] : [municipality?.otherYear, municipality]
  const delta = municipality?.[metric]
  const signed = new Intl.NumberFormat('es-MX', { maximumFractionDigits: 1, signDisplay: 'exceptZero' })

  return <>
    <div className="atlas-controls">
      <label>Indicador<select value={metric} onChange={e => setMetric(e.target.value as Metric)}>
        <option value="total">Divorcios registrados</option><option value="share">Custodia asignada a ambas personas</option>
        <option value="totalChange">Cambio en divorcios · 2025 frente a 2024</option>
        <option value="shareChange">Cambio en custodia para ambas personas · 2025 frente a 2024</option>
      </select></label>
      <label>Municipio o demarcación<select value={selected} onChange={e => setSelected(e.target.value)}>
        <option value="">Selecciona un municipio</option>
        {municipalities.map(item => <option key={item.code} value={item.code}>{item.name}</option>)}
      </select></label>
    </div>
    <Map data={data} metric={metric} selected={selected} onSelect={setSelected} />
    <ul className="atlas-legend" aria-label="Leyenda">
      {labels[metric].map((label, i) => <li key={label}><i style={{ background: palette[i] }} />{label}</li>)}
      <li><i style={{ background: '#d4d9d7' }} />{comparing ? 'Dato reservado o geometría diferente' : 'Dato reservado o sin correspondencia'}</li>
    </ul>
    {municipality && <div aria-live="polite">
      <p className="atlas-selection"><strong>{municipality.name}</strong> · {municipality.code}
        {comparing && delta != null && ` · Cambio de ${signed.format(delta)}${metric === 'shareChange' ? ' pp' : ' divorcios'}`}
      </p>
      {comparing && !municipality.comparable && <p>La geometría difiere entre las capas simplificadas. Se reserva la diferencia.</p>}
      {comparing && municipality.comparable && delta == null && <p>La diferencia requiere cifras disponibles en ambos años.</p>}
      <div className="table-scroll"><table>
        <thead><tr><th scope="col">Año</th><th scope="col">Divorcios registrados</th>
          <th scope="col">Custodia para ambas personas</th><th scope="col">Casos / base de cálculo</th></tr></thead>
        <tbody>{(comparing ? annualRows : [municipality]).map((row, index) => <tr key={index}>
          <th scope="row">{comparing ? 2024 + index : year}</th>
          <td>{row?.total == null ? '—' : number.format(row.total)}</td>
          <td>{row?.share == null ? '—' : `${number.format(row.share)}%`}</td>
          <td>{row?.both == null || row.eligible == null ? '—' : `${number.format(row.both)} / ${number.format(row.eligible)}`}</td>
        </tr>)}</tbody>
      </table></div>
    </div>}
    <p className="note">El guion indica una cifra reservada o sin correspondencia. Los porcentajes usan los divorcios judiciales con menores registrados en cada municipio. Se reservan los conteos pequeños y los porcentajes con menos de cinco casos en la categoría o en su complemento.</p>
  </>
}
