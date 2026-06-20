import { useState, useEffect, useMemo } from 'react'
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  Legend as RechartsLegend,
  AreaChart,
  Area,
  Cell
} from 'recharts'
import { Doughnut } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip as ChartJSTooltip,
  Legend as ChartJSLegend,
} from 'chart.js'
import apiClient from '@/api/client'
import { Leaf, AlertTriangle } from 'lucide-react'

// Register Chart.js elements
ChartJS.register(ArcElement, ChartJSTooltip, ChartJSLegend)

interface ChartData {
  period: string
  Total: number
  Scope1: number
  Scope2: number
  Scope3: number
  rawItem: any
  date: Date
}

const EmissionsPage = () => {
  const [data, setData] = useState<ChartData[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  
  // View toggle for time-series progress tracking
  const [timeView, setTimeView] = useState<'weekly' | 'monthly' | 'yearly'>('monthly')

  useEffect(() => {
    const fetchAssessments = async () => {
      try {
        setLoading(true)
        const response = await apiClient.get('/assessment/')
        const items = Array.isArray(response.data) ? response.data : response.data.items || []
        
        // Map to a format Recharts can use easily
        const chartData = items.map((item: any) => {
          const date = new Date(item.created_at)
          return {
            period: item.period || date.toLocaleString('default', { month: 'short', year: 'numeric' }),
            Scope1: item.scope_1 || 0,
            Scope2: item.scope_2 || 0,
            Scope3: item.scope_3 || 0,
            Total: item.total_emission || item.total_emissions || (item.scope_1 + item.scope_2 + item.scope_3) || 0,
            rawItem: item,
            date: date
          }
        })
        
        // Sort newest first to get latest, but reverse for charts (left to right)
        chartData.sort((a: ChartData, b: ChartData) => b.date.getTime() - a.date.getTime())
        setData(chartData.reverse())
      } catch (err: any) {
        if (err.message?.includes('404')) {
          setData([])
        } else {
          setError(err.message || 'Failed to load emissions data')
        }
      } finally {
        setLoading(false)
      }
    }
    fetchAssessments()
  }, [])

  const currentTotal = data.length > 0 ? data[data.length - 1].Total : 0
  const previousTotal = data.length > 1 ? data[data.length - 2].Total : 0
  const percentChange = previousTotal ? ((currentTotal - previousTotal) / previousTotal) * 100 : 0
  const trend = percentChange > 0 ? 'up' : percentChange < 0 ? 'down' : 'flat'

  // --- Category Breakdown Data (Doughnut Chart) ---
  const latestAssessment = data.length > 0 ? data[data.length - 1].rawItem : null
  const doughnutData = {
    labels: ['Transport', 'Energy', 'Food', 'Water', 'Waste'],
    datasets: [
      {
        data: latestAssessment ? [
          latestAssessment.transport || latestAssessment.transport_emission || 0,
          latestAssessment.energy || latestAssessment.energy_emission || 0,
          latestAssessment.food || latestAssessment.food_emission || 0,
          latestAssessment.water || latestAssessment.water_emission || 0,
          latestAssessment.waste || latestAssessment.waste_emission || 0,
        ] : [0,0,0,0,0],
        backgroundColor: ['#14B8A6', '#0EA5E9', '#6366F1', '#38BDF8', '#8B5CF6'],
        borderWidth: 0,
        hoverOffset: 6
      }
    ]
  }
  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    cutout: '70%',
    animation: { animateScale: true, animateRotate: true },
    plugins: {
      legend: {
        position: 'right' as const,
        labels: { color: '#94A3B8', font: { family: 'Inter', size: 12 }, boxWidth: 12, padding: 20 }
      },
      tooltip: {
        backgroundColor: 'rgba(15, 23, 42, 0.9)',
        titleFont: { family: 'Inter', size: 13 },
        bodyFont: { family: 'Inter', size: 13 },
        padding: 12,
        callbacks: {
          label: (context: any) => ` ${context.label}: ${context.raw.toFixed(1)} kg CO₂e`
        }
      }
    }
  }

  // --- Comparative Analytics Benchmarking Data (Bar Chart) ---
  // Note: These averages are statically seeded for now as no live benchmark API exists yet.
  const benchmarkData = [
    { name: 'You', value: currentTotal, fill: '#10B981' }, // Emerald for user
    { name: 'City Avg', value: 250, fill: '#334155' },
    { name: 'State Avg', value: 300, fill: '#475569' },
    { name: 'Country Avg', value: 400, fill: '#64748B' },
    { name: 'Global Avg', value: 350, fill: '#94A3B8' },
  ]

  // --- Progress Tracking (Area Chart with Time View toggle) ---
  const timeSeriesData = useMemo(() => {
    // Grouping logic for the time-series area chart
    if (data.length === 0) return []
    
    const formatStr = (d: Date, type: string) => {
      if (type === 'weekly') {
        const startOfYear = new Date(d.getFullYear(), 0, 1)
        const days = Math.floor((d.getTime() - startOfYear.getTime()) / (24 * 60 * 60 * 1000))
        const weekNumber = Math.ceil((d.getDay() + 1 + days) / 7)
        return `W${weekNumber} ${d.getFullYear()}`
      }
      if (type === 'monthly') return d.toLocaleString('default', { month: 'short', year: '2-digit' })
      if (type === 'yearly') return d.getFullYear().toString()
      return d.toLocaleDateString()
    }

    const grouped = new Map<string, number>()
    data.forEach(item => {
      const key = formatStr(item.date, timeView)
      grouped.set(key, (grouped.get(key) || 0) + item.Total) // Could also average if desired
    })

    const result = Array.from(grouped.entries()).map(([time, total]) => ({
      time,
      Emissions: total
    }))
    
    // Fill empty gaps if needed (simplified for now to just show points)
    return result
  }, [data, timeView])

  return (
    <main className="max-w-7xl mx-auto p-4 md:p-6 space-y-8 animate-fade-in pb-12">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold text-white tracking-tight">Emissions Analytics</h1>
          <p className="text-slate-400 mt-1">Detailed breakdown and comparative benchmarking</p>
        </div>
        <button className="bg-emerald-600 hover:bg-emerald-500 text-white px-5 py-2.5 rounded-xl font-medium transition-colors shadow-lg shadow-emerald-900/20">
          Export Report
        </button>
      </div>

      {loading ? (
        <div className="flex h-64 items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-emerald-500"></div>
        </div>
      ) : error ? (
        <div className="glass-card p-6 border-red-500/30 text-red-400 text-center">
          <AlertTriangle className="w-8 h-8 mx-auto mb-2 opacity-80" />
          {error}
        </div>
      ) : data.length === 0 ? (
        <div className="glass-card p-12 text-center border-white/5">
          <Leaf className="mx-auto h-12 w-12 text-emerald-500/50 mb-4" />
          <h2 className="text-xl font-semibold text-white mb-2">No Emissions Data</h2>
          <p className="text-slate-400">Complete your first carbon assessment to see your analytics.</p>
        </div>
      ) : (
        <>
          {/* KPI Row (Existing) */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div className="glass-card p-6 border-white/5 transition-transform hover:-translate-y-1 duration-300">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Latest Period Total</h3>
              <div className="flex items-baseline">
                <span className="text-4xl font-bold text-white">{currentTotal.toFixed(1)}</span>
                <span className="ml-2 text-sm text-slate-500 font-medium">kg CO₂e</span>
              </div>
            </div>

            <div className="glass-card p-6 border-white/5 transition-transform hover:-translate-y-1 duration-300">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Trend vs Previous</h3>
              <div className="flex items-baseline">
                <span className={`text-4xl font-bold ${trend === 'down' ? 'text-emerald-400' : trend === 'up' ? 'text-red-400' : 'text-slate-300'}`}>
                  {trend === 'up' ? '+' : ''}{percentChange.toFixed(1)}%
                </span>
                <span className="ml-2 text-sm text-slate-500 font-medium">
                  {trend === 'down' ? <><Leaf className="w-4 h-4 inline-block mr-1 text-emerald-400" /> Decrease</> : trend === 'up' ? <><AlertTriangle className="w-4 h-4 inline-block mr-1 text-amber-500" /> Increase</> : 'No Change'}
                </span>
              </div>
            </div>

            <div className="glass-card p-6 border-white/5 transition-transform hover:-translate-y-1 duration-300">
              <h3 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-2">Largest Scope</h3>
              <div className="flex items-baseline">
                <span className="text-4xl font-bold text-white">
                  {
                    Object.entries({
                      'Scope 1': data[data.length - 1].Scope1,
                      'Scope 2': data[data.length - 1].Scope2,
                      'Scope 3': data[data.length - 1].Scope3,
                    }).sort((a, b) => b[1] - a[1])[0][0]
                  }
                </span>
              </div>
            </div>
          </div>

          {/* New Analytics Row: Doughnut & Benchmark */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            
            {/* Category Breakdown */}
            <div className="glass-card p-6 border-white/5 flex flex-col relative overflow-hidden group">
              <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-teal-500/5 rounded-full blur-3xl transition-transform group-hover:scale-110"></div>
              <h3 className="text-lg font-bold text-white mb-6 relative z-10">Emission Breakdown</h3>
              <div className="flex-1 min-h-[300px] relative z-10 flex items-center justify-center">
                {latestAssessment ? (
                  <Doughnut data={doughnutData} options={doughnutOptions} />
                ) : (
                  <p className="text-slate-500">No data available</p>
                )}
              </div>
            </div>

            {/* Comparative Benchmarking */}
            <div className="glass-card p-6 border-white/5 flex flex-col relative overflow-hidden group">
              <div className="absolute top-0 right-0 -mt-8 -mr-8 w-48 h-48 bg-emerald-500/5 rounded-full blur-3xl transition-transform group-hover:scale-110"></div>
              <h3 className="text-lg font-bold text-white mb-6 relative z-10">Comparative Analytics</h3>
              <div className="flex-1 min-h-[300px] relative z-10">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={benchmarkData} margin={{ top: 20, right: 10, left: -20, bottom: 5 }}>
                    <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                    <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} dy={10} />
                    <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} />
                    <RechartsTooltip 
                      cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                      contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '0.5rem', color: '#fff' }}
                      formatter={(val: number) => [`${val} kg CO₂e`, 'Emissions']}
                    />
                    <Bar dataKey="value" radius={[4, 4, 0, 0]} isAnimationActive={true}>
                      {benchmarkData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          </div>

          {/* New Analytics: Progress Tracking Area Chart */}
          <div className="glass-card p-6 border-white/5 relative overflow-hidden">
            <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-full h-32 bg-emerald-500/5 blur-[100px] pointer-events-none"></div>
            <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8 gap-4 relative z-10">
              <h3 className="text-lg font-bold text-white">Progress Tracking</h3>
              <div className="flex items-center bg-slate-800/80 rounded-lg p-1 border border-white/5">
                {(['weekly', 'monthly', 'yearly'] as const).map(view => (
                  <button
                    key={view}
                    onClick={() => setTimeView(view)}
                    className={`px-4 py-1.5 text-sm font-medium rounded-md transition-all duration-200 capitalize ${
                      timeView === view 
                        ? 'bg-emerald-500/20 text-emerald-400 shadow-sm' 
                        : 'text-slate-400 hover:text-slate-200'
                    }`}
                  >
                    {view}
                  </button>
                ))}
              </div>
            </div>
            
            <div className="h-72 w-full relative z-10">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={timeSeriesData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <defs>
                    <linearGradient id="colorEmissions" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#10B981" stopOpacity={0.3}/>
                      <stop offset="95%" stopColor="#10B981" stopOpacity={0}/>
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis dataKey="time" axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} dy={10} />
                  <YAxis axisLine={false} tickLine={false} tick={{ fill: '#94A3B8', fontSize: 12 }} />
                  <RechartsTooltip 
                    contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', borderColor: 'rgba(16,185,129,0.2)', borderRadius: '0.5rem', color: '#fff' }}
                    itemStyle={{ color: '#10B981', fontWeight: 600 }}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="Emissions" 
                    stroke="#10B981" 
                    strokeWidth={3}
                    fillOpacity={1} 
                    fill="url(#colorEmissions)" 
                    isAnimationActive={true}
                    animationDuration={1500}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Existing Chart: Historical Scopes */}
          <div className="glass-card p-6 border-white/5">
            <h3 className="text-lg font-bold text-white mb-6">Historical Emissions by Scope</h3>
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={data} margin={{ top: 10, right: 10, left: 0, bottom: 20 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="rgba(255,255,255,0.05)" />
                  <XAxis 
                    dataKey="period" 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#94A3B8', fontSize: 12 }} 
                    dy={10}
                  />
                  <YAxis 
                    axisLine={false} 
                    tickLine={false} 
                    tick={{ fill: '#94A3B8', fontSize: 12 }} 
                    dx={-10}
                  />
                  <RechartsTooltip 
                    cursor={{ fill: 'rgba(255,255,255,0.02)' }}
                    contentStyle={{ backgroundColor: 'rgba(15, 23, 42, 0.9)', borderColor: 'rgba(255,255,255,0.1)', borderRadius: '0.5rem', color: '#fff' }}
                  />
                  <RechartsLegend wrapperStyle={{ paddingTop: '20px' }} iconType="circle" />
                  <Bar dataKey="Scope1" name="Scope 1 (Direct)" stackId="a" fill="#14B8A6" radius={[0, 0, 4, 4]} isAnimationActive={true} />
                  <Bar dataKey="Scope2" name="Scope 2 (Indirect)" stackId="a" fill="#0EA5E9" isAnimationActive={true} />
                  <Bar dataKey="Scope3" name="Scope 3 (Value Chain)" stackId="a" fill="#6366F1" radius={[4, 4, 0, 0]} isAnimationActive={true} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </>
      )}
    </main>
  )
}

export default EmissionsPage
