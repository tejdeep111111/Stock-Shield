import { useEffect, useMemo, useState } from 'react'
import './App.css'

type Summary = {
  products_at_risk: number
  expected_lost_revenue: number
  revenue_protected: number
  critical_supplier_risks: number
  average_days_to_stockout: number
  last_analysis_timestamp: string
}

type Risk = {
  product_id: number
  product_name: string
  region_id: number
  region_name: string
  current_inventory: number
  daily_demand: number
  stockout_date: string | null
  days_to_stockout: number | null
  stockout_probability: number
  risk_level: 'Critical' | 'High' | 'Medium' | 'Low'
  expected_lost_revenue: number
  recommended_action: string
}

type Disruption = {
  id: number
  type: 'demand_shock' | 'supplier_delay'
  name: string
  active: boolean
  product_id?: number
  supplier_id?: number
  region_id?: number
  severity: number
  demand_multiplier: number
  delay_days: number
  start_date: string
  duration_days: number
}

type Strategy = {
  strategy: string
  success_probability: number
  arrival_days: number
  units_recovered: number
  revenue_protected: number
  cost: number
  net_value: number
}

type RecoveryResponse = {
  run_id: string
  strategies: Strategy[]
  recommendation: {
    recommended_action: string
    expected_revenue_protected: number
    intervention_cost: number
    net_value: number
    confidence: number
    reasoning: string[]
  }
  explanations: string[]
}

const API_BASE = import.meta.env.VITE_API_BASE ?? 'http://localhost:8000'

function App() {
  const [summary, setSummary] = useState<Summary | null>(null)
  const [risks, setRisks] = useState<Risk[]>([])
  const [disruptions, setDisruptions] = useState<Disruption[]>([])
  const [recovery, setRecovery] = useState<RecoveryResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [shockProductId, setShockProductId] = useState(1)
  const [shockRegionId, setShockRegionId] = useState(1)
  const [shockMultiplier, setShockMultiplier] = useState(1.5)
  const [delaySupplierId, setDelaySupplierId] = useState(1)
  const [delayProductId, setDelayProductId] = useState(1)
  const [delayDays, setDelayDays] = useState(10)

  const riskBadgeClass = (level: Risk['risk_level']) => `badge badge-${level.toLowerCase()}`

  const regionalShift = useMemo(() => {
    const byRegion = new Map<string, number[]>()
    risks.forEach((risk) => {
      const values = byRegion.get(risk.region_name) ?? []
      values.push(risk.stockout_probability)
      byRegion.set(risk.region_name, values)
    })
    return Array.from(byRegion.entries()).map(([region, values]) => {
      const avg = values.reduce((a, b) => a + b, 0) / Math.max(values.length, 1)
      return { region, avg }
    })
  }, [risks])

  const loadDashboard = async () => {
    try {
      setLoading(true)
      setError(null)
      const [summaryRes, riskRes, disruptionRes, recoveryRes] = await Promise.all([
        fetch(`${API_BASE}/api/dashboard/summary`),
        fetch(`${API_BASE}/api/dashboard/risk-matrix`),
        fetch(`${API_BASE}/api/disruptions`),
        fetch(`${API_BASE}/api/recovery/run`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ scenario_id: 'frontend-load', budget: 10000 }),
        }),
      ])
      if (!summaryRes.ok || !riskRes.ok || !disruptionRes.ok || !recoveryRes.ok) {
        throw new Error('Failed to load dashboard')
      }
      setSummary(await summaryRes.json())
      const riskJson = await riskRes.json()
      setRisks(riskJson.risks)
      setDisruptions(await disruptionRes.json())
      setRecovery(await recoveryRes.json())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    loadDashboard()
  }, [])

  const runRecovery = async () => {
    const res = await fetch(`${API_BASE}/api/recovery/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scenario_id: 'manual-run', budget: 10000 }),
    })
    if (res.ok) {
      setRecovery(await res.json())
      await loadDashboard()
    }
  }

  const createDemandShock = async () => {
    await fetch(`${API_BASE}/api/disruptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'demand_shock',
        name: `UI Demand Shock P${shockProductId}R${shockRegionId}`,
        product_id: shockProductId,
        region_id: shockRegionId,
        severity: Math.min(1, shockMultiplier - 1),
        start_date: new Date().toISOString().slice(0, 10),
        duration_days: 7,
        demand_multiplier: shockMultiplier,
      }),
    })
    await loadDashboard()
  }

  const createSupplierDelay = async () => {
    await fetch(`${API_BASE}/api/disruptions`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        type: 'supplier_delay',
        name: `UI Supplier Delay S${delaySupplierId}P${delayProductId}`,
        supplier_id: delaySupplierId,
        product_id: delayProductId,
        severity: 0.8,
        delay_days: delayDays,
        start_date: new Date().toISOString().slice(0, 10),
        duration_days: 7,
      }),
    })
    await loadDashboard()
  }

  const toggleDisruption = async (id: number, active: boolean) => {
    await fetch(`${API_BASE}/api/disruptions/${id}/${active ? 'deactivate' : 'activate'}`, { method: 'POST' })
    await loadDashboard()
  }

  if (loading) return <main className="layout"><h2>Loading StockShield dashboard…</h2></main>
  if (error) return <main className="layout"><h2>Dashboard error: {error}</h2></main>
  if (!summary) return <main className="layout"><h2>No dashboard data available</h2></main>

  return (
    <main className="layout">
      <header className="header">
        <div>
          <h1>StockShield</h1>
          <p>Scenario: Seeded Round 1 Demo</p>
          <p>Last analysis: {new Date(summary.last_analysis_timestamp).toLocaleString()}</p>
        </div>
        <button className="button" onClick={runRecovery}>Run Recovery Analysis</button>
      </header>

      <section className="kpis">
        <article><h3>Products at Risk</h3><strong>{summary.products_at_risk}</strong></article>
        <article><h3>Expected Lost Revenue</h3><strong>${summary.expected_lost_revenue.toFixed(0)}</strong></article>
        <article><h3>Revenue Protected</h3><strong>${summary.revenue_protected.toFixed(0)}</strong></article>
        <article><h3>Critical Supplier Risks</h3><strong>{summary.critical_supplier_risks}</strong></article>
        <article><h3>Avg Days to Stockout</h3><strong>{summary.average_days_to_stockout}</strong></article>
      </section>

      <section className="panel">
        <h2>Products at Risk</h2>
        <table>
          <thead>
            <tr>
              <th>Product</th><th>Region</th><th>Inventory</th><th>Daily Demand</th><th>Stockout Date</th><th>Probability</th><th>Lost Revenue</th><th>Risk</th><th>Recommended Action</th>
            </tr>
          </thead>
          <tbody>
            {risks.slice(0, 12).map((r) => (
              <tr key={`${r.product_id}-${r.region_id}`}>
                <td>{r.product_name}</td>
                <td>{r.region_name}</td>
                <td>{r.current_inventory}</td>
                <td>{r.daily_demand.toFixed(1)}</td>
                <td>{r.stockout_date ?? 'No stockout in horizon'}</td>
                <td>{(r.stockout_probability * 100).toFixed(0)}%</td>
                <td>${r.expected_lost_revenue.toFixed(0)}</td>
                <td><span className={riskBadgeClass(r.risk_level)}>{r.risk_level}</span></td>
                <td>{r.recommended_action}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="grid-two">
        <article className="panel">
          <h2>Supplier Risk & Disruptions</h2>
          <ul className="list">
            {disruptions.map((d) => (
              <li key={d.id}>
                <div>
                  <strong>{d.name}</strong>
                  <div>{d.type} {d.active ? '• active' : '• inactive'}</div>
                </div>
                <button className="button secondary" onClick={() => toggleDisruption(d.id, d.active)}>
                  {d.active ? 'Deactivate' : 'Activate'}
                </button>
              </li>
            ))}
          </ul>
        </article>

        <article className="panel">
          <h2>Regional Demand View</h2>
          <div className="regions">
            {regionalShift.map((item) => (
              <div key={item.region} className={`region ${item.avg >= 0.75 ? 'critical' : item.avg >= 0.5 ? 'high' : item.avg >= 0.25 ? 'medium' : 'low'}`}>
                <strong>{item.region}</strong>
                <span>{(item.avg * 100).toFixed(0)} risk index</span>
              </div>
            ))}
          </div>
        </article>
      </section>

      <section className="grid-two">
        <article className="panel">
          <h2>Inject Demand Shock</h2>
          <div className="form-grid">
            <label>Product ID <input type="number" value={shockProductId} onChange={(e) => setShockProductId(Number(e.target.value))} /></label>
            <label>Region ID <input type="number" value={shockRegionId} onChange={(e) => setShockRegionId(Number(e.target.value))} /></label>
            <label>Demand Multiplier <input type="number" step="0.1" value={shockMultiplier} onChange={(e) => setShockMultiplier(Number(e.target.value))} /></label>
          </div>
          <button className="button" onClick={createDemandShock}>Create Demand Shock</button>
        </article>

        <article className="panel">
          <h2>Inject Supplier Delay</h2>
          <div className="form-grid">
            <label>Supplier ID <input type="number" value={delaySupplierId} onChange={(e) => setDelaySupplierId(Number(e.target.value))} /></label>
            <label>Product ID <input type="number" value={delayProductId} onChange={(e) => setDelayProductId(Number(e.target.value))} /></label>
            <label>Delay Days <input type="number" value={delayDays} onChange={(e) => setDelayDays(Number(e.target.value))} /></label>
          </div>
          <button className="button" onClick={createSupplierDelay}>Create Supplier Delay</button>
        </article>
      </section>

      <section className="panel">
        <h2>Recovery Strategy Comparison</h2>
        <table>
          <thead>
            <tr>
              <th>Strategy</th><th>Arrival</th><th>Success</th><th>Cost</th><th>Revenue Protected</th><th>Net Value</th>
            </tr>
          </thead>
          <tbody>
            {recovery?.strategies.slice(0, 8).map((s) => (
              <tr key={s.strategy}>
                <td>{s.strategy}</td>
                <td>{s.arrival_days}d</td>
                <td>{(s.success_probability * 100).toFixed(0)}%</td>
                <td>${s.cost.toFixed(0)}</td>
                <td>${s.revenue_protected.toFixed(0)}</td>
                <td>${s.net_value.toFixed(0)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="panel recommendation">
        <h2>Recommendation</h2>
        <h3>{recovery?.recommendation.recommended_action}</h3>
        <p>Expected revenue protected: ${recovery?.recommendation.expected_revenue_protected.toFixed(0) ?? 0}</p>
        <p>Intervention cost: ${recovery?.recommendation.intervention_cost.toFixed(0) ?? 0}</p>
        <p>Net value: ${recovery?.recommendation.net_value.toFixed(0) ?? 0}</p>
        <p>Confidence: {(((recovery?.recommendation.confidence ?? 0) * 100)).toFixed(0)}%</p>
        <ul>
          {recovery?.recommendation.reasoning.map((r) => <li key={r}>{r}</li>)}
        </ul>
      </section>
    </main>
  )
}

export default App
