import { lazy, Suspense, useEffect, useRef, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { init, use, type ComposeOption } from 'echarts/core'
import { BarChart, LineChart, type BarSeriesOption, type LineSeriesOption } from 'echarts/charts'
import {
  GridComponent, TooltipComponent, LegendComponent, AriaComponent,
  type GridComponentOption, type TooltipComponentOption, type LegendComponentOption, type AriaComponentOption,
} from 'echarts/components'
import { CanvasRenderer } from 'echarts/renderers'
import './style.css'

const MunicipalAtlas = lazy(() => import('./MunicipalAtlas'))

use([BarChart, LineChart, GridComponent, TooltipComponent, LegendComponent, AriaComponent, CanvasRenderer])

type ChartOption = ComposeOption<BarSeriesOption | LineSeriesOption | GridComponentOption |
  TooltipComponentOption | LegendComponentOption | AriaComponentOption>
type ChildrenSummary = { cases: number; children: number; unknown: number; noAwardUnknown?: number; custody: Record<string, number> }
type StateRow = [number, number, Record<string, number> | null, ChildrenSummary?]
type Dataset = Record<string, Record<string, StateRow>>

const states = [
  'Aguascalientes', 'Baja California', 'Baja California Sur', 'Campeche', 'Coahuila',
  'Colima', 'Chiapas', 'Chihuahua', 'Ciudad de México', 'Durango', 'Guanajuato',
  'Guerrero', 'Hidalgo', 'Jalisco', 'México', 'Michoacán', 'Morelos', 'Nayarit',
  'Nuevo León', 'Oaxaca', 'Puebla', 'Querétaro', 'Quintana Roo', 'San Luis Potosí',
  'Sinaloa', 'Sonora', 'Tabasco', 'Tamaulipas', 'Tlaxcala', 'Veracruz', 'Yucatán', 'Zacatecas',
]
const code = (index: number) => String(index + 1).padStart(2, '0')
const number = new Intl.NumberFormat('es-MX')
const percent = new Intl.NumberFormat('es-MX', { style: 'percent', maximumFractionDigits: 1 })
const sum = ([judicial, administrative]: StateRow) => judicial + administrative
const colors = ['#087f72', '#87c0b3', '#ad7b34']
const categories: Record<string, string> = {
  '3': 'Ambas personas', mujer: 'Una mujer', hombre: 'Un hombre',
  '0': 'No se otorgó', '4': 'Otra persona', '98': 'No aplica',
  '99': 'No especificada', sexo_desconocido: 'Persona con sexo sin especificar',
}
const categoryOrder = ['3', 'mujer', 'hombre', '4', '0', '98', '99', 'sexo_desconocido']

function totals(rows: Record<string, StateRow>, state: string): StateRow {
  if (state) return rows[state]
  const result: StateRow = [0, 0, Object.values(rows)[0][2] === null ? null : {}]
  if (Object.values(rows)[0][3]) result[3] = { cases: 0, children: 0, unknown: 0, noAwardUnknown: 0, custody: {} }
  for (const [judicial, administrative, custody, children] of Object.values(rows)) {
    result[0] += judicial
    result[1] += administrative
    if (children && result[3]) {
      result[3].cases += children.cases
      result[3].children += children.children
      result[3].unknown += children.unknown
      const unknownNoAward = result[3].noAwardUnknown
      result[3].noAwardUnknown = unknownNoAward === undefined || children.noAwardUnknown === undefined
        ? undefined : unknownNoAward + children.noAwardUnknown
      for (const [key, count] of Object.entries(children.custody)) {
        result[3].custody[key] = (result[3].custody[key] ?? 0) + count
      }
    }
    if (custody && result[2]) {
      for (const [key, count] of Object.entries(custody)) result[2][key] = (result[2][key] ?? 0) + count
    }
  }
  return result
}

function Chart({ options, label }: { options: ChartOption; label: string }) {
  const element = useRef<HTMLDivElement>(null)
  const chart = useRef<ReturnType<typeof init> | null>(null)
  useEffect(() => {
    const container = element.current!
    const instance = init(container)
    chart.current = instance
    const observer = new ResizeObserver(() => instance.resize())
    observer.observe(container)
    return () => { observer.disconnect(); instance.dispose() }
  }, [])
  useEffect(() => { chart.current?.setOption(options, true) }, [options])
  return <div className="chart" ref={element} role="img" aria-label={label} />
}

function ChildrenExplorer({ year, location, state, local, national, onFirstYear }: {
  year: string; location: string; state: string; local?: ChildrenSummary;
  national?: ChildrenSummary; onFirstYear: () => void
}) {
  const scopes = local && national
    ? state ? [[location, local], ['Nacional', national]] as const : [['Nacional', national]] as const
    : []
  const keys = categoryOrder.filter(key => scopes.some(([, row]) => row.custody[key]))
  const share = (count: number, cases: number) => cases ? percent.format(count / cases) : '—'

  function downloadCsv() {
    const csv = [
      ['anio', 'ambito', 'divorcios_con_menores', 'menores_registrados', 'divorcios_con_numero_de_menores_sin_dato_utilizable', 'custodia', 'registros', 'porcentaje'],
      ...scopes.flatMap(([name, row]) => keys.map(key => {
        const count = row.custody[key] ?? 0
        return [year, name, row.cases, row.children, row.unknown, categories[key], count,
          row.cases ? (100 * count / row.cases).toFixed(4) : '']
      })),
    ].map(row => row.join(',')).join('\r\n')
    const url = URL.createObjectURL(new Blob(['\uFEFF', csv], { type: 'text/csv;charset=utf-8' }))
    const link = document.createElement('a')
    link.href = url
    link.download = `divorcios-con-menores-${year}-${state || 'nacional'}.csv`
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  }

  return <section id="menores" className="section">
    <div className="section-head"><div><span className="kicker">04 / HIJAS E HIJOS</span><h2>Divorcios con menores</h2></div>
      <span className="pill">{location} · {year}</span></div>
    <article className="panel">
      <div className="panel-head"><div><h3>Custodia en divorcios judiciales con menores</h3>
        <p>Base de cálculo por ámbito: divorcios judiciales con al menos un menor registrado.</p></div>
        {keys.length > 0 && <button className="csv-button" onClick={downloadCsv}>Descargar CSV</button>}
      </div>
      {scopes.length ? <>
        <div className="table-scroll"><table>
          <thead><tr><th scope="col">Ámbito</th><th scope="col">Divorcios con menores</th><th scope="col">Menores registrados</th><th scope="col">Divorcios sin dato utilizable de menores</th></tr></thead>
          <tbody>{scopes.map(([name, row]) => <tr key={name}><th scope="row">{name}</th>
            <td>{number.format(row.cases)}</td><td>{number.format(row.children)}</td><td>{number.format(row.unknown)}</td>
          </tr>)}</tbody>
        </table></div>
        {keys.length ? <div className="table-scroll"><table>
          <thead><tr><th scope="col">Asignación registrada</th>
            {scopes.map(([name]) => <th scope="col" key={name}>{name} · casos y %</th>)}</tr></thead>
          <tbody>{keys.map(key => <tr key={key}><th scope="row">{categories[key]}</th>
            {scopes.map(([name, row]) => <td key={name}>{number.format(row.custody[key] ?? 0)} · {share(row.custody[key] ?? 0, row.cases)}</td>)}
          </tr>)}</tbody>
        </table></div> : <p>No hay divorcios judiciales con menores registrados para esta selección.</p>}
        <p className="note">Los divorcios sin dato utilizable sobre el número de menores quedan fuera del cálculo. Los casos con custodia no especificada permanecen en el denominador.</p>
      </> : <p className="empty">El explorador cubre 2014–2025. <button onClick={onFirstYear}>Ir a 2014</button></p>}
    </article>
  </section>
}

function CustodyProfiles({ state, onState }: { state: string; onState: (state: string) => void }) {
  const [profiles, setProfiles] = useState<Record<string, [number, number, number]> | null>(null)
  const [failed, setFailed] = useState(false)
  const [period, setPeriod] = useState('1')
  const [age, setAge] = useState('1')
  const [duration, setDuration] = useState('2')
  const [residence, setResidence] = useState('')
  const [comparisonState, setComparisonState] = useState<string | null>(null)
  useEffect(() => {
    const controller = new AbortController()
    fetch(`${import.meta.env.BASE_URL}perfiles-custodia.json`, { signal: controller.signal })
      .then(response => {
        if (!response.ok) throw new Error(String(response.status))
        return response.json()
      })
      .then(setProfiles)
      .catch(() => { if (!controller.signal.aborted) setFailed(true) })
    return () => controller.abort()
  }, [])

  const comparing = comparisonState !== null
  const groups = (comparing ? [state, comparisonState] : [state]).map(key => {
    const residenceKey = residence ? ':' + residence : ''
    const counts = profiles?.[`${period}:${key || '00'}:${age}:${duration}${residenceKey}`]
    return {
      name: key ? states[Number(key) - 1] : 'Nacional',
      counts,
      total: counts?.reduce((sum, count) => sum + count, 0) ?? 0,
    }
  })
  const [first, second] = groups
  const labels = ['Ambas personas', 'Un hombre', 'Una mujer']
  const difference = new Intl.NumberFormat('es-MX', { maximumFractionDigits: 1, signDisplay: 'exceptZero' })

  return <section id="perfiles" className="section">
    <div className="section-head"><div><span className="kicker">06 / PERFILES</span><h2>Perfiles históricos de custodia</h2></div>
      <span className="pill">2018–2025</span></div>
    <article className="panel">
      <h3>Asignaciones observadas en divorcios comparables</h3>
      <p>Divorcios judiciales con menores, entre un hombre y una mujer, con datos completos para los filtros.</p>
      <div className="atlas-controls">
        <label>Periodo del perfil<select value={period} onChange={e => setPeriod(e.target.value)}>
          <option value="1">2023–2025</option><option value="0">2018–2022</option>
        </select></label>
        <label>{comparing ? "Grupo A" : "Lugar de registro"}<select value={state} onChange={e => onState(e.target.value)}>
          <option value="">Nacional</option>
          {states.map((name, index) => <option value={code(index)} key={name}>{name}</option>)}
        </select></label>
        {comparing && <label>Grupo B<select value={comparisonState} onChange={e => setComparisonState(e.target.value)}>
          <option value="">Nacional</option>
          {states.map((name, index) => <option value={code(index)} key={name}>{name}</option>)}
        </select></label>}
        <label>Edad aproximada de la persona más joven<select value={age} onChange={e => setAge(e.target.value)}>
          <option value="0">Menos de 30 años</option><option value="1">30 a 39 años</option><option value="2">40 años o más</option>
        </select></label>
        <label>Años de matrimonio al registrar la demanda<select value={duration} onChange={e => setDuration(e.target.value)}>
          <option value="0">Menos de 5 años</option><option value="1">5 a 9 años</option><option value="2">10 años o más</option>
        </select></label>
        <label>Residencia habitual de la pareja<select value={residence} onChange={e => setResidence(e.target.value)}>
          <option value="">Todas las residencias</option>
          <option value="mismo">Mismo municipio o demarcación</option>
          <option value="otro-municipio">Distinto municipio del mismo estado</option>
          <option value="otro-estado">Distinto estado</option>
          <option value="sin-dato">Sin par de municipios válido en México</option>
        </select></label>
      </div>
      <button className="csv-button" onClick={() => setComparisonState(comparing ? null : state ? '' : '19')}>
        {comparing ? 'Quitar grupo' : 'Agregar grupo'}
      </button>
      <div aria-live="polite">
        {!profiles ? <p className="empty">{failed ? 'No se pudieron cargar los perfiles. Recarga la página para reintentar.'
          : 'Cargando perfiles históricos…'}</p> : second ? <>
          <div className="table-scroll"><table>
            <thead><tr><th scope="col">Asignación registrada</th>
              <th scope="col">A · {first.name}</th>
              <th scope="col">B · {second.name}</th><th scope="col">Diferencia A − B</th>
            </tr></thead>
            <tbody>
              <tr><th scope="row">Divorcios en el perfil</th>
                {groups.map((group, index) => <td key={index}>{group.counts ? number.format(group.total) : 'No disponible'}</td>)}
                <td>—</td>
              </tr>
              {labels.map((label, index) => {
                const delta = first.counts && second.counts
                  ? 100 * (first.counts[index] / first.total - second.counts[index] / second.total)
                  : null
                return <tr key={label}><th scope="row">{label}</th>
                  {groups.map((group, groupIndex) => <td key={groupIndex}>{group.counts
                    ? `${number.format(group.counts[index])} · ${percent.format(group.counts[index] / group.total)}`
                    : '—'}</td>)}
                  <td>{delta === null ? '—' : `${difference.format(delta)} pp`}</td>
                </tr>
              })}
            </tbody>
          </table></div>
          {groups.some(group => !group.counts) && <p className="empty">Algún grupo tiene pocos casos o está reservado. La diferencia requiere datos de ambos grupos.</p>}
        </> : first.counts ? <>
          <p><strong>{number.format(first.total)} divorcios</strong> con asignación a una o ambas personas divorciantes.</p>
          <div className="custody-list">{first.counts.map((count, index) => <div className="custody-row" key={labels[index]}>
            <span>{labels[index]}</span>
            <div className="bar-track" aria-hidden="true"><i style={{ width: `${100 * count / first.total}%` }} /></div>
            <strong>{number.format(count)}</strong><span>{percent.format(count / first.total)}</span>
          </div>)}</div>
        </> : <p className="empty">Este perfil tiene pocos casos o está reservado.</p>}
      </div>
      <p className="note">Los porcentajes usan el total de cada grupo.{comparing && " Las diferencias se expresan en puntos porcentuales (pp). El total nacional incluye a la entidad comparada."} Se requieren al menos 100 divorcios por perfil y 10 en cada categoría. La edad y los años de matrimonio se aproximan mediante diferencias entre años calendario.</p>
    </article>
  </section>
}

function Dashboard({ data }: { data: Dataset }) {
  const years = Object.keys(data).sort()
  const [year, setYear] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('anio')
    return requested && Object.hasOwn(data, requested) ? requested : years.at(-1)!
  })
  const [state, setState] = useState(() => {
    const requested = new URLSearchParams(window.location.search).get('entidad')
    return requested && Object.hasOwn(data[year], requested) ? requested : ''
  })
  useEffect(() => {
    const url = new URL(window.location.href)
    url.searchParams.set('anio', year)
    if (state) url.searchParams.set('entidad', state)
    else url.searchParams.delete('entidad')
    window.history.replaceState(null, '', url)
  }, [year, state])
  const [metric, setMetric] = useState<'total' | 'tramite'>('total')
  const [onlyWithMinors, setOnlyWithMinors] = useState(false)
  const location = state ? states[Number(state) - 1] : 'México'
  const current = totals(data[year], state)
  const [judicial, administrative, custody] = current
  const total = sum(current)
  const trend = years.map(y => totals(data[y], state))
  const ranking = states.map((name, index) => ({ name, id: code(index), row: data[year][code(index)] }))
    .sort((a, b) => sum(b.row) - sum(a.row))
  const peak = sum(ranking[0].row)
  const children = current[3]
  const custodyCounts = onlyWithMinors ? children?.custody : custody
  const custodyBase = onlyWithMinors ? children?.cases ?? 0 : judicial
  const known = categoryOrder.filter(key => (custodyCounts?.[key] ?? 0) > 0 || (onlyWithMinors && key === '0'))
  const noAward = custody?.['0'] ?? 0
  const noAwardWithMinors = children?.custody['0'] ?? 0
  const noAwardUnknown = children?.noAwardUnknown
  const prior = data[String(Number(year) - 1)]
  const change = prior ? total / sum(totals(prior, state)) - 1 : null
  const series = metric === 'total'
    ? [{ name: 'Divorcios registrados', values: trend.map(sum) }]
    : [{ name: 'Judiciales', values: trend.map(row => row[0]) },
       { name: 'Administrativos', values: trend.map(row => row[1]) }]
  const options: ChartOption = {
    color: colors,
    aria: { enabled: true },
    grid: { left: 63, right: 20, top: 20, bottom: 56 },
    legend: { bottom: 0 },
    tooltip: { trigger: 'axis', valueFormatter: value => number.format(Number(value)) },
    xAxis: { type: 'category', data: years, boundaryGap: false, axisLabel: { hideOverlap: true } },
    yAxis: { type: 'value', min: 0, axisLabel: { formatter: value => number.format(Number(value)) },
      splitLine: { lineStyle: { color: '#e7eeeb' } } },
    series: series.map(({ name, values }) => ({
      type: 'line', name, data: values.map((value, i) => years[i] === year
        ? { value, symbol: 'circle', symbolSize: 9, itemStyle: { color: '#bd8e46' } }
        : value),
      symbol: 'none', lineStyle: { width: 3 }, emphasis: { focus: 'series' },
    })),
  }

  return <>
    <header className="top"><div className="top-inner">
      <a href="#inicio" className="brand"><span className="brand-icon" aria-hidden="true">▥</span> Observatorio <strong>Divorcios MX</strong></a>
      <nav aria-label="Secciones"><a href="#panorama">Panorama</a><a href="#entidades">Entidades</a><a href="#custodia">Custodia</a><a href="#menores">Menores</a><a href="#atlas">Mapa</a><a href="#perfiles">Perfiles</a><a href="#contacto">Contacto</a></nav>
    </div></header>
    <section className="hero" id="inicio"><div className="wrap hero-inner">
      <div className="eyebrow"><span className="dot" /> DATOS, FAMILIAS Y JUSTICIA</div>
      <h1>Divorcios y custodia<br />en México</h1>
      <p>Explora cuatro décadas de divorcios registrados y conoce a quién se asignó la custodia en los divorcios judiciales.</p>
      <div className="hero-meta"><span>FUENTE OFICIAL · INEGI</span><span>1985–2025</span><span>32 ENTIDADES</span></div>
    </div></section>
    <main className="wrap">
      <div className="filters" aria-label="Filtros del tablero">
        <div><span className="kicker">EXPLORA LOS DATOS</span><p>Selecciona el año y el lugar de registro.</p></div>
        <div className="filter-fields">
          <label>Año de referencia<select value={year} onChange={e => setYear(e.target.value)}>
            {[...years].reverse().map(y => <option key={y}>{y}</option>)}
          </select></label>
          <label>Entidad de registro<select value={state} onChange={e => setState(e.target.value)}>
            <option value="">Nacional</option>{states.map((name, i) => <option value={code(i)} key={name}>{name}</option>)}
          </select></label>
        </div>
      </div>
      <section id="panorama" className="section">
        <div className="section-head"><div><span className="kicker">01 / PANORAMA</span><h2>Divorcios registrados</h2></div><span className="pill" aria-live="polite">{location} · {year}</span></div>
        <div className="stats">
          <article className="stat primary"><span>Total registrado</span><strong>{number.format(total)}</strong><small>{change === null ? 'Primer año de la serie' : `${change > 0 ? '+' : ''}${percent.format(change)} respecto de ${Number(year) - 1}`}</small></article>
          <article className="stat"><span>Judiciales</span><strong>{number.format(judicial)}</strong><small>{percent.format(judicial / total)} del total</small></article>
          <article className="stat"><span>Administrativos</span><strong>{number.format(administrative)}</strong><small>{percent.format(administrative / total)} del total</small></article>
        </div>
        <article className="panel">
          <div className="panel-head"><div><h3>Evolución anual</h3><p>{location} · 1985–2025 · Número de registros</p></div>
            <div className="toggle" aria-label="Serie de evolución">
              <button aria-pressed={metric === 'total'} onClick={() => setMetric('total')}>Total</button>
              <button aria-pressed={metric === 'tramite'} onClick={() => setMetric('tramite')}>Por trámite</button>
            </div>
          </div>
          <Chart options={options} label={`Serie anual de divorcios registrados en ${location}`} />
          <p className="note">INEGI cambió el proceso de captación en 1993 para reducir la duplicación entre fuentes.</p>
          <details><summary>Ver datos de la serie</summary><div className="table-scroll"><table>
            <thead><tr><th scope="col">Año</th><th scope="col">Total</th><th scope="col">Judiciales</th><th scope="col">Administrativos</th></tr></thead>
            <tbody>{years.map((y, i) => <tr key={y}><th scope="row">{y}</th><td>{number.format(sum(trend[i]))}</td><td>{number.format(trend[i][0])}</td><td>{number.format(trend[i][1])}</td></tr>)}</tbody>
          </table></div></details>
        </article>
      </section>
      <section id="entidades" className="section">
        <div className="section-head"><div><span className="kicker">02 / TERRITORIO</span><h2>Comparación por entidad</h2></div><span className="pill">{year}</span></div>
        <article className="panel">
          <h3>Divorcios por entidad de registro</h3><p>Ordenados por volumen. Selecciona una entidad para explorar su serie.</p>
          <div className="table-scroll rank"><table>
            <thead><tr><th scope="col">Entidad</th><th scope="col">Total</th><th scope="col">Judiciales</th><th scope="col">Administrativos</th></tr></thead>
            <tbody>{ranking.map(({ name, id, row }) => <tr key={id} className={state === id ? 'selected' : ''}>
              <th scope="row"><button className="state-button" aria-pressed={state === id} onClick={() => setState(id)}>{name}</button><div className="bar-track" aria-hidden="true"><i style={{ width: `${100 * sum(row) / peak}%` }} /></div></th>
              <td>{number.format(sum(row))}</td><td>{number.format(row[0])}</td><td>{number.format(row[1])}</td>
            </tr>)}</tbody>
          </table></div>
        </article>
      </section>
      <section id="custodia" className="section">
        <div className="section-head"><div><span className="kicker">03 / CUSTODIA</span><h2>Asignación registrada</h2></div><span className="pill">{location} · {year}</span></div>
        <article className="panel">
          <h3>Custodia en divorcios judiciales</h3>
          {custody ? <>
            <div className="atlas-controls"><label>Universo de custodia
              <select value={onlyWithMinors ? 'minors' : 'all'} onChange={e => setOnlyWithMinors(e.target.value === 'minors')}>
                <option value="all">Todos los divorcios judiciales</option>
                <option value="minors" disabled={!children}>Solo divorcios judiciales con hijos menores registrados</option>
              </select>
            </label></div>
            <div aria-live="polite">
              <p>Base de cálculo de {number.format(custodyBase)} divorcios judiciales {onlyWithMinors ? 'con hijos menores registrados' : 'registrados'}.</p>
              {custodyBase > 0 && custodyCounts ? <div className="custody-list">{known.map(key => {
                const count = custodyCounts[key] ?? 0
                return <div className="custody-row" key={key}>
                  <span>{categories[key] ?? `Código ${key}`}</span><div className="bar-track" aria-hidden="true"><i style={{ width: `${100 * count / custodyBase}%` }} /></div>
                  <strong>{number.format(count)}</strong><span>{percent.format(count / custodyBase)}</span>
                </div>
              })}</div> : <p className="empty">No hay registros para este universo.</p>}
              {!onlyWithMinors && noAward > 0 && noAwardUnknown !== undefined && <p className="note">
                De los {number.format(noAward)} casos en «No se otorgó», {number.format(noAward - noAwardWithMinors - noAwardUnknown)} registraron cero hijos menores, {number.format(noAwardWithMinors)} registraron hijos menores y {number.format(noAwardUnknown)} carecían de un dato utilizable sobre el número de menores.
              </p>}
            </div>
            <p className="note">«Ambas personas» identifica la categoría del registro. Las categorías «Una mujer» y «Un hombre» usan el sexo registrado de la persona a quien se asignó la custodia.</p>
          </> : <p className="empty">Esta vista usa la codificación disponible desde 2014. <button onClick={() => setYear('2014')}>Ir a 2014</button></p>}
        </article>
      </section>
      <ChildrenExplorer year={year} location={location} state={state} local={current[3]}
        national={state ? totals(data[year], '')[3] : current[3]} onFirstYear={() => setYear('2014')} />
      <section id="atlas" className="section">
        <div className="section-head"><div><span className="kicker">05 / ATLAS</span><h2>Mapa municipal</h2></div>
          <span className="pill">2024–2025</span></div>
        <article className="panel">
          <h3>Divorcios por municipio de registro</h3>
          <p>Estadística de Divorcios y Marco Geoestadístico 2024 y 2025 del INEGI.</p>
          <div className="atlas-controls">
            <label>Año del mapa<select value={year === '2024' || year === '2025' ? year : ''} onChange={e => setYear(e.target.value)}>
              {year !== '2024' && year !== '2025' && <option value="" disabled>Selecciona un año</option>}
              <option value="2025">2025</option><option value="2024">2024</option>
            </select></label>
            <label>Entidad del mapa<select value={state} onChange={e => setState(e.target.value)}>
              <option value="">Selecciona una entidad</option>
              {states.map((name, i) => <option value={code(i)} key={name}>{name}</option>)}
            </select></label>
          </div>
          {year !== '2024' && year !== '2025' ? <p className="empty">Selecciona 2024 o 2025 para consultar el mapa.</p>
            : state ? <Suspense fallback={<p role="status">Cargando mapa…</p>}><MunicipalAtlas key={year + state} state={state} year={year} /></Suspense>
              : <p className="empty">Selecciona una entidad para consultar sus municipios.</p>}
          <p><a href="https://www.inegi.org.mx/programas/mg/">Marco Geoestadístico del INEGI</a></p>
        </article>
      </section>
      <CustodyProfiles state={state} onState={setState} />
      <section id="contacto" className="section" aria-labelledby="contacto-titulo">
        <span className="kicker">07 / CONTACTO</span>
        <h2 id="contacto-titulo">Contacto</h2>
        <div className="panel contact-panel">
          <div>
            <h3>Sobre el observatorio</h3>
            <p>El Observatorio de Divorcios y Custodia en México reúne datos del INEGI para explorar cómo han cambiado los divorcios registrados y la asignación de custodia en el país.</p>
            <p>Para preguntas, comentarios o propuestas de colaboración, escribe a <a href="mailto:doctordata670@gmail.com">doctordata670@gmail.com</a>.</p>
          </div>
          <div>
            <h3>Apoya el proyecto</h3>
            <p>Si el observatorio te resulta útil, puedes apoyar su mantenimiento y futuras actualizaciones con una aportación voluntaria en Ko-fi.</p>
            <iframe
              className="kofi-widget"
              src={`${import.meta.env.BASE_URL}ko-fi.html`}
              title="Apoyar en Ko-fi"
              loading="lazy"
              sandbox="allow-scripts allow-popups allow-popups-to-escape-sandbox"
            />
          </div>
        </div>
      </section>
    </main>
    <footer><div className="wrap foot"><strong>Observatorio de Divorcios y Custodia en México</strong><a href="https://www.inegi.org.mx/programas/ed/#datos_abiertos">Estadística de Divorcios · INEGI ↗</a></div></footer>
  </>
}

function App() {
  const [data, setData] = useState<Dataset | null>(null)
  const [failed, setFailed] = useState(false)
  useEffect(() => {
    fetch(`${import.meta.env.BASE_URL}indicadores.json`).then(response => {
      if (!response.ok) throw new Error(String(response.status))
      return response.json()
    }).then(setData).catch(() => setFailed(true))
  }, [])
  if (!data) return <main className="wrap"><p role="status">{failed ? 'No se pudieron cargar los datos. Vuelve a cargar la página.' : 'Cargando indicadores del INEGI…'}</p></main>
  return <Dashboard data={data} />
}

createRoot(document.getElementById('root')!).render(<App />)
